from django import template
import os

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})


@register.filter
def basename(value):
    return os.path.basename(value)


@register.filter(name='call_method')
def call_method(obj, arg):
    """Вызывает метод объекта с аргументом"""
    if hasattr(obj, '__call__'):
        return obj(arg)
    return False
