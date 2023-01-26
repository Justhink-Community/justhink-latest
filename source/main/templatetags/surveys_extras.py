from django import template
from idea.models import Survey

register = template.Library()

@register.simple_tag(name='check_user_participation')
def check_user_participation(username: str, survey_id: int):
    try:
        survey = Survey.objects.get(pk=survey_id)
    except Survey.DoesNotExist:
        return False 
    else:
        return survey.check_user_participation(username)
  