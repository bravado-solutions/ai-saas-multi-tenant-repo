import os
import json
import redis
import uvicorn
from typing import List
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator

from openai import OpenAI  # ✅ NEW SDK

# Internal Imports
from database import SessionLocal, engine, Base
from auth import get_current_tenant, router as auth_router
from vector_service import init_qdrant, search_knowledge
from webhooks import router as webhook_router
from events import publish_event  # Event-driven system

# Middleware Imports
from middleware import tenant_context_middleware  # ✅ 1. Import your middleware logic
from starlette.middleware.base import BaseHTTPMiddleware # ✅ 2. Import the required wrapper

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize FastAPI
app = FastAPI(
    title="Bravado Solutions AI SaaS API",
    description="Enterprise-grade Multi-tenant RAG Backend",
    version="2.1.0"
)

# --- 1. OBSERVABILITY & MIDDLEWARE ---
Instrumentator().instrument(app).expose(app)

# A. Register Custom Tenant Context Middleware ✅
# This must be registered before routes to ensure request.state.tenant_id is populated.
app.add_middleware(BaseHTTPMiddleware, dispatch=tenant_context_middleware)

# B. CORS Middleware
origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,https://app.bravado.io"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. EXTERNAL CLIENTS ---
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=6379,
    db=0,
    decode_responses=True
)

# --- 3. DATABASE DEPENDENCY ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 4. LIFECYCLE EVENTS ---
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    await init_qdrant()

    print("✅ API service started successfully")

# --- 5. ROUTER REGISTRATION ---
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(webhook_router, prefix="/webhooks", tags=["billing"])

# --- 6. HEALTH CHECK ---
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        redis_client.ping()

        return {
            "status": "healthy",
            "postgres": "connected",
            "redis": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service Unavailable: {str(e)}"
        )

# --- 7. CHAT ENDPOINT (EVENT-DRIVEN) ---
@app.post("/chat")
async def chat_endpoint(
    request_data: dict,
    tenant=Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    query = request_data.get("query")

    if not query or not isinstance(query, str):
        raise HTTPException(
            status_code=400,
            detail="Valid query text is required"
        )

    try:
        # 1. Generate embedding (NEW SDK)
        embedding_resp = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        vector = embedding_resp.data[0].embedding

        # 2. Vector search (tenant-isolated)
        search_results = await search_knowledge(
            tenant['id'],
            vector
        )

        # 3. 🔥 NON-BLOCKING EVENT PUBLISH
        try:
            publish_event("usage.logged", {
                "tenant_id": tenant['id'],
                "tokens": 1,
                "endpoint": "/chat"
            })
        except Exception as event_error:
            print(f"⚠️ Event publish failed: {event_error}")

        # 4. Response
        return {
            "tenant_id": tenant['id'],
            "results": [
                {
                    "content": r.payload.get("text_content"),
                    "score": r.score
                }
                for r in search_results
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI Search Error: {str(e)}"
        )

# --- 8. INGEST ENDPOINT (ASYNC EVENT-DRIVEN) ---
@app.post("/ingest")
async def ingest_document(
    request: Request,
    tenant=Depends(get_current_tenant)
):
    body = await request.json()
    content = body.get("content")

    if not content or len(content) < 10:
        raise HTTPException(
            status_code=400,
            detail="Content too short"
        )

    task_id = str(uuid4())

    payload = {
        "tenant_id": tenant['id'],
        "doc_id": task_id,
        "content": content
    }

    try:
        publish_event("document.ingest.requested", payload)

        return {
            "status": "queued",
            "task_id": task_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue task: {str(e)}"
        )

# --- 9. ROOT ---
@app.get("/")
async def root():
    return {
        "message": "Bravado AI SaaS API is running",
        "version": "2.1.0"
    }

# --- 10. LOCAL RUN ---
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )