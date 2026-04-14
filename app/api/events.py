import json
import os
import redis
from datetime import datetime

REDIS_HOST = os.getenv("REDIS_HOST", "redis")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    db=0,
    decode_responses=True
)

STREAM_NAME = "event_stream"

def publish_event(event_type: str, payload: dict):
    """
    Publish event to Redis Stream (production-safe).
    """
    event = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": json.dumps(payload)
    }

    redis_client.xadd(STREAM_NAME, event)