from django import template

register = template.Library()

@register.simple_tag(name='format_content')
def format_content(content: str):
    return content[:590]
  