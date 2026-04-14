import os
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, User, Tenant

router = APIRouter()

# Config
SECRET_KEY = os.getenv("JWT_SECRET", "bravado-secret-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helpers
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- ENDPOINTS ---

@router.post("/signup")
async def signup(user_request: dict, db: Session = Depends(get_db)):
    """Creates a new Tenant (Company) and the first Admin User."""
    email = user_request.get("email")
    password = user_request.get("password")
    company = user_request.get("companyName")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="User already exists")

    # 1. Create Tenant
    new_tenant_id = str(uuid4())
    new_tenant = Tenant(id=new_tenant_id, company_name=company)
    db.add(new_tenant)

    # 2. Create User linked to Tenant
    new_user = User(
        email=email,
        hashed_password=hash_password(password),
        tenant_id=new_tenant_id
    )
    db.add(new_user)
    db.commit()

    return {"message": "Tenant created successfully", "tenant_id": new_tenant_id}

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Standard OAuth2 token endpoint for the login form."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(data={"tenant_id": user.tenant_id, "sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


    """Dependency used by other routes to ensure the user is authenticated and active."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id: str = payload.get("tenant_id")
        if tenant_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Verify Tenant exists and is active (Sprint 2 will harden the 'active' check)
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=403, detail="Tenant not found")
            
        return {"id": tenant_id, "status": tenant.subscription_status}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    
async def get_current_tenant(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id: str = payload.get("tenant_id")
        
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        # GATEKEEPER LOGIC
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        if tenant.subscription_status != "active":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED, 
                detail="Subscription inactive. Please update billing."
            )
            
        return {"id": tenant_id, "stripe_id": tenant.stripe_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired")