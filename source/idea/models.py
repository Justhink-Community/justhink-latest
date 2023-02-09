import datetime
from user_profile.models import Profile
from django.contrib.auth.models import User
from django.db import models

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import get_connection, EmailMultiAlternatives
from django.shortcuts import reverse


def send_mass_html_mail(datatuple, fail_silently=False, user=None, password=None, 
                        connection=None):
    """
    Given a datatuple of (subject, text_content, html_content, from_email,
    recipient_list), sends each message to each recipient list. Returns the
    number of emails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

    """
    connection = connection or get_connection(
        username=user, password=password, fail_silently=fail_silently)
    messages = []
    for subject, text, html, from_email, recipient in datatuple:
        message = EmailMultiAlternatives(subject, text, from_email, recipient)
        message.attach_alternative(html, 'text/html')
        messages.append(message)
    return connection.send_messages(messages)

        
class Idea(models.Model):
    idea_author = models.ForeignKey(to=Profile, on_delete=models.CASCADE)
    idea_content = models.TextField()
    idea_publish_date = models.DateTimeField(auto_now=True)

    idea_likes = models.JSONField(default=dict)
    idea_like_count = models.IntegerField(editable=False, default=0)
    idea_comments = models.IntegerField(editable=False, default=0)

    idea_topic = models.CharField(max_length=100, default="Belirlenemedi.", null=True, editable=True)

    idea_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.idea_content

    def get_absolute_url(self,):
        return reverse('inspect-idea-page', args=[self.pk,])

class Survey(models.Model):
    survey_author = models.ForeignKey(to=Profile, on_delete=models.CASCADE)
    survey_content = models.CharField(max_length=40)
    survey_publish_date = models.DateTimeField(auto_now=True)
    survey_end_date = models.DateTimeField()

    survey_votes = models.JSONField(default=dict, null=True, blank=True)

    survey_archived = models.BooleanField(default=False) 

    def get_survey_option(self, option_id: str):
        return self.survey_votes[str(option_id)] if str(option_id) in self.survey_votes else False

    def clear_user_votes(self, username: str):
        for key, value in self.survey_votes.items():
            if username in value['participants']:
                del value['participants'][username]
        self.adapt_ratios()
        self.save()

    def did_participate_user(self, username: str):
        for key, value in self.survey_votes.items():
            if username in value['participants']:
                return key, value

    def calculate_total_participants(self):
        participants = [len(option['participants']) for option in self.survey_votes.values()] 
        return sum(participants)

    def calculate_ratio(self, option_id: str):
        try:
            ratio: float = ( len(self.survey_votes[option_id]['participants']) * 100 ) / self.calculate_total_participants()
        except ZeroDivisionError:
            ratio: float = 0.0
        return int(ratio) 

    def adapt_ratios(self, option_id: str = ''):
        for key, value in self.survey_votes.items():
            if option_id != key:
                value['info']['ratio'] = self.calculate_ratio(key)
        self.save()
        return True

    def check_user_participation(self, username: str):
        return any(username in value['participants'] for value in self.survey_votes.values())

    @property
    def is_past_due(self):
        return datetime.datetime.now() > self.survey_end_date

    @classmethod 
    def get_available_surveys(cls):
        return [survey for survey in cls.objects.all() if survey.survey_archived is False and survey.is_past_due is False]


    def __str__(self):
        return self.survey_content 
    
class Comment(models.Model):
    comment_idea = models.ForeignKey(to=Idea, on_delete=models.CASCADE)
    comment_author = models.ForeignKey(to=Profile, on_delete=models.CASCADE)
    comment_content = models.TextField()
    comment_publish_date = models.DateTimeField()

    comment_likes = models.JSONField(editable=False, default=dict)
    comment_like_count = models.IntegerField(editable=False, default=0)
    
    comment_dislikes = models.JSONField(editable=False, default=dict)
    comment_dislike_count = models.IntegerField(editable=False, default=0)

    comment_topic = models.CharField(max_length=100, default="Belirlenemedi.", null=True, editable=True)

    comment_archived = models.BooleanField(default=False)
    
class Topic(models.Model):
  topic_name = models.CharField(max_length=100)
  topic_sources = models.TextField()
  topic_keywords = models.CharField(max_length=40)
  topic_date = models.DateTimeField()
  topic_video_id = models.CharField(max_length=16)
  topic_rate = models.JSONField(default=dict, null=True, blank=True, editable=True)
  topic_survey = models.JSONField(null=False, blank=False, default=dict)
  special_topic_message = models.CharField(max_length=70, default="Bu pazar günü Yıldızlararası filmini tartışıyoruz!", blank=False, null=False)

  def save(self, *args, **kwargs):
    today = datetime.datetime.now()
    if today.date() != self.topic_date.date(): 
        self.topic_date = today 
    
        


    
    super().save(*args, **kwargs)
  def send_mail(self):
        ctx = {
        'subtitle': 'Günün konusu hazır:',
        'title': self.topic_name,
        'paragraph_1': self.topic_sources[:500] + '...'
        }
        html_message = render_to_string('dynamic_mail.html', ctx)
        plain_message = strip_tags(html_message)
        send_mass_html_mail(
            [('Günün konusu hazır! - justhink.net', plain_message, html_message, 'iletisim@justhink.net', [user.email]) for user in [User.objects.get(username="justhink")]],
        fail_silently=True)


class TopicSuggestion(models.Model):
    topic_suggestion_content = models.CharField(max_length=200)
    topic_suggestion_author = models.ForeignKey(to=Profile, on_delete=models.CASCADE)
    topic_suggestion_approved = models.BooleanField(default=False)

    topic_suggestion_publish_date = models.DateTimeField(auto_now=True)

    topic_suggestion_likes = models.JSONField(default=dict)
    topic_suggestion_like_count = models.IntegerField(editable=False, default=0)
    topic_suggestion_comments = models.IntegerField(editable=False, default=0)
    topic_suggestion_archived = models.BooleanField(default=False)

UPDATE_GENRES = (
    ('bugfix', 'Bugfix'),
    ('design', 'Design'),
    ('development', 'Development'),
    ('cybersecurity', 'Cyber Security'),
    ('dbms', 'DBMS'),
)

class Update(models.Model):
    update_genre = models.CharField(choices=UPDATE_GENRES, max_length=20)
    update_work = models.CharField(max_length=75)
    update_date = models.DateTimeField(auto_now_add=True)
    update_authors = models.CharField(max_length=20)
    
class Product(models.Model):
  product_name = models.CharField(max_length=20)
  product_description = models.CharField(max_length=100)
  product_fee = models.IntegerField()
  product_image = models.URLField()
  product_sold_count = models.IntegerField(editable=False, null=False, default=0)


class Feedback(models.Model):
    feedback_author = models.ForeignKey(to=Profile, on_delete=models.CASCADE)
    feedback_fullname = models.CharField(max_length=40)
    feedback_email = models.EmailField()
    feedback_message = models.TextField()