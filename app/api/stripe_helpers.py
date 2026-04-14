import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(tenant_id: str):
    """Creates a Stripe Checkout session for a specific tenant."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': os.getenv('STRIPE_PRICE_ID'), # e.g., price_H5ggY...
                'quantity': 1,
            }],
            mode='subscription',
            # client_reference_id is our bridge to the Postgres tenant_id
            client_reference_id=tenant_id,
            success_url='https://app.bravado.io/dashboard?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://app.bravado.io/billing',
        )
        return session.url
    except Exception as e:
        return str(e)

def create_portal_session(stripe_customer_id: str):
    """Allows users to manage their subscription (cancel/update card)."""
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url='https://app.bravado.io/dashboard',
    )
    return session.url