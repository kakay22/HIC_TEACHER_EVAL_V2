from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def time_badge(value):
    if not value:
        return ""

    now = timezone.now()
    diff = now - value

    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = diff.days

    if seconds < 60:
        return "Just now"
    elif minutes < 60:
        return f"{int(minutes)}m ago"
    elif hours < 24:
        return f"{int(hours)}h ago"
    elif days == 1:
        return "Yesterday"
    else:
        return f"{days}d ago"