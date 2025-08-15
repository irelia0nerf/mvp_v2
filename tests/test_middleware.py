import pytest
import httpx
import logging
import json
import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

# Import the middleware and context variables
from app.middleware.request_context_middleware import (
    RequestContextMiddleware,
    request_id_context,
    decision_id_context,
    use_case_context,
    REQUESTS_PROCESSED_COUNT # Import the counter for potential future tests
)

# Configure logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a test router with endpoints to check context and generate specific logs
test_router = APIRouter()

@test_router.get("/test-context")
async def test_context():
    # Access context variables within the endpoint
    req_id = request_id_context.get()
    dec_id = decision_id_context.get()
    uc = use_case_context.get()
    logger.info("Inside test_context endpoint", extra={"req_id": req_id, "dec_id": dec_id, "use_case": uc})
    return JSONResponse({
        "request_id_from_context": req_id,
        "decision_id_from_context": dec_id,
        "use_case_from_context": uc,
    })

@test_router.post("/test-decision")
async def test_decision():
    # Simulate setting a DecisionID and UseCase in the service layer
    test_decision_id = str(uuid.uuid4())
    test_use_case = "test_decision_use_case"
    decision_id_token = decision_id_context.set(test_decision_id)
    use_case_token = use_case_context.set(test_use_case)

    # Simulate setting data in request.state (requires middleware to pass request)
    # Note: The current middleware __call__ structure might make direct request.state access tricky
    # without passing the request object down, but contextvars work independently.
    # We'll focus on contextvars and log structure for now.

    logger.info("Inside test_decision endpoint, setting contextvars", extra={"dec_id_set": test_decision_id, "uc_set": test_use_case})

    # Reset contextvars - important!
    decision_id_context.reset(decision_id_token)
    use_case_context.reset(use_case_token)

    return JSONResponse({"status": "ok"})


# Define a test FastAPI app with the middleware
test_app = FastAPI()
test_app.add_middleware(RequestContextMiddleware)
test_app.include_router(test_router)

# Helper to parse JSON logs
def parse_log_message(log_entry: str) -> dict:
    # Assuming logs are single-line JSON objects
    try:
        return json.loads(log_entry)
    except json.JSONDecodeError:
        pytest.fail(f"Log entry is not valid JSON: {log_entry}")

# --- Test Cases ---

@pytest.mark.asyncio
async def test_middleware_adds_request_id_header():
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get("/test-context")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    # DecisionID should not be present by default if not set
    assert "x-decision-id" not in response.headers

@pytest.mark.asyncio
async def test_middleware_preserves_provided_request_id_header():
    provided_request_id = str(uuid.uuid4())
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get("/test-context", headers={"X-Request-ID": provided_request_id})

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"] == provided_request_id

@pytest.mark.asyncio
async def test_context_vars_are_accessible_in_endpoint(caplog):
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get("/test-context")

    assert response.status_code == 200
    response_data = response.json()

    # Check context vars from response data
    assert "request_id_from_context" in response_data
    assert "decision_id_from_context" in response_data # Should be default '-'
    assert "use_case_from_context" in response_data # Should be default 'unknown'

    req_id_from_resp = response_data["request_id_from_context"]
    dec_id_from_resp = response_data["decision_id_from_context"]
    uc_from_resp = response_data["use_case_from_context"]

    # Check if the request_id in response matches the header
    assert req_id_from_resp == response.headers["x-request-id"]
    assert dec_id_from_resp == "-"
    assert uc_from_resp == "unknown"

    # Check logs for context vars (assuming default logging format initially, will refine for JSON)
    # This test is more conceptual until JSON formatter is fully integrated and tested
    # For now, check if log message contains expected patterns
    log_messages = [rec.getMessage() for rec in caplog.records]
    # Find the log from inside the endpoint
    endpoint_log = next((msg for msg in log_messages if "Inside test_context endpoint" in msg), None)
    assert endpoint_log is not None
    # More specific log content checks require JSON formatter setup for tests

@pytest.mark.asyncio
async def test_middleware_generates_structured_logs(caplog):
    caplog.set_level(logging.INFO) # Ensure INFO logs are captured

    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get("/test-context")

    assert response.status_code == 200

    # Filter logs generated by the middleware (look for "request.start" and "request.end")
    middleware_logs = [rec for rec in caplog.records if "request.start" in rec.message or "request.end" in rec.message]

    assert len(middleware_logs) >= 2 # Expect at least start and end logs

    start_log = next((rec for rec in middleware_logs if "request.start" in rec.message), None)
    end_log = next((rec for rec in middleware_logs if "request.end" in rec.message), None)

    assert start_log is not None
    assert end_log is not None

    # Assuming the JsonFormatter from logging_config is applied for tests
    # This part needs the JsonFormatter to be used by the logger
    # We'll manually parse the message for this test for now, assuming the format is like the print in middleware
    # For a real test, configure logging with the JsonFormatter before running tests

    # Manual parsing based on the print(json.dumps(log_event)) from the middleware code
    # This is a temporary approach until JsonFormatter is integrated with test logger
    start_log_data = parse_log_message(start_log.message) # The print is the message here
    end_log_data = parse_log_message(end_log.message) # The print is the message here

    # Validate start log schema and content
    assert start_log_data["event"] == "request.start"
    assert "decision_id" in start_log_data
    assert "request_id" in start_log_data
    assert "method" in start_log_data
    assert "path" in start_log_data
    assert "client" in start_log_data
    assert "body_truncated" in start_log_data
    assert "body_size" in start_log_data
    assert "truncated_body" in start_log_data

    # Validate end log schema and content
    assert end_log_data["event"] == "request.end"
    assert "decision_id" in end_log_data
    assert "request_id" in end_log_data
    assert "timestamp" in end_log_data
    assert "latency_ms" in end_log_data
    assert "use_case" in end_log_data
    assert "entity_id" in end_log_data
    assert "action" in end_log_data
    assert "score_before" in end_log_data
    assert "score_after" in end_log_data
    assert "flags_triggered" in end_log_data
    assert "status_code" in end_log_data
    assert "body_truncated" in end_log_data
    assert "body_size" in end_log_data
    assert "actor_ip" in end_log_data
    assert "actor_agent" in end_log_data

    # Check correlation IDs match between start and end logs for the same request
    assert start_log_data["request_id"] == end_log_data["request_id"]
    assert start_log_data["decision_id"] == end_log_data["decision_id"]

    # Check RequestID in logs matches header
    assert end_log_data["request_id"] == response.headers["x-request-id"]

    # Check default DecisionID and UseCase in logs
    assert end_log_data["decision_id"] is not None # Should be generated
    assert end_log_data["use_case"] == "undefined" # Default if not set

