"""Shared role and permission helpers used across the project."""


def get_user_role(user):
    if not user.is_authenticated:
        return None
    try:
        return user.profile.role
    except Exception:
        return 'admin' if (user.is_superuser or user.is_staff) else 'customer'


def is_admin(user):
    return get_user_role(user) == 'admin'


def is_salesperson(user):
    return get_user_role(user) == 'salesperson'


def is_staff_member(user):
    """Admin or salesperson — staff who manage rentals."""
    role = get_user_role(user)
    return role in ('admin', 'salesperson')


def is_customer(user):
    return get_user_role(user) == 'customer'


def get_dashboard_url_name(user):
    role = get_user_role(user)
    if role == 'admin':
        return 'dashboard:admin_dashboard'
    if role == 'salesperson':
        return 'dashboard:salesperson_dashboard'
    return 'dashboard:customer_dashboard'
