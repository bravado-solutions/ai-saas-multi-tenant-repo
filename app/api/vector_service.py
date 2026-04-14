import os
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

# --- 1. CONFIGURATION ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
COLLECTION = "tenant_knowledge" # Matches the worker collection name
VECTOR_SIZE = 1536              # Matches OpenAI text-embedding-3-small

# Initialize the Async client for non-blocking FastAPI performance
client = AsyncQdrantClient(host=QDRANT_HOST, port=6333)

# --- 2. STORAGE INITIALIZATION ---
async def init_qdrant():
    """
    Ensures the vector collection exists with correct dimensions.
    Typically called during FastAPI startup.
    """
    try:
        collections = await client.get_collections()
        exists = any(c.name == COLLECTION for c in collections.collections)

        if not exists:
            await client.create_collection(
                collection_name=COLLECTION,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE, 
                    distance=models.Distance.COSINE
                )
            )
            print(f"🚀 Vector collection '{COLLECTION}' initialized.")
    except Exception as e:
        print(f"❌ Qdrant Init Error: {str(e)}")

# --- 3. ISOLATED SEARCH LOGIC ---
async def search_knowledge(tenant_id: str, vector: list, top_k: int = 5):
    """
    Performs a vector search restricted STRICTLY to the current tenant.
    This is the core security gate for the RAG chat.
    """
    return await client.search(
        collection_name=COLLECTION,
        query_vector=vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="tenant_id", 
                    match=models.MatchValue(value=tenant_id) # Mandatory Isolation
                )
            ]
        ),
        limit=top_k
    )

# --- 4. DATA LIFECYCLE (PURGE) ---
async def purge_tenant_data(tenant_id: str):
    """
    Hard delete of all vectors belonging to a specific tenant.
    Critical for GDPR compliance and account offboarding.
    """
    try:
        await client.delete(
            collection_name=COLLECTION,
            wait=True,  # Ensures physical deletion before returning success
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="tenant_id", 
                        match=models.MatchValue(value=tenant_id)
                    )
                ]
            )
        )
        print(f"🧹 Purged all vector data for Tenant: {tenant_id}")
        return True
    except Exception as e:
        print(f"❌ Purge Error for Tenant {tenant_id}: {str(e)}")
        return False