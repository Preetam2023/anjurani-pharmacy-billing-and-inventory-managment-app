"""
Pure billing calculations — no database or UI dependency, so this math
can be tested or reused on its own.
"""


def calculate_line_total(unit_price, quantity):
    return round(unit_price * quantity, 2)


def calculate_subtotal(cart_items):
    """cart_items: list of dicts/objects with 'unit_price' and 'quantity'."""
    return round(sum(item["unit_price"] * item["quantity"] for item in cart_items), 2)


def calculate_grand_total(subtotal, discount_percent):
    return round(subtotal * (1 - discount_percent / 100), 2)
