from django.contrib import admin
from .models import Idea, Survey, Comment, Topic, Update, Product, Feedback

# Register your models here.

admin.site.site_header = 'Justhink Yönetim Paneli'

class TopicAdmin(admin.ModelAdmin):
    list_display = ('topic_name', 'topic_keywords', 'topic_date')

    @staticmethod
    def get_readonly_fields(request, obj=None):
        return [f.name for f in obj._meta.fields if not f.editable]

admin.site.register(Topic, TopicAdmin)

class IdeaAdmin(admin.ModelAdmin):
    list_display = ('get_idea_author','pk', 'idea_topic')
    list_filter = ('idea_topic', 'idea_publish_date')

    @admin.display(ordering='idea_author', description='Idea Author')
    def get_idea_author(self, obj):
        return obj.idea_author.account.username

admin.site.register(Idea, IdeaAdmin)

class SurveyAdmin(admin.ModelAdmin):
    list_display = ('get_survey_author','pk', 'survey_content')

    @admin.display(ordering='survey_author', description='Survey Author')
    def get_survey_author(self, obj):
        return obj.survey_author.account.username

admin.site.register(Survey, SurveyAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('get_comment_author','pk',  'get_comment_idea', 'comment_topic')
    list_filter = ('comment_topic', 'comment_publish_date')

    @admin.display(ordering='comment_author', description='Comment Author')
    def get_comment_author(self, obj):
        return obj.comment_author.account.username

    @admin.display(ordering='comment_idea', description='Comment Idea')
    def get_comment_idea(self, obj):
        return obj.comment_idea.pk

admin.site.register(Comment, CommentAdmin)

class UpdateAdmin(admin.ModelAdmin):
    list_display = ('update_work', 'update_genre', 'update_authors', 'update_date')
    list_filter = ('update_genre', 'update_authors', 'update_date')

admin.site.register(Update, UpdateAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_fee', 'product_sold_count')
    list_filter = ('product_name', 'product_fee', 'product_sold_count')

admin.site.register(Product, ProductAdmin)


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('get_feedback_author','pk')

    @admin.display(ordering='feedback_author', description='Feedback Author')
    def get_feedback_author(self, obj):
        return obj.feedback_author.account.username

admin.site.register(Feedback, FeedbackAdmin)