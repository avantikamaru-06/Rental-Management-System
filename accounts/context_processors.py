"""
accounts/context_processors.py
Injects a safe `customer_profile` variable into every template context.
Avoids crashes when the logged-in user is an admin superuser without a Customer model entry.
"""
from customers.models import Customer
from .permissions import get_user_role

def customer_profile_context(request):
    """Adds `customer_profile` to all templates safely."""
    if request.user.is_authenticated:
        try:
            profile = request.user.customer_profile
        except Customer.DoesNotExist:
            profile = None
    else:
        profile = None
    return {
        'customer_profile': profile,
        'user_role': get_user_role(request.user),
    }
