import datetime
import random
import uuid
import string
import httpagentparser
import random
import os
import sys
import magic

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q

from user_profile.models import Profile
from idea.models import Idea, Survey, Comment, Topic, Update, Product, Feedback

from django.template import Context
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail, EmailMessage

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import get_connection, EmailMultiAlternatives

from idea.models import send_mass_html_mail

from django.conf import settings

from django.http import JsonResponse
from django.core.cache import cache

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.management import call_command

NOTIFICATION_TAGS = {
    "success": "/static/images/icons/check-circle-outline.svg",
    "error": "/static/images/icons/cross-circled.svg",
    "warning": "/static/images/icons/warning-circle-outline.svg",
    "info": "/static/images/icons/info-outline.svg",
}

POINT_POLICY = {
    "like_idea": 1,
    "get_vote": 1,
    "daily_strike": {
        0: 10,
        1: 15,
        2: 20,
        3: 25,
        4: 30,
        5: 40,
        6: 50,
    },
    "reference_idea_point": 50,
}

BADGES = {
    'ADMINISTRATION_TEAM': 'static/images/badges/admin.svg',
    'CONTENT_TEAM': 'static/images/badges/content-team.svg',
    'SOFTWARE_TEAM': 'static/images/badges/software-team.svg',
    'SOFTWARE_LEAD': 'static/images/badges/software-lead.svg'
}


def get_total_votes(surveys: list):
    total_votes = [len(vote['participants']) for survey in surveys for vote in survey.survey_votes.values()]
    return sum(total_votes)

def get_user_badge(user) -> str:
    user_groups = [str(group) for group in user.groups.all()]

    if 'Administration Team' in user_groups:
        user_admin_badge = 'SOFTWARE_LEAD' if 'Software Team' in user_groups else 'ADMINISTRATION_TEAM'
        return open(BADGES[user_admin_badge], encoding='utf-8').read() 
    elif 'Content Team' in user_groups:
        return open(BADGES['CONTENT_TEAM'], encoding='utf-8').read()
    elif 'Software Team' in user_groups:
        return open(BADGES['SOFTWARE_TEAM'], encoding='utf-8').read()

    return ''

def get_client_ip(request, method: str = "classic"):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    if method == "classic":
        try:
            found_profile = Profile.objects.get(Q(ip_addresses__has_key = ip))
        except Profile.DoesNotExist:
            pass 
        else:
            if found_profile and (request.user.is_anonymous or found_profile.account != request.user):
                try:
                    user_profile = Profile.objects.get(account=request.user)
                except:
                    ip = '{}.{}.{}.{}'.format(*random.sample(range(0,255),4))
                    return ip
                else: 
                    # print(not isinstance(user_profile.ip_addresses, dict), len(user_profile.ip_addresses) < 2)
                    if not isinstance(user_profile.ip_addresses, dict) or len(user_profile.ip_addresses) < 2:
                        ip = '{}.{}.{}.{}'.format(*random.sample(range(0,255),4))
                        return ip
                    else:
                        return list(user_profile.ip_addresses.keys())[1]

    return ip

