from django import template
from main.views import get_time_span

register = template.Library()

@register.simple_tag(name='get_notification_time')
def get_notification_time(compared_time):
    return get_time_span(compared_time)
  
@register.simple_tag(name='format_notifications')
def format_notifications(notifications):
  return notifications.items()