@pytest.mark.asyncio
async def test_middleware_captures_set_context_vars_in_logs(caplog):
    caplog.set_level(logging.INFO)

    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post("/test-decision") # Call endpoint that sets context

    assert response.status_code == 200

    # Filter logs generated by the middleware
    middleware_logs = [rec for rec in caplog.records if "request.start" in rec.message or "request.end" in rec.message]

    assert len(middleware_logs) >= 2

    end_log = next((rec for rec in middleware_logs if "request.end" in rec.message), None)
    assert end_log is not None

    end_log_data = parse_log_message(end_log.message)

    # Check if DecisionID and UseCase from contextvars were captured in the end log
    # The test endpoint sets them directly in contextvars, so middleware should see them
    # Note: This requires the middleware to access contextvars OR state AFTER call_next
    # The current middleware code attempts to get from request.state AFTER call_next.
    # The test_decision endpoint sets contextvars, NOT state.
    # We need to reconcile how use_case/decision_id are propagated.
    # If middleware generates DecisionID and service sets use_case/entity_id in state,
    # then middleware should capture use_case/entity_id from state.
    # DecisionID propagation needs refinement.

    # Let's test the DecisionID generated by the middleware and the default UseCase/EntityID first
    assert end_log_data["decision_id"] is not None # Middleware generates this
    assert end_log_data["use_case"] == "undefined" # Default
    assert end_log_data["entity_id"] == "unknown" # Default

    # To test contextvar propagation from endpoint/service, we'd need to adjust
    # how middleware reads them OR how the endpoint/service injects them (state vs contextvar).
    # The middleware currently tries to read use_case/entity_id from state.
    # The test_decision endpoint sets contextvars. This is a mismatch.

    # Let's adjust the test_decision endpoint to also set state to match the middleware expectation
    @test_router.post("/test-decision-with-state")
    async def test_decision_with_state(request: Request): # Need Request object to set state
         test_decision_id = str(uuid.uuid4())
         test_use_case = "test_state_use_case"
         test_entity_id = "test_entity_123"
         test_score_before = 0.5
         test_score_after = 0.7
         test_flags = ["FLAG_A", "FLAG_B"]

         # Set contextvars (for potential logging within endpoint/service)
         decision_id_token = decision_id_context.set(test_decision_id)
         use_case_token = use_case_context.set(test_use_case)

         # Set request.state (for middleware to capture in end log)
         request.state.use_case = test_use_case
         request.state.entity_id = test_entity_id
         request.state.score_before = test_score_before
         request.state.score_after = test_score_after
         request.state.flags_triggered = test_flags

         logger.info("Inside test_decision_with_state endpoint, setting state")

         # Reset contextvars
         decision_id_context.reset(decision_id_token)
         use_case_context.reset(use_case_token)

         return JSONResponse({"status": "ok"})

    # Now test the endpoint that sets state
    caplog.clear() # Clear previous logs
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post("/test-decision-with-state")

    assert response.status_code == 200

    middleware_logs_state = [rec for rec in caplog.records if "request.start" in rec.message or "request.end" in rec.message]
    assert len(middleware_logs_state) >= 2
    end_log_state = next((rec for rec in middleware_logs_state if "request.end" in rec.message), None)
    assert end_log_state is not None

    end_log_state_data = parse_log_message(end_log_state.message)

    # Validate that state data was captured in the end log
    assert end_log_state_data["use_case"] == "test_state_use_case"
    assert end_log_state_data["entity_id"] == "test_entity_123"
    assert end_log_state_data["score_before"] == 0.5
    assert end_log_state_data["score_after"] == 0.7
    assert end_log_state_data["flags_triggered"] == ["FLAG_A", "FLAG_B"]


# TODO: Add tests for PII masking in logs (requires JsonFormatter integration)
# TODO: Add tests for Veritas signature calculation (requires JsonFormatter/middleware print output check)
# TODO: Add tests for body truncation
# TODO: Add tests for middleware heartbeat check (requires health endpoint and middleware counter)