def get_time_span(compared):
    compared = compared.split('.')[0]
    compared = datetime.datetime.strptime(compared, '%Y-%m-%d %H:%M:%S')
    time_span = (datetime.datetime.now() - compared).seconds
    if ((time_span // 60) // 60) // 24 >= 1:
      time_span = f'{((time_span // 60) // 60)} gün önce'
    elif (time_span // 60) // 60 >= 1:
      time_span = f'{(time_span // 60) // 60} saat önce'
    elif (time_span // 60) >= 1:
      time_span = f'{(time_span // 60)} dakika önce'
    else:
      time_span = f'{(time_span)} saniye önce'
    return time_span
  
def create_hash(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def IncrementLogin(request):
    if not request.user.is_anonymous:
        try:
            agent = request.META["HTTP_USER_AGENT"]
            parsed_agent = httpagentparser.detect(agent)
            platform, os, is_bot, browser = (
                " ".join(parsed_agent["platform"].values()),
                " ".join(parsed_agent["os"].values()),
                parsed_agent["bot"],
                " ".join(parsed_agent["browser"].values()),
            )
        except TypeError:
            return 

        try:
            user_profile = Profile.objects.get(account=request.user)
        except Profile.DoesNotExist:
            pass 
        else: 
            try:
                if user_profile.user_restricted:
                    return render(request, "404.html")
            except KeyError:
                pass 
            if user_profile.last_logged_in.day != datetime.datetime.now().day: 
                if user_profile.login_strike is None: 
                    user_profile.login_strike = 0 
                try:
                    user_profile.total_point = (
                        int(user_profile.total_point)
                        + POINT_POLICY["daily_strike"][user_profile.login_strike]
                    )
                except:
                    user_profile.total_point = POINT_POLICY["daily_strike"][
                        user_profile.login_strike
                    ]
                user_profile.login_strike += 1
                if user_profile.login_strike >= 7:
                    user_profile.login_strike = 0

            user_profile.login_count += 1
            user_profile.last_logged_in = datetime.datetime.now()
            logged_time = user_profile.last_logged_in - request.user.date_joined
            user_profile.total_logged_time = logged_time
            try:
                user_profile.ip_addresses[get_client_ip(request)] = str(user_profile.last_logged_in)
            except TypeError:
                user_profile.ip_addresses = {}
                user_profile.ip_addresses[get_client_ip(request)] = str(user_profile.last_logged_in)

            user_profile.profile_user = "Belirlenemedi"

            try:
                user_profile.profile_platforms[platform] = str(
                    user_profile.last_logged_in
                )
            except TypeError:
                user_profile.profile_platforms = {}
                user_profile.profile_platforms[platform] = str(
                    user_profile.last_logged_in
                )

            try:
                user_profile.profile_oses[os] = str(user_profile.last_logged_in)
            except TypeError:
                user_profile.profile_oses = {}
                user_profile.profile_oses[os] = str(user_profile.last_logged_in)

            try:
                user_profile.profile_browsers[browser] = str(
                    user_profile.last_logged_in
                )
            except TypeError:
                user_profile.profile_browsers = {}
                user_profile.profile_browsers[browser] = str(
                    user_profile.last_logged_in
                )

            user_profile.is_bot = is_bot
            if user_profile.profile_rank is None:
                user_profile.profile_rank = "rookie"

            # print(user_profile.web_theme)
            
            today_topic = Topic.objects.first()
            
            try:
              user_profile.user_notifications[today_topic.topic_name]
            except TypeError:
              user_profile.user_notifications = {}
              
              user_profile.user_notifications[today_topic.topic_name] = {
                'notification_content': f'Günün konusu yayında: {today_topic.topic_name}',
                'notification_details': str(today_topic.topic_date),
                'notification_image': 'robot',
                'notification_link': '/',
                'viewed': False
              }
            except KeyError: 
              
              user_profile.user_notifications[today_topic.topic_name] = {
                'notification_content': f'Günün konusu yayında: {today_topic.topic_name}',
                'notification_details': str(today_topic.topic_date),
                'notification_image': 'robot',
                'notification_link': '/',
                'viewed': False
              }
              
            
            if today_topic.topic_survey['active']:
            
                try:
                    user_profile.user_notifications[today_topic.topic_survey['survey_name']]
                except TypeError:
                    user_profile.user_notifications = {}
                    
                    user_profile.user_notifications[today_topic.topic_survey['survey_name']] = {
                        'notification_content': 'Yeni anketiniz var: ' + today_topic.topic_survey['survey_name'],
                        'notification_details': str(today_topic.topic_date),
                        'notification_image': 'robot',
                        'notification_link': today_topic.topic_survey['survey_url'],
                        'viewed': False
                    }
                except KeyError: 
                
                    user_profile.user_notifications[today_topic.topic_survey['survey_name']] = {
                        'notification_content': 'Yeni anketiniz var: ' + today_topic.topic_survey['survey_name'],
                        'notification_details': str(today_topic.topic_date),
                        'notification_image': 'robot',
                        'notification_link': today_topic.topic_survey['survey_url'],
                        'viewed': False
                    }

            if isinstance(today_topic.special_topic_message, str) and len(today_topic.special_topic_message) >= 2:
                try:
                    user_profile.user_notifications[today_topic.special_topic_message]
                except TypeError:
                    user_profile.user_notifications = {}
                    
                    user_profile.user_notifications[today_topic.special_topic_message] = {
                        'notification_content': today_topic.special_topic_message,
                        'notification_details': str(today_topic.topic_date),
                        'notification_image': 'robot',
                        'notification_link': '/',
                        'viewed': False
                    }
                except KeyError: 
                
                    user_profile.user_notifications[today_topic.special_topic_message] = {
                        'notification_content': today_topic.special_topic_message,
                        'notification_details': str(today_topic.topic_date),
                        'notification_image': 'robot',
                        'notification_link': '/',
                        'viewed': False
                    }
            user_profile.save()


def GivePoint(user, amount):
    try:
        user_profile = Profile.objects.get(account=user)
    except Profile.DoesNotExist:
        return False
    try:
        user_profile.total_point = int(user_profile.total_point) + int(amount)
    except:
        user_profile.total_point = 0
    user_profile.save()


def TakePoint(user, amount):
    try:
        user_profile = Profile.objects.get(account=user)
    except Profile.DoesNotExist:
        return False
    try:
        user_profile.total_point = int(user_profile.total_point) - int(amount)
    except:
        user_profile.total_point = 0
    user_profile.save()


def get_user_profile(user):
    try:
        profile = Profile.objects.get(account=user)
    except Profile.DoesNotExist:
        return False
    except TypeError:
        return False
    else:
        profile.user_notifications = dict(
          sorted(profile.user_notifications.items(), 
                key=lambda notification: notification[1]['notification_details'],
                reverse=True
                )
          )

        profile.save()
        return profile

def DashBoardView(request):
    ideas = Idea.objects.filter(Q(idea_archived=False))

    comments = Comment.objects.filter(Q(comment_archived=False))

    IncrementLogin(request)
    surveys =  Survey.get_available_surveys()
    return render(
        request,
        "index.html",
        {
            "profile": get_user_profile(request.user),
            "topic": Topic.objects.first(),
            "top_ideas": ideas,
            "comments_count": len(comments),
            "ideas_count": len(ideas),
            "surveys": surveys,
            "total_votes": get_total_votes(surveys),
            "section": "summary",
        },
    )

def OpenSurveysView(request):


    surveys = Survey.get_available_surveys()

    IncrementLogin(request)

    return render(
        request,
        "index.html",
        {
            "profile": get_user_profile(request.user),
            "topic": 'Bir oylama başlatmak için + sembolünü kullanabilirsin.',
            "total_votes": get_total_votes(surveys),
            "surveys": surveys,
            "section": "open-surveys",
        },
    )

@user_passes_test(lambda u: not u.is_anonymous)
def VoteOpenSurveyView(request, survey_id: int, option_id: str):
    if request.POST:
        try:
            survey = Survey.objects.get(Q(pk=survey_id))
        except Survey.DoesNotExist:
            return redirect('open-surveys-page')
        else:
            if survey.survey_archived or survey.is_past_due:
                return {'survey_results': {}}

            survey_selected_opt = survey.get_survey_option(option_id)

            if request.user.username not in survey_selected_opt['participants']:
                if not survey.did_participate_user(request.user.username):
                    GivePoint(survey.survey_author.account, POINT_POLICY['get_vote'])

                survey.clear_user_votes(request.user.username)

                survey_selected_opt['participants'][request.user.username] = str(datetime.datetime.now())
                survey_selected_opt['info']['ratio'] = survey.calculate_ratio(option_id)
                survey.adapt_ratios(option_id)
                survey.survey_votes[option_id] = survey_selected_opt

                survey.save()
            else:
                TakePoint(survey.survey_author.account, POINT_POLICY['get_vote'])
                survey.clear_user_votes(request.user.username)



        return JsonResponse({
            "survey_results": survey.survey_votes
        })

def IndexView(request):
    if request.user.is_anonymous:
        return LandingView(request)

    return DashBoardView(request)

@user_passes_test(lambda u: not u.is_anonymous)
def ShopView(request):
    user_profile = get_user_profile(request.user)
  
  
    if request.POST:
      product_name = request.POST['product_name']
      
      try:
        product = Product.objects.get(Q(product_name=product_name))
      except Product.DoesNotExist:
        messages.error(request, 'Ürün veritabanında bulunamadı!', extra_tags=NOTIFICATION_TAGS['error'])
      else:
        if user_profile.total_point >= product.product_fee:
          try:
            user_profile.shop_bought_products[product_name]
          except KeyError:
            pass 
          except TypeError:
            user_profile.shop_bought_products = {}
          else:
            return messages.error(request, 'Bu ürünü zaten almışsın!', extra_tags=NOTIFICATION_TAGS["error"])
          
          user_profile.web_theme = product_name
          user_profile.total_point -= product.product_fee
          user_profile.shop_bought_products[product_name] = str(datetime.datetime.now())
          product.product_sold_count += 1
          
          user_profile.save()
          product.save()
          
          messages.success(request, 'Ürün başarıyla satın alındı!', extra_tags=NOTIFICATION_TAGS['success'])
          
        else:
          messages.error(request, 'Puanınız yetersiz!', extra_tags=NOTIFICATION_TAGS['error'])
          

    IncrementLogin(request)

    return render(
        request,
        "shop.html",
        {
            "profile": user_profile,
            "section": "shop",
            "products": Product.objects.all()
        },
    )

@user_passes_test(lambda u: not u.is_anonymous)
def ChangeThemeView(request):
  if request.GET:
    user_profile = get_user_profile(request.user)
    product_name = request.GET['product_name']
    
    if product_name != 'Thinker Tema':

        try:
            user_profile.shop_bought_products[product_name]
        except KeyError:
            messages.error(request, 'Bu ürün satın alınmamış.', extra_tags=NOTIFICATION_TAGS['error'])
        except TypeError:
            user_profile.shop_bought_products = {}
            user_profile.save()
            messages.error(request, 'Bu ürün satın alınmamış.', extra_tags=NOTIFICATION_TAGS['error'])
        else:
            product_code = product_name
            if user_profile.web_theme != product_code:
                user_profile.web_theme = product_code
                user_profile.save()
                messages.success(request, f'Tema değiştirildi: {product_name}', extra_tags=NOTIFICATION_TAGS["success"])
            else:
                messages.error(request, 'Zaten bu tema aktifleştirilmiş.', extra_tags=NOTIFICATION_TAGS['error'])
        finally:
            return render(request, 'shop.html',         {
                    "profile": user_profile,
                    "section": "shop",
                    "products": Product.objects.all(),
                },)
    else:
        product_code = product_name
        if user_profile.web_theme != product_code:
            user_profile.web_theme = product_code
            user_profile.save()
            messages.success(request, f'Tema değiştirildi: {product_name}', extra_tags=NOTIFICATION_TAGS["success"])
        else:
            messages.error(request, 'Zaten bu tema aktifleştirilmiş.', extra_tags=NOTIFICATION_TAGS['error'])
    return render(request, 'shop.html',         {
        "profile": user_profile,
        "section": "shop",
        "products": Product.objects.all(),
    },)


def LandingView(request):
    IncrementLogin(request)

    topic = Topic.objects.first()

    return render(
        request,
        "home.html",
        {
            "profile": get_user_profile(request.user),
            "topic_name": topic.topic_name[:40],
            "topic_sources": topic.topic_sources[:300],
            "section": "home",
        },
    ) 
    
def AboutUsView(request):
  IncrementLogin(request)
  
  return render(request, "about_us.html", {"section": "about-us", "profile": get_user_profile(request.user)})


@user_passes_test(lambda u: u.is_anonymous)
def ReferencedAuthenticationView(request, reference_code: str):
    if request.method == "GET":
        try:
            referenced_user = Profile.objects.get(user_secret=reference_code)
        except Profile.DoesNotExist:
            messages.error(request, 'Böyle bir referans kodu bulunamadı!', extra_tags=NOTIFICATION_TAGS['error'])
            return AuthenticationView(request)
        else:
            messages.success(request, f'Referans Alındı: {referenced_user.account.username}', extra_tags=NOTIFICATION_TAGS['success'])
            IncrementLogin(request)

            return render(
                request,
                "authentication.html",
                {
                    "profile": get_user_profile(request.user),
                    "section": "home-authentication",
                    "reference_code": reference_code,
                    "reference_user": referenced_user
                },
            ) 


@user_passes_test(lambda u: u.is_anonymous)
def AuthenticationView(request):
    if request.POST:
      
      username, password = request.POST.get('username'), request.POST.get('password')
      user = authenticate(username=username, password=password)

      if user is not None:
          login(request, user)
          messages.success(
              request,
              f"Başarıyla giriş yaptın: {username}",
              extra_tags=NOTIFICATION_TAGS["success"],
          )
          
          return redirect('profile-page', username)
      else:
          messages.error(
              request,
              "Bilgilerinde hata var, kontrol et!",
              extra_tags=NOTIFICATION_TAGS["error"],
          )

      return redirect("index-page")
  
    else:
        ref_code: str = request.GET.get('reference_code')
        if ref_code is not None and len(ref_code) == 6:
            return ReferencedAuthenticationView(request, ref_code)

    IncrementLogin(request)

    return render(
        request,
        "authentication.html",
        {
            "profile": get_user_profile(request.user),
            "section": "home-authentication",
        },
    ) 

def ProfileView(request, username):
  try: 
    user = User.objects.get(username = username) 
  except User.DoesNotExist:
    if request.user.is_authenticated:
        user = request.user 
    else:
        return redirect('authentication')
  finally:
    try:
        if user:
            profile = Profile.objects.get(account = user)
            ideas = Idea.objects.filter(Q(idea_author = profile)).order_by('-idea_publish_date')
            return render(request, 'profile.html', {'pprofile': profile, 'profile':  get_user_profile(request.user),'puser': user, 'user_ideas': ideas, 'user_comments': Comment.objects.filter(Q(comment_author = profile)).order_by('-comment_publish_date')})
        else:
            return redirect('authentication')
    except UnboundLocalError:
        return redirect('authentication')

@user_passes_test(lambda u: not u.is_anonymous)
def FollowProfileView(request, profile_id: int):
    try:
        profile = Profile.objects.get(pk = profile_id)
    except Profile.DoesNotExist:
        return False 
    else: 
        if profile.account == request.user: return False

        try:
            profile.profile_followers[request.user.username]
        except KeyError:
            profile.profile_followers[request.user.username] = str(datetime.datetime.now())
            profile.user_notifications[create_hash(16)] = {
              'notification_content': f'{request.user.username} sizi takip etmeye başladı.',
              'notification_details': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
              'notification_image': 'robot',
              'notification_link': f'/profile/{request.username}',
              'viewed': False
            }
            
            profile.save()
        except TypeError:
            profile.profile_followers = {}
            profile.profile_followers[request.user.username] = str(datetime.datetime.now())

            profile.user_notifications[create_hash(16)] = {
              'notification_content': f'{request.user.username} sizi takip etmeye başladı.',
              'notification_details': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
              'notification_image': 'robot',
              'notification_link': f'/profile/{profile.account.username}',
              'viewed': False
            }
            
            profile.save()
        else:
            del profile.profile_followers[request.user.username]
        finally:
            profile.save()
            return redirect('profile-page', profile.account.username)


def FavouriteIdeasView(request):
    ideas = Idea.objects.filter(Q(idea_archived=False))
    comments = Comment.objects.filter(Q(comment_archived=False))
    IncrementLogin(request)
    surveys = Survey.get_available_surveys()
    return render(
        request,
        "index.html",
        {
            "profile": get_user_profile(request.user),
            "topic": Topic.objects.first(),
            "top_ideas": ideas.order_by("-idea_like_count")
            if len(ideas) >= 2
            else ideas,
            "comments_count": len(comments),
            "ideas_count": len(ideas),
            "surveys": surveys,
            "total_votes": get_total_votes(surveys),
            'section': 'ideas'
        },
    )


def TrendIdeasView(request):
    ideas = Idea.objects.filter(Q(idea_archived=False))
    comments = Comment.objects.filter(Q(comment_archived=False))
    IncrementLogin(request)
    return render(
        request,
        "index.html",
        {
            "profile": get_user_profile(request.user),
            "topic": Topic.objects.first(),
            "top_ideas": ideas.order_by("-idea_comments") if len(ideas) >= 2 else ideas,
            "comments_count": len(comments),
            "ideas_count": len(ideas),
            "section": "trends",
        },
    )


def IdeasOverview(request):
    ideas = Idea.objects.filter(Q(idea_archived=False))
    comments = Comment.objects.filter(Q(comment_archived=False))
    IncrementLogin(request)
    return render(
        request,
        "ideas_overview.html",
        {
            "profile": get_user_profile(request.user),
            "topic": Topic.objects.first(),
            "random_idea": random.choice(ideas) if len(ideas) >= 2 else ideas[0],
            "comments_count": len(comments),
            "ideas_count": len(ideas),
            "section": "idea-overview",
        },
    )

def UpdatesView(request):
    return render(request, 'updates.html', {'updates': Update.objects.all()[::-1]})

def StatusView(request):
    return redirect('https://stats.uptimerobot.com/NyKm0fZmO3')

def IpToLocView(request):
    return redirect('https://ipapi.co/json')

def StatisticsView(request):
    if request.user.is_superuser:
        profiles = Profile.objects.all()

        for profile in profiles:
            if not isinstance(profile.ip_addresses, dict):
                profile.ip_addresses = {profile.ip_addresses: True}
                profile.save()

        users, ideas, comments = User.objects.all(), Idea.objects.all(), Comment.objects.all()
        users_who_has_written_idea = set([idea.idea_author for idea in ideas])


        users_who_has_used_website_2_days = [idea.idea_author for idea in ideas if len(Idea.objects.filter(Q(idea_author = idea.idea_author))) >= 2]
        
        char_count_of_total_ideas = sum([len(idea.idea_content) for idea in ideas]) 
        word_count_of_total_ideas = sum([len(idea.idea_content.split(' ')) for idea in ideas]) 
        sentence_count_of_total_ideas = sum([len(idea.idea_content.split('.')) for idea in ideas]) 

        today_char_count_of_total_ideas = sum([len(idea.idea_content) for idea in ideas if idea.idea_archived == False]) 
        today_word_count_of_total_ideas = sum([len(idea.idea_content.split(' ')) for idea in ideas if idea.idea_archived == False]) 
        today_sentence_count_of_total_ideas = sum([len(idea.idea_content.split('.')) for idea in ideas if idea.idea_archived == False]) 

        char_count_of_total_comments = sum([len(comment.comment_content) for comment in comments]) 
        word_count_of_total_comments = sum([len(comment.comment_content.split(' ')) for comment in comments]) 
        sentence_count_of_total_comments = sum([len(comment.comment_content.split('.')) for comment in comments]) 

        today_char_count_of_total_comments = sum([len(comment.comment_content) for comment in comments if comment.comment_archived == False]) 
        today_word_count_of_total_comments = sum([len(comment.comment_content.split(' ')) for comment in comments if comment.comment_archived == False]) 
        today_sentence_count_of_total_comments = sum([len(comment.comment_content.split('.')) for comment in comments if comment.comment_archived == False]) 

        words = [word.lower() for idea in ideas for word in idea.idea_content.split(' ')] + [word.lower() for comment in comments for word in comment.comment_content.split(' ')]  



        user_register_dates = {}

        for user in users: 
            try: 
                user_register_dates[f'{user.date_joined.day}-{user.date_joined.month}'] += 1 
            except KeyError:
                user_register_dates[f'{user.date_joined.day}-{user.date_joined.month}'] = 1 

        
        idea_publish_dates = {} 

        for idea in ideas: 
            try: 
                idea_publish_dates[idea.idea_publish_date.day] += 1 
            except KeyError:
                idea_publish_dates[idea.idea_publish_date.day] = 1 
        ideas_per_days = [x for x in  sorted(idea_publish_dates.values())]
        idea_per_day = sum(ideas_per_days) // len(ideas_per_days)
        print()

        idea_per_7_day = sum(ideas_per_days[::-1][:7]) // len(ideas_per_days[::-1][:7])
        
        comment_publish_dates = {} 

        for comment in comments: 
            try: 
                comment_publish_dates[comment.comment_publish_date.day] += 1 
            except KeyError:
                comment_publish_dates[comment.comment_publish_date.day] = 1 


        print(
        """JUSTHINK STATS 

        Total Users: {}
        Total Ideas: {}
        Idea Per Day: {}
        Idea Per 7 Days: {}
        Total Comments: {}

        Users Who Has Written An Idea: {}
        Users Who Has Used the Website At Least 2 Days: {}

        Total Idea Char Count: {}
        Total Idea Word Count: {}
        Total Idea Sentence Count: {}
        Avr. Ideas' Word Length: {} 

        Today Total Idea Char Count: {}
        Today Total Idea Word Count: {}
        Today Total Idea Sentence Count: {}

        Total Comment Char Count: {}
        Total Comment Word Count: {}
        Total Comment Sentence Count: {}
        Avr. Comment' Word Length: {} 

        Today Total Comment Char Count: {}
        Today Total Comment Word Count: {}
        Today Total Comment Sentence Count: {}

        Total Char Count: {}
        Total Word Count: {}
        Total Sentence Count: {}
        Avr. Word Length: {}

        Max Used Words: 
        User Dates: {}
        Idea Dates: {}
        Comment Dates: {}
        Today Video Watch Rate: (21 out of 100+) [%21]

        """.format(len(users), len(ideas), idea_per_day, idea_per_7_day, len(comments), len(users_who_has_written_idea), len(users_who_has_used_website_2_days), 
        char_count_of_total_ideas, word_count_of_total_ideas, sentence_count_of_total_ideas, char_count_of_total_ideas / word_count_of_total_ideas, 
        today_char_count_of_total_ideas, today_word_count_of_total_ideas, today_sentence_count_of_total_ideas,
        char_count_of_total_comments, word_count_of_total_comments, sentence_count_of_total_comments, char_count_of_total_comments / word_count_of_total_comments,
        today_char_count_of_total_comments, today_word_count_of_total_comments, today_sentence_count_of_total_comments,
        char_count_of_total_ideas + char_count_of_total_comments, word_count_of_total_ideas + word_count_of_total_comments, sentence_count_of_total_comments + sentence_count_of_total_ideas, ((char_count_of_total_comments / word_count_of_total_comments) + (char_count_of_total_ideas / word_count_of_total_ideas)) / 2,
        user_register_dates, idea_publish_dates, comment_publish_dates
        ))
        return redirect('index-page')

def InspectIdeaView(request, idea_id: int, sorting_method: str = "sort-by-date"):
    try:
        if request.user.is_anonymous:
            idea_object = Idea.objects.get(Q(id=idea_id) & Q(idea_archived=False))
        else:
            idea_object = Idea.objects.get(Q(id=idea_id) & Q(idea_archived=False))
        if sorting_method == "sort-by-date":
            comments = (
                Comment.objects.filter(comment_idea=idea_object)
                .order_by("comment_publish_date")
            )
            # for comment in comments:
            #     print(comment.comment_content, comment.comment_publish_date)
        else: 
            comments = (
                Comment.objects.filter(comment_idea=idea_object)
                .order_by("comment_like_count")
                .reverse()
            )
    except Idea.DoesNotExist:
        return redirect("index-page")
    else:
        ideas = Idea.objects.filter(Q(idea_archived=False))
        all_comments = Comment.objects.filter(Q(comment_archived=False))
        return render(
            request,
            "inspect_idea.html",
            {
                "topic": Topic.objects.first(),
                "idea": idea_object,
                "comments": comments,
                "comments_count": len(all_comments),
                "ideas_count": len(ideas),
                "section": "inspect-idea",
                "profile": get_user_profile(request.user),
                "user_icon": get_user_badge(idea_object.idea_author.account),
                "redirect_to": f"/inspect-idea/{idea_id}/sort-by-likes" if sorting_method == "sort-by-date" else f"/inspect-idea/{idea_id}/sort-by-date",
                "sort_msg": "Tarihe Göre" if sorting_method == "sort-by-date" else "Beğeniye Göre",
            },
        )


def LeaderboardView(request):
    ideas = Idea.objects.filter(Q(idea_archived = False))

    comments = Comment.objects.filter(Q(comment_archived = False))
    all_profiles =  Profile.objects.all().filter(Q(account__is_superuser = False) & Q(account__is_staff = False)).order_by('-total_point')
    profiles = all_profiles[:10]


    IncrementLogin(request)

    return render(
        request,
        "leaderboard.html",
        {
            "profile": get_user_profile(request.user),
            "profiles": profiles,
            "topic": Topic.objects.first(),
            "comments_count": len(comments),
            "ideas_count": len(ideas),
            'section': 'leaderboard'
        },
    ) 

def EditIdeaView(request, idea_id: int):
    return redirect(request.META.get("HTTP_REFERER"))


def SurveyView(request):
    return redirect('https://forms.gle/B6ER4AqcpXQZFsSd9')


@user_passes_test(lambda u: u.is_anonymous)
def RegisterView(request):
    if request.POST:
        try:
            kvkk_check = request.POST["kvkk"]
        except KeyError:
            messages.error(
                request,
                "Kayıt olmak için KVKK'yı kabul etmelisin.",
                extra_tags=NOTIFICATION_TAGS["error"],
            )
            return redirect(request.META.get("HTTP_REFERER"))

        else:
          
            username, password, email, reference_code = request.POST["username"], request.POST["password"], request.POST["email"], request.POST["reference_code"] 

            try:
                found_user = User.objects.filter(Q(username=username) | Q(email=email))
                found_profile = Profile.objects.filter(Q(ip_addresses__has_key = get_client_ip(request, 'server')))
            except User.DoesNotExist:
                pass 
            else:
                if found_user or False:
                    messages.error(
                        request,
                        "Bu bilgilere ait bir hesap zaten var!",
                        extra_tags=NOTIFICATION_TAGS["error"],
                    )
                    return redirect(request.META['HTTP_REFERER'])
            kvkk_check = True


            try:
                validate_email(email)

                if email.endswith('.com') or email.endsiwth('.net'):
                    pass 
                else:
                    messages.error(request, 'Bu e-posta adresi ile kayıt olamazsınız.', extra_tags=NOTIFICATION_TAGS["error"],)
                    return redirect(request.META['HTTP_REFERER']) 
            except ValidationError:
                messages.error(request, 'Bu e-posta adresi ile kayıt olamazsınız.', extra_tags=NOTIFICATION_TAGS["error"],)
                return redirect(request.META['HTTP_REFERER'])

            user = User.objects.create_user(
                username=username, password=password, email=email
            )

            if user is not None:
                login(request, user)
                
                messages.success(
                    request,
                    "Başarıyla hesabınızı oluşturdunuz.",
                    extra_tags=NOTIFICATION_TAGS["success"],
                )
                referenced_name: str = ''
                if len(reference_code) == 6:
                    try:
                        referenced_user = Profile.objects.get(user_secret=reference_code)
                    except:
                        pass
                    else:
                        try:
                            referenced_user.profile_referred[request.user.username] = str(datetime.datetime.now())
                        except:
                            referenced_user.profile_referred = {}
                            referenced_user.profile_referred[request.user.username] = str(datetime.datetime.now())
                        finally:
                            referenced_user.save()
                            referenced_name = referenced_user.account.username

                profile = Profile.objects.create(
                    account=user,
                    web_theme="Thinker Tema",
                    kvkk_agreed=True,
                    email_permission=True,
                    total_logged_time=datetime.timedelta(seconds=1),
                    last_logged_in=datetime.datetime.now(),
                    profile_rank="rookie",
                    profile_referenced_by=referenced_name
                )
                profile.save()

            else:
                messages.error(
                    request,
                    "Hesabınız bizden kaynaklı bir sorundan ötürü oluşturulamadı. [#0001]",
                    extra_tags=NOTIFICATION_TAGS["error"],
                )

    return redirect('authentication')

@user_passes_test(lambda u: not u.is_anonymous)
def LogoutView(request):
    messages.info(
        request,
        f"Hesabınızdan çıkış yaptınız: {request.user.username}",
        extra_tags=NOTIFICATION_TAGS["info"],
    ),

    logged_out = datetime.datetime.now()
    profile = Profile.objects.get(account=request.user)
    logged_time = logged_out - profile.last_logged_in
    profile.total_logged_time = profile.total_logged_time + logged_time
    profile.save()

    logout(request)

    return redirect("index-page")


def PublishIdeaView(request):
    if request.user.is_anonymous: 
    
        messages.error(
            request,
            "Bu işlem için giriş yapman gerekiyor!",
            extra_tags=NOTIFICATION_TAGS["error"],
        )
        return redirect('authentication')

    if request.POST:
        no_msg = False
        try:
            profile = get_user_profile(request.user)
            referenced_user: User = User.objects.get(username=profile.profile_referenced_by)
        except Profile.DoesNotExist:
            pass 
        except User.DoesNotExist:
            pass 
        else:
            if len(Idea.objects.filter(idea_author=profile)) == 0 and referenced_user:
                no_msg = True
                GivePoint(request.user, POINT_POLICY['reference_idea_point'])
                GivePoint(referenced_user, POINT_POLICY['reference_idea_point'])
                messages.info(request, f'Referansınla beraber 50 puan kazandın!', NOTIFICATION_TAGS['info'])

                referenced_profile: Profile = Profile.objects.get(account=referenced_user)

                referenced_profile.user_notifications[str(uuid.uuid4())] = {
                    'notification_content': f'Referansın {request.user.username}, sana 50 puan kazandırdı!',
                    'notification_details': str(datetime.datetime.now()),
                    'notification_image': 'robot',
                    'notification_link': '/',
                    'viewed': False
                }

                referenced_profile.save()
                
                profile.user_notifications[str(uuid.uuid4())] = {
                    'notification_content': f'Fikir paylaştığın için referansın ve sen 50 puan kazandınız!',
                    'notification_details': str(datetime.datetime.now()),
                    'notification_image': 'robot',
                    'notification_link': '/',
                    'viewed': False
                }

                profile.save()


        idea_content = request.POST["idea-content"]
        idea = Idea.objects.create(
            idea_author=Profile.objects.get(account=request.user),
            idea_content=idea_content,
            idea_topic=Topic.objects.first().topic_name
        )
        idea.save()

        if not no_msg:
            messages.success(
                request,
                "Başarıyla fikrinizi paylaştınız!",
                extra_tags=NOTIFICATION_TAGS["success"],
            )


        return redirect('inspect-idea-page', idea.pk)

def PublishSurveyView(request):
    if request.user.is_anonymous: 
    
        messages.error(
            request,
            "Bu işlem için giriş yapman gerekiyor!",
            extra_tags=NOTIFICATION_TAGS["error"],
        )
        return redirect('authentication')

    if request.POST:
        survey_content = request.POST["survey-content"]
        survey_options = request.POST['survey-options'].split(',')
        survey_date = datetime.datetime.strptime(request.POST['survey-date'], '%Y-%m-%dT%H:%M')
        
        if len(survey_options) > 5 or len(survey_options) < 1:
            messages.error(
                request,
                "Kelimelerini virgülle ayırmalısın. (En fazla 5 kelime)",
                extra_tags=NOTIFICATION_TAGS["error"],
            )
            return redirect('open-surveys-page')

        survey_votes = {}
        for survey_option in survey_options:
            trimmed_option = survey_option.strip().capitalize()
            survey_votes[str(uuid.uuid4())] = {
                'info': {
                    'title': trimmed_option,
                    'ratio': 0
                },
                'participants': {}
            }

        if survey_date >= datetime.datetime.now():

            survey = Survey.objects.create(
                survey_author=Profile.objects.get(account=request.user),
                survey_content=survey_content,
                survey_votes=survey_votes,
                survey_end_date=survey_date
            )
            survey.save()

            messages.success(
                request,
                "Başarıyla anketinizi paylaştınız!",
                extra_tags=NOTIFICATION_TAGS["success"],
            )
        else:
            messages.error(
                request,
                "Anketin bitiş tarihini doğru girmelisin.",
                extra_tags=NOTIFICATION_TAGS["error"],
            )


        return redirect('open-surveys-page')

def LikePostView(request, post_id: int):
    if request.user.is_anonymous:
        messages.error(
            request,
            "Bu işlem için giriş yapman gerekiyor!",
            extra_tags=NOTIFICATION_TAGS["error"],
        )
        return redirect('authentication')

    try:
        idea_object = Idea.objects.get(id=post_id)
    except Idea.DoesNotExist:
        return redirect("index-page")
    else:
        try:
            idea_object.idea_likes[request.user.username]
        except KeyError:
            idea_object.idea_like_count += 1
            idea_object.idea_likes[request.user.username] = True
            idea_object.save()

            idea_object.idea_author.user_notifications[create_hash(16)] = {
              'notification_content': f'{request.user.username} fikrinizi beğendi',
              'notification_details': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
              'notification_image': 'robot',
              'notification_link': f'/inspect-idea/{post_id}',
              'viewed': False
            }
            
            idea_object.idea_author.save()
            
            GivePoint(idea_object.idea_author.account, POINT_POLICY["like_idea"])

        else:
            idea_object.idea_like_count -= 1
            del idea_object.idea_likes[request.user.username]
            idea_object.save()

            TakePoint(idea_object.idea_author.account, POINT_POLICY["like_idea"])


        return redirect(request.META["HTTP_REFERER"])



def SendCommentView(request, idea_id: int):
    if request.user.is_anonymous: 
        messages.error(
            request,
            "Bu işlem için giriş yapman gerekiyor!",
            extra_tags=NOTIFICATION_TAGS["error"],
        )
        return redirect('authentication')
    if request.POST:
        try:
            idea_object = Idea.objects.get(id=idea_id)
        except Idea.DoesNotExist:
            return redirect("inspect-idea-page", idea_id)
        else:


            comment_content = request.POST['comment_content']
            
            Comment.objects.create(comment_idea = idea_object, comment_author = Profile.objects.get(account=request.user), comment_content = comment_content, comment_topic=Topic.objects.first().topic_name, comment_publish_date=datetime.datetime.now()).save()
            idea_object.idea_comments += 1
            idea_object.save()
            
            idea_object.idea_author.user_notifications[create_hash(16)] = {
              'notification_content': f'{request.user.username} fikrinize yorum yaptı',
              'notification_details': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              'notification_image': 'robot',
              'notification_link': f'/inspect-idea/{idea_id}',
              'viewed': False
              }
            
            idea_object.idea_author.save()
            
            messages.success(
                    request,
                    "Başarıyla yorumunuzu paylaştınız!",
                    extra_tags=NOTIFICATION_TAGS["success"],
                )


    return redirect("inspect-idea-page", idea_id)
    
    
def LikeCommentView(request, idea_id: int,  comment_id: int):
    if request.user.is_anonymous: 
      messages.error(
          request,
          "Bu işlem için giriş yapman gerekiyor!",
          extra_tags=NOTIFICATION_TAGS["error"],
      )
      return redirect('authentication')
  
    try:
        comment_object = Comment.objects.get(id=comment_id)
    except Idea.DoesNotExist:
        return redirect("inspect-idea-page", idea_id)
    else:
        try:
            comment_object.comment_likes[request.user.username]
        except KeyError:
            try:
                comment_object.comment_dislikes[request.user.username]
            except KeyError:
                pass
            else:

                comment_object.comment_dislike_count -= 1
                del comment_object.comment_dislikes[request.user.username]
            finally:
                comment_object.comment_author.user_notifications[create_hash(16)] = {
                  'notification_content': f'{request.user.username} yorumunuzu beğendi',
                  'notification_details': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  'notification_image': 'robot',
                  'notification_link': f'/inspect-idea/{idea_id}',
                  'viewed': False
                }
            
                comment_object.comment_author.save()
              
                comment_object.comment_like_count += 1
                comment_object.comment_likes[request.user.username] = True
                comment_object.save()

        else:
          
            comment_object.comment_like_count -= 1
            del comment_object.comment_likes[request.user.username]
            comment_object.save()

        return redirect("inspect-idea-page", idea_id)


def DislikeCommentView(request, idea_id: int, comment_id: int):
    if request.user.is_anonymous:
        messages.error(
            request,
            "Bu işlem için giriş yapman gerekiyor!",
            extra_tags=NOTIFICATION_TAGS["error"],
        )
        return redirect('authentication')

    try:
        comment_object = Comment.objects.get(id=comment_id)
    except Idea.DoesNotExist:
        return redirect("inspect-idea-page", idea_id)
    else:
        try:
            comment_object.comment_dislikes[request.user.username]
        except KeyError:
            try:
                comment_object.comment_likes[request.user.username]
            except KeyError:
                pass
            else:
              
              
                comment_object.comment_like_count -= 1
                del comment_object.comment_likes[request.user.username]
            finally:
                comment_object.comment_author.user_notifications[create_hash(16)] = {
                  'notification_content': f'{request.user.username} yorumunuzu beğenmedi',
                  'notification_details': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  'notification_image': 'robot',
                  'notification_link': f'/inspect-idea/{idea_id}',
                  'viewed': False
                }
            
                comment_object.comment_author.save()
              
                comment_object.comment_dislike_count += 1
                comment_object.comment_dislikes[request.user.username] = True
                comment_object.save()
        else:
            comment_object.comment_dislike_count -= 1
            del comment_object.comment_dislikes[request.user.username]
            comment_object.save()

        return redirect("inspect-idea-page", idea_id)

def ViewNotificationView(request, notification_key):
  profile = get_user_profile(request.user)
  try:
    profile.user_notifications[notification_key]
  except KeyError:
    return redirect('index-page')
  else:
    profile.user_notifications[notification_key]['viewed'] = True 
    profile.save()

    return redirect(profile.user_notifications[notification_key]["notification_link"])
    
def handle_404(request, exception):
    return render(request, "404.html")

@user_passes_test(lambda u: u.is_anonymous)
def ForgotPasswordView(request):
  IncrementLogin(request)
  if request.POST:
    return 
  else:
    return render(
        request,
        "forgot_password.html",
        {
            "section": "forgot-password",
        },
    ) 

@user_passes_test(lambda u: not u.is_anonymous)
def RateTopicView(request):
    if request.GET:
        topic = Topic.objects.first()
        try:
            topic_voted = topic.topic_rate['voted']
        except KeyError:
            topic.topic_rate = {'rate': 0, 'voted': {}}
            topic_voted = topic.topic_rate['voted']
        except TypeError:
            topic.topic_rate = {'rate': 0, 'voted': {}}
            topic_voted = topic.topic_rate['voted']
        
        if request.user.username not in topic_voted:
            user_rate = request.GET['rate']
            topic.topic_rate['voted'][request.user.username] = int(user_rate) 
            topic.topic_rate['rate'] = sum([int(topic_rate) for topic_rate in topic.topic_rate['voted'].values()]) / len(topic.topic_rate['voted'])
            topic.save()
            return redirect('index-page')
        else:
            return redirect('index-page')

def DailyResetView(request, token: str):   
    if token == "DAILY_BACKUP" and get_client_ip(request, 'server') == '37.59.221.234':
        mail = EmailMessage('Günlük Veritabanı Yedeği Alındı - justhink.net', 'Bugüne ait veritabanı yedeğinin SQL ve JSON dosyaları.', settings.EMAIL_HOST_USER, ['furkanesen1900@gmail.com', 'ogulcanozturk72@gmail.com'])
        backup_file_name = fr'C:\Users\Administrator\Desktop\Database Backups\Daily Backups\Database Backup'
        sysout = sys.stdout
        with open(f'{backup_file_name}.json' , 'w+', encoding='utf-8') as f:
            sys.stdout = f 
            call_command('dumpdata',)
            sys.stdout = sysout
        
        with open(f'{backup_file_name}.json' , 'r', encoding='utf-8') as f:
            mime = magic.Magic(mime=True)
            mail.attach(f.name, f.read(), mime.from_file(f'{backup_file_name}.json'))

        sysout = sys.stdout
        with open(f'{backup_file_name}.sql' , 'w+', encoding='utf-8') as f:
            sys.stdout = f 
            call_command('dumpdata',)
            sys.stdout = sysout

        with open(f'{backup_file_name}.sql' , 'r', encoding='utf-8') as f:
            mime = magic.Magic(mime=True)
            mail.attach(f.name, f.read(), mime.from_file(f'{backup_file_name}.sql'))
        mail.send()

    elif token == "DAILY_RESET" and get_client_ip(request, 'server') == '37.59.221.234':
        not_archived_ideas = Idea.objects.filter(idea_archived = False)
        not_archived_ideas.update(idea_archived = True)
        
        not_archived_comments = Comment.objects.filter(comment_archived = False)
        not_archived_comments.update(comment_archived = True)

        not_archived_surveys = Survey.objects.filter(survey_archived = False)
        not_archived_surveys.update(survey_archived = True)

        Profile.objects.all().update(user_notifications = {})

        topic = Topic.objects.first()
        topic.topic_rate = {}
        topic.save()



    return redirect('index-page')

def ContactUsView(request):
    if request.POST:
        full_name, email_address, message = request.POST['full-name'], request.POST['email-address'], request.POST['message']

        author = False
        if request.user.is_anonymous:
            author = Profile.objects.first()
        else:
            author = Profile.objects.get(account=request.user)

        feedback = Feedback.objects.create(feedback_author = author, feedback_fullname=full_name, feedback_email=email_address, feedback_message=message)

        send_mail('Yeni bir geribildirim var! - justhink.net', f'Yeni bir geribildirim mevcut! \n\nGönderen: {full_name} ({email_address})\nMesaj: {message}\n\nAdmin Panelde Görüntülemek için: https://justhink.net/admin/idea/feedback/{feedback.pk}/change/', 'iletisim@justhink.net', ['furkanesen1900@gmail.com', 'paladilasu@gmail.com', 'ogulcanozturk72@gmail.com'], fail_silently=True) #, 'kadircantuzuner@gmail.com', 'paladilasu@gmail.com'


    return render(request, 'contact_us.html', {"profile": get_user_profile(request.user),
                    "section": "contact-us"})


def BlogPartyView(request):
    return redirect('https://justhink.blog/justhinke-hos-geldiniz/')