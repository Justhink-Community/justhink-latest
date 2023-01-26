from django import template

register = template.Library()

@register.simple_tag(name='get_theme_logo')
def get_theme_logo(theme):
    if theme == 'default-theme': return 'thinker_logo.svg'
    theme_formatted: str = theme.split(' ')[0].lower()
    if theme_formatted == '':
        return 'thinker_logo.svg'
    return f'{theme_formatted}_logo.svg'

@register.simple_tag(name='get_theme_favicon')
def get_theme_favicon(theme):
    if theme == 'default-theme': return 'thinker-favicon.png'
    theme_formatted: str = theme.split(' ')[0].lower()
    if theme_formatted == '':
        return 'thinker-favicon.png'
    return f'{theme_formatted}-favicon.png'
  
@register.simple_tag(name='get_theme_banner')
def get_theme_banner(theme):
    if theme == 'default-theme': return 'thinker_banner.png'
    theme_formatted: str = theme.split(' ')[0].lower()
    if theme_formatted == '':
        return 'thinker_banner.png'
    return f'{theme_formatted}_banner.png'