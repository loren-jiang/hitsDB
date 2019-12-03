from django import template

register = template.Library()

@register.filter(name='add')
def add(n, k):
    return n + k
    
@register.filter(name='times')
def times(n):
    return range(int(n))

@register.filter
def hash(h, key):
    return h.get(key,'')

# @register.filter
# def getattr(h, attr):
#     return getattr(h, attr)