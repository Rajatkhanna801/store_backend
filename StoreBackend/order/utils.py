

def generate_upi_payment_data(amount, order_id, merchant_id="merchant@upi"):
    """
    Generate basic UPI payment data for QR code display
    """
    return f"upi://pay?pa={merchant_id}&pn=Store&am={amount}&tn=Order#{order_id}&cu=INR"

def validate_inventory_for_order(cart_items):
    """
    Validate if there's sufficient inventory for the order
    Returns: (is_valid, errors_list)
    """
    errors = []
    
    for cart_item in cart_items:
        if cart_item.quantity > cart_item.product.quantity:
            errors.append(
                f"Product '{cart_item.product.name}' has only {cart_item.product.quantity} in stock, but {cart_item.quantity} requested"
            )
    
    return len(errors) == 0, errors
