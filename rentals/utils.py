from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone

from .models import RentalOrderItem


def to_decimal(value, default=Decimal('0.00')):
    """Normalize money values to Decimal while tolerating floats and strings."""
    if value is None:
        return default
    return Decimal(str(value))

ACTIVE_RENTAL_STATUSES = ['confirmed', 'picked_up', 'overdue']


def calculate_rental_days(start_date, end_date):
    """Rental Days = End Date - Start Date + 1"""
    if hasattr(start_date, 'date'):
        start = start_date.date()
    else:
        start = start_date
    if hasattr(end_date, 'date'):
        end = end_date.date()
    else:
        end = end_date
    return (end - start).days + 1


def calculate_rental_price(price_per_day, rental_days):
    return to_decimal(price_per_day) * rental_days


def calculate_grand_total(rental_price, deposit):
    return to_decimal(rental_price) + to_decimal(deposit)


def parse_date_input(date_str):
    """Parse YYYY-MM-DD, DD/MM/YYYY, or datetime-local string to an aware datetime."""
    if not date_str:
        return None
    if hasattr(date_str, 'date') and hasattr(date_str, 'hour'):
        return date_str

    text = str(date_str).strip()
    if not text:
        return None

    try:
        if 'T' in text:
            dt = datetime.fromisoformat(text)
        else:
            dt = None
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                return None
            dt = dt.replace(hour=9, minute=0, second=0)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    except (ValueError, TypeError):
        return None


def is_product_available(product_id, start_date, end_date, exclude_order_id=None):
    """Return False if product is already rented for overlapping dates."""
    if hasattr(start_date, 'date'):
        start = start_date.date()
    else:
        start = start_date
    if hasattr(end_date, 'date'):
        end = end_date.date()
    else:
        end = end_date

    if end < start:
        return False

    overlapping = RentalOrderItem.objects.filter(
        product_id=product_id,
        order__status__in=ACTIVE_RENTAL_STATUSES,
        order__pickup_date__date__lte=end,
        order__return_date__date__gte=start,
    )
    if exclude_order_id:
        overlapping = overlapping.exclude(order_id=exclude_order_id)
    return not overlapping.exists()


def get_unavailable_message():
    return "Product is unavailable for selected dates."
