from django import template

register = template.Library()


@register.filter
def deadline_badge_class(opportunity):
    state = getattr(opportunity, "deadline_state", "unknown")
    mapping = {
        "safe": "bg-green-100 text-green-700",
        "warning": "bg-yellow-100 text-yellow-700",
        "urgent": "bg-red-100 text-red-700",
        "expired": "bg-rose-100 text-rose-700",
        "unknown": "bg-slate-100 text-slate-600",
    }
    return mapping.get(state, mapping["unknown"])


@register.filter
def days_until(opportunity):
    days_left = getattr(opportunity, "days_until_deadline", None)
    if days_left is None:
        return "No deadline"
    if days_left < 0:
        return f"Passed {abs(days_left)} day(s) ago"
    return f"{days_left} day(s) left"
