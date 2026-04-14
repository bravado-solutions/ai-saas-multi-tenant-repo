import stripe
import os
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, Tenant

router = APIRouter()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post("/stripe")
async def stripe_webhook(
    request: Request, 
    stripe_signature: str = Header(None), 
    db: Session = Depends(get_db)
):
    payload = await request.body()
    try:
        # 1. ALWAYS verify the signature to prevent spoofing
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail="Invalid payload or signature")

    # Event 1: Payment Successful -> Activate Tenant
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # We passed tenant_id as client_reference_id during session creation
        tenant_id = session.get('client_reference_id')
        stripe_customer_id = session.get('customer')
        
        if tenant_id:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant:
                tenant.stripe_id = stripe_customer_id
                tenant.subscription_status = "active"
                db.commit()

    # Event 2: Subscription Updated (Handling Upgrades/Downgrades)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        status = subscription.get('status') # e.g., 'active', 'past_due', 'unpaid'
        
        tenant = db.query(Tenant).filter(Tenant.stripe_id == customer_id).first()
        if tenant:
            tenant.subscription_status = status
            db.commit()

    # Event 3: Subscription Canceled
    elif event['type'] == 'customer.subscription.deleted':
        obj = event['data']['object']
        customer_id = obj.get('customer')
        
        tenant = db.query(Tenant).filter(Tenant.stripe_id == customer_id).first()
        if tenant:
            tenant.subscription_status = "inactive"
            db.commit()

    # Always return 200 to Stripe quickly to acknowledge receipt
    return {"status": "success"}