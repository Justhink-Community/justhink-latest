from django import template
from main.views import get_user_badge
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(name='get_group_icon')
def get_group_icon(user):
    return mark_safe(get_user_badge(user))
  