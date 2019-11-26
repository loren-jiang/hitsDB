from django import template

register = template.Library()

@register.filter
def hash(h, key):
    return h.get(key,'')

# @register.filter
# def getattr(h, attr):
#     return getattr(h, attr)