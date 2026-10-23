from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def money(amount_minor, currency="INR"):
    value = Decimal(amount_minor) / Decimal(100)
    symbol = "₹" if currency == "INR" else f"{currency} "
    return f"{symbol}{value:,.2f}"


def parse_amount_minor(value):
    try:
        amount = Decimal(value.strip().replace(",", "")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        amount_minor = int(amount * 100)
    except (AttributeError, InvalidOperation, ValueError):
        raise ValueError("Enter a valid amount greater than zero.") from None
    if amount_minor <= 0:
        raise ValueError("Enter a valid amount greater than zero.")
    return amount_minor


def date_text(value):
    try:
        return datetime.fromisoformat(value).astimezone().strftime("%b %d · %I:%M %p")
    except ValueError:
        return value
