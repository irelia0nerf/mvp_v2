import time
import uuid
import hashlib
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send
import logging

logger = logging.getLogger("request-context")

class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, body_max_len: int = 5000):
        super().__init__(app)
        self.body_max_len = body_max_len

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # IDs institucionais
        decision_id = str(uuid.uuid4())
        # Capture request_id from scope (ASGI server might provide it), fallback to UUID if not
        request_id = request.scope.get("x-request-id", str(uuid.uuid4()))

        # Capture body (truncated)
        # Need to consume body here before call_next if logging it
        try:
            body = await request.body()
            truncated_body = body[:self.body_max_len].decode("utf-8", errors="replace")
            body_truncated = len(body) > self.body_max_len
            body_size = len(body)
        except Exception as e:
            truncated_body = "<unreadable>"
            body_truncated = True
            body_size = 0
            logger.error(f"Failed to read request body: {e}", extra={"request_id": request_id, "decision_id": decision_id})


        # Re-inject body into request. It's usually not needed if you only read it once,
        # but if any downstream middleware/endpoint needs the body again, you'd handle it here.
        # For simple body logging like this, reading it once is fine and usually doesn't
        # require re-injecting unless other parts of the app rely on request.body().
        # If you need to re-inject: https://github.com/encode/starlette/issues/1310
        # For this use case (logging), just consuming the body once here is simpler.


        response = Response(status_code=500) # Default in case of unhandled errors

        try:
            response = await call_next(request)
        except Exception as e:
            # Log unexpected exceptions before re-raising
            logger.error(f"Unhandled exception during request processing: {e}", exc_info=True, extra={
                "decision_id": decision_id,
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500, # Assume 500 for unhandled exceptions
                "event": "request.exception" # Custom event type
            })
            # Set status code on response for logging purposes if not already set by exception handler
            if response.status_code == 500:
                 response.status_code = 500 # Ensure 500 is captured if no specific handler set it
            raise # Re-raise the exception


        latency_ms = int((time.time() - start_time) * 1000)

        # Scores reputacionais (injected into request.state by the application logic)
        # Use getattr with a default to avoid errors if the attribute is not set
        use_case = getattr(request.state, "use_case", "undefined")
        entity_id = getattr(request.state, "entity_id", "unknown") # Assuming entity_id is stored in state
        score_before = getattr(request.state, "score_before", None)
        score_after = getattr(request.state, "score_after", None)
        flags_triggered = getattr(request.state, "flags_triggered", []) # Assuming stored as list

        # Construct the log event dictionary with the fixed reputational schema
        log_event = {
            "decision_id": decision_id,
            "request_id": request_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "latency_ms": latency_ms,

            "use_case": use_case,
            "entity_id": entity_id,
            "action": f"{request.method} {request.url.path}",

            "score_before": score_before,
            "score_after": score_after,
            "flags_triggered": flags_triggered,

            "status_code": response.status_code,
            "body_truncated": body_truncated,
            "body_size": body_size,

            "actor_ip": request.client.host if request.client else None,
            "actor_agent": request.headers.get("user-agent", "unknown"),
        }

        # Calculate Veritas signature (SHA256 hash of the sorted JSON log event)
        try:
            # Ensure consistent order for hashing
            log_event_sorted_json = json.dumps(log_event, sort_keys=True, ensure_ascii=False).encode("utf-8")
            log_event["veritas_signature"] = hashlib.sha256(log_event_sorted_json).hexdigest()
        except Exception as e:
             logger.error(f"Failed to calculate veritas_signature: {e}", extra={"request_id": request_id, "decision_id": decision_id})
             log_event["veritas_signature"] = "error_calculating_hash"


        # Output the JSON log event (to stdout for now)
        # In a real scenario, this would go to Kafka, Pub/Sub, etc.
        print(json.dumps(log_event, ensure_ascii=False))


        return response
