import os
import stripe
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database import Usage, Tenant

# --- CONFIG ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

def sync_usage_to_stripe():
    db = Session()
    print("🔄 Starting Usage Sync to Stripe...")

    # 1. Get total usage per tenant that hasn't been synced yet
    # We filter by 'synced_to_stripe == False' to avoid double-charging
    results = db.query(
        Usage.tenant_id, 
        func.sum(Usage.tokens).label('total_tokens') # Using sum of tokens instead of count
    ).filter(Usage.synced_to_stripe == False).group_by(Usage.tenant_id).all()

    if not results:
        print("✅ No new usage to sync.")
        db.close()
        return

    for tenant_id, token_sum in results:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if tenant and tenant.stripe_id and tenant.subscription_status == "active":
            try:
                # 2. Find the active subscription item for metered billing
                subscriptions = stripe.Subscription.list(customer=tenant.stripe_id, status='active', limit=1)
                
                if subscriptions.data:
                    # Assumes the first item in the subscription is the metered AI usage price
                    si_id = subscriptions.data[0]['items']['data'][0].id
                    
                    # 3. Report usage to Stripe
                    # Use 'increment' to add to the existing period total
                    stripe.SubscriptionItem.create_usage_record(
                        si_id,
                        quantity=int(token_sum),
                        action='increment',
                        timestamp='now'
                    )

                    # 4. MARK AS SYNCED
                    # This prevents these specific records from being pulled in the next run
                    db.query(Usage).filter(
                        Usage.tenant_id == tenant_id,
                        Usage.synced_to_stripe == False
                    ).update({"synced_to_stripe": True}, synchronize_session=False)
                    
                    db.commit()
                    print(f"✅ Synced {token_sum} tokens for Tenant {tenant_id}")
                else:
                    print(f"⚠️ No active subscription found for Tenant {tenant_id}")

            except Exception as e:
                db.rollback()
                print(f"❌ Failed to sync for {tenant_id}: {e}")
        else:
            print(f"⚠️ Skipping {tenant_id}: Missing Stripe ID or Inactive status")

    db.close()
    print("🏁 Sync process finished.")

if __name__ == "__main__":
    sync_usage_to_stripe()