import os
import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Boolean

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/bravado_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, index=True)
    company_name = Column(String)
    stripe_id = Column(String, nullable=True)
    subscription_status = Column(String, default="inactive") # active, inactive, past_due
    
    # Relationship to users
    users = relationship("User", back_populates="tenant")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    
    tenant = relationship("Tenant", back_populates="users")

class Usage(Base):
    __tablename__ = "usage_logs"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String)
    tokens = Column(Integer)
    endpoint = Column(String) # e.g., "/chat" or "/ingest"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    synced_to_stripe = Column(Boolean, default=False)

def init_db():
    Base.metadata.create_all(bind=engine)