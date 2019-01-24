from django import template

register = template.Library()


@register.filter
def field_correct(dict, key):
    return dict[key+'_correct']


@register.filter
def label_correct(dict, key):
    return dict[key+'_correct'].label


@register.filter
def field_wrong(dict, key):
    return dict[key+'_wrong']


@register.filter
def label_wrong(dict, key):
    return dict[key+'_wrong'].label
