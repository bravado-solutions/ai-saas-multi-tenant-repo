import os
import uuid
from openai import OpenAI  # ✅ Updated for 2026 SDK
from qdrant_client import QdrantClient
from qdrant_client.http import models

# 1. Configuration & Client Initialization
# In 2026, we use text-embedding-3-small for the best cost/performance ratio
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_SIZE = 1536  # Standard for OpenAI 3-series embeddings

# ✅ Modern Client Initialization
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

q_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "qdrant"), 
    port=6333
)

def process_and_index_document(tenant_id: str, content: str) -> bool:
    """
    Core RAG Pipeline:
    Converts raw text into a searchable vector and stores it with tenant isolation.
    """
    try:
        # Step 1: Generate the Vector Embedding
        # ✅ Updated to use the client.embeddings.create pattern
        response = client.embeddings.create(
            input=content,
            model=EMBEDDING_MODEL
        )
        # ✅ Accessing attribute directly instead of dict indexing
        vector = response.data[0].embedding

        # Step 2: Prepare metadata and ID
        # We use a UUID to ensure every document "chunk" is unique
        point_id = str(uuid.uuid4())

        # Step 3: Upsert to Qdrant
        # The payload ensures that search queries can be filtered by tenant_id
        q_client.upsert(
            collection_name="tenant_knowledge",
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "tenant_id": tenant_id,     # Mandatory for Multi-Tenant Isolation
                        "text_content": content,    # Stored so we can show it in chat results
                        "metadata": {
                            "source": "api_ingest",
                            "processed_at": str(uuid.uuid4()) # Traceability
                        }
                    }
                )
            ]
        )

        print(f"✅ Successfully indexed document for Tenant: {tenant_id}")
        return True

    except Exception as e:
        # In a real production app, you would log this to Azure Monitor/Log Analytics
        print(f"❌ Error processing document for Tenant {tenant_id}: {str(e)}")
        return False

def init_worker_storage():
    """
    Ensures the Qdrant collection exists with the correct dimensions
    before the worker starts processing tasks.
    """
    try:
        collections = q_client.get_collections().collections
        exists = any(c.name == "tenant_knowledge" for c in collections)

        if not exists:
            q_client.create_collection(
                collection_name="tenant_knowledge",
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE, 
                    distance=models.Distance.COSINE
                )
            )
            print("🚀 Created 'tenant_knowledge' collection in Qdrant.")
    except Exception as e:
        print(f"❌ Qdrant Initialization Error: {e}")

# Run initialization if this script is executed directly for testing
if __name__ == "__main__":
    init_worker_storage()