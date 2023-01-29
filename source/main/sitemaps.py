from django.contrib.sitemaps import Sitemap 
from django.shortcuts import reverse 
from user_profile.models import Profile
from idea.models import Idea 

class StaticViewSiteMap(Sitemap):
    @staticmethod
    def items():
        return ['index-page', 'ideas-page', 'random-ideas-page',  'home', 'about-us-page']
    @staticmethod
    def location(item):
        return reverse(item)

class ProfileSiteMap(Sitemap):
    changefreq = 'hourly'
    priority = 0.9

    @staticmethod
    def items():
        return Profile.objects.all()

class IdeaSiteMap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    @staticmethod
    def items():
        return Idea.objects.all()