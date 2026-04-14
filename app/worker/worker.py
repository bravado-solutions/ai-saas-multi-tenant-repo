import os
import json
import redis
import time
import signal
import sys
from tasks import process_and_index_document, init_worker_storage

# --- CONFIGURATION ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

STREAM = "event_stream"
GROUP = "worker-group"
CONSUMER = f"worker-{os.getpid()}"  # ✅ unique consumer per process

r = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    db=0,
    decode_responses=True
)

shutdown_flag = False


# --- 1. GRACEFUL SHUTDOWN ---
def handle_shutdown(signum, frame):
    global shutdown_flag
    print(f"\n🛑 Shutdown signal received by {CONSUMER}...")
    shutdown_flag = True


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


# --- 2. INIT STREAM ---
def init_stream():
    try:
        # mkstream=True creates the stream automatically if it doesn't exist
        r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        print("✅ Consumer group created")
    except redis.exceptions.ResponseError:
        print("ℹ️ Consumer group already exists")


# --- 3. EVENT HANDLER ---
def handle_event(event):
    """
    Routes events to specific task logic.
    Note: Exceptions raised here are caught in the loop/pending logic.
    """
    event_type = event.get("event_type")
    data = json.loads(event.get("data", "{}"))

    if event_type == "document.ingest.requested":
        print(f"📥 Processing ingestion for tenant {data.get('tenant_id')}")
        # Success/Failure determined by process_and_index_document
        process_and_index_document(
            data.get("tenant_id"),
            data.get("content")
        )

    elif event_type == "usage.logged":
        print(f"📊 Usage event received for tenant: {data.get('tenant_id')}")
        # Future: Logic for reporting to Stripe or internal DB

    else:
        print(f"⚠️ Unknown event type: {event_type}")


# --- 4. DEAD LETTER QUEUE (DLQ) ---
def send_to_dlq(event_id, event_data, error):
    """Moves failing events to a separate stream for manual debugging."""
    try:
        r.xadd("dead_letter_stream", {
            "original_event_id": event_id,
            "event_data": json.dumps(event_data),
            "error": str(error),
            "consumer": CONSUMER,
            "timestamp": time.ctime()
        })
        print(f"☠️ Event {event_id} moved to DLQ")
    except Exception as dlq_error:
        print(f"💥 DLQ failure: {dlq_error}")


# --- 5. PROCESS PENDING (RELIABILITY FIX) ---
def process_pending():
    """Checks for messages that were delivered but never acknowledged (e.g., worker crash)."""
    try:
        # Fetch up to 10 messages that are currently in the PEL
        pending = r.xpending_range(STREAM, GROUP, "-", "+", 10)

        for msg in pending:
            event_id = msg["message_id"]
            # Fetch the actual event data for this ID
            messages = r.xrange(STREAM, event_id, event_id)

            for _, event_data in messages:
                try:
                    print(f"♻️ Retrying pending event {event_id}")
                    handle_event(event_data)
                    # Successful retry
                    r.xack(STREAM, GROUP, event_id)
                except Exception as e:
                    print(f"❌ Pending retry failed for {event_id}: {e}")
                    send_to_dlq(event_id, event_data, e)
                    # Acknowledge in main stream to remove from PEL after DLQ move
                    r.xack(STREAM, GROUP, event_id)

    except Exception as e:
        print(f"⚠️ Pending processing error: {e}")


# --- 6. MAIN WORKER LOOP ---
def start_worker():
    print("🚀 Initializing worker storage and streams...")

    # Ensure Qdrant collection and Redis group are ready
    init_worker_storage()
    init_stream()

    print(f"👂 Worker {CONSUMER} listening to {STREAM}...")

    while not shutdown_flag:
        try:
            # 1. Recover any abandoned tasks from the PEL
            process_pending()

            # 2. Block and wait for NEW messages
            # count=10 allows batch processing for efficiency
            # block=5000 means wait 5 seconds before checking shutdown_flag
            messages = r.xreadgroup(
                GROUP,
                CONSUMER,
                {STREAM: ">"},
                count=10,
                block=5000
            )

            if not messages:
                continue

            for stream, events in messages:
                for event_id, event_data in events:
                    try:
                        # Process the task
                        handle_event(event_data)

                        # ✅ Success: Acknowledge to clear from PEL
                        r.xack(STREAM, GROUP, event_id)
                        print(f"✨ Event {event_id} processed successfully")

                    except Exception as e:
                        print(f"❌ Failed processing event {event_id}: {e}")

                        # ✅ Failure: Log to DLQ and clear from main stream
                        send_to_dlq(event_id, event_data, e)
                        r.xack(STREAM, GROUP, event_id)

        except Exception as e:
            if not shutdown_flag:
                print(f"💥 Main worker loop error: {str(e)}")
                # Short sleep to prevent CPU spiking if Redis is down
                time.sleep(5)

    print("✅ Worker shutdown complete")


# --- 7. ENTRYPOINT ---
if __name__ == "__main__":
    start_worker()