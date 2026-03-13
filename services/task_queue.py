"""Queue boundary for future async extraction workers."""


def enqueue_extraction(payload):
    """Placeholder queue API.

    Later replace this with Celery/RQ/Kafka enqueue logic.
    """
    return {"queued": False, "mode": "sync", "payload": payload}
