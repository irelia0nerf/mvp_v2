#!/usr/bin/env python3
import asyncio
import os
import httpx
from dotenv import load_dotenv

async def main():
    load_dotenv()
    BASE_URL = os.getenv("API_URL", "http://localhost:8000")

    print(f"--- FoundLab Backend Data Initialization ---")
    print(f"Attempting to initialize data using API at: {BASE_URL}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("Checking API health...")
        try:
            health_response = await client.get("/health")
            health_response.raise_for_status()
            print(f"API is healthy: {health_response.json()['status']}")
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"ERROR: Could not connect to the API at {BASE_URL}.")
            print(f"Details: {e}")
            if "localhost" in BASE_URL:
                print("If running locally, use 'make run_docker' or 'make run' first.")
            else:
                print("If deploying to Cloud Run, ensure the service is up and accessible.")
            return

        print("--- Initializing Default DFC Flags ---")
        default_flags = [
            {
                "name": "is_foundlab_member",
                "description": "Flag to identify if an entity is a FoundLab member (active for demo purposes).",
                "type": "boolean",
                "default_value": False,
                "rules": [{"field": "is_foundlab_registered", "condition": "eq", "value": True}],
                "weight": 0.5,
                "category": "membership"
            },
            {
                "name": "high_risk_country",
                "description": "Flag if entity's country is in a high-risk jurisdiction for compliance.",
                "type": "boolean",
                "default_value": False,
                "rules": [{"field": "country_iso", "condition": "in", "value": ["SY", "IR", "KP", "CU"]}],
                "weight": 0.9,
                "category": "compliance"
            },
            {
                "name": "large_transaction_volume",
                "description": "Flag if entity has processed high transaction volume recently (USD).",
                "type": "numeric",
                "default_value": 0.0,
                "rules": [{"field": "recent_transaction_volume_usd", "condition": "gte", "value": 50000.0}],
                "weight": 0.7,
                "category": "financial"
            },
            {
                "name": "suspect_behavior_pattern",
                "description": "Flag for observed suspect behavior on platform.",
                "type": "boolean",
                "default_value": False,
                "rules": [{"field": "behavior_score", "condition": "gte", "value": 0.8}],
                "weight": 0.8,
                "category": "fraud_detection"
            }
        ]

        for flag_data in default_flags:
            try:
                response = await client.post("/flags/definitions", json=flag_data)
                response.raise_for_status()
                print(f"  Flag '{flag_data['name']}' created successfully (or already exists).")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 409:
                    print(f"  Flag '{flag_data['name']}' already exists, skipping creation.")
                else:
                    print(f"  Failed to create flag '{flag_data['name']}': {e.response.text}")
            except httpx.RequestError as e:
                print(f"  Network error creating flag '{flag_data['name']}': {e}")

        print("--- Initializing Default Risk Triggers ---")
        default_triggers = [
            {
                "name": "critical_low_score_alert",
                "description": "Triggers if P(x) score falls below 0.2, indicating critical reputational risk.",
                "trigger_type": "score_threshold",
                "score_threshold": 0.2,
                "risk_level": "CRITICAL",
                "is_active": True
            },
            {
                "name": "high_risk_country_trigger",
                "description": "Triggers if entity is flagged for high-risk country association.",
                "trigger_type": "flag_presence",
                "flag_name": "high_risk_country",
                "risk_level": "HIGH",
                "is_active": True
            },
            {
                "name": "fraud_suspect_behavior",
                "description": "Triggers if suspect behavior pattern flag is active.",
                "trigger_type": "flag_presence",
                "flag_name": "suspect_behavior_pattern",
                "risk_level": "HIGH",
                "is_active": True
            },
            {
                "name": "unusual_activity_and_low_score",
                "description": "Custom logic: combines low overall score with significant transaction volume.",
                "trigger_type": "custom_logic",
                "custom_logic_params": {"max_score": 0.4, "min_recent_volume": 75000.0},
                "risk_level": "MEDIUM",
                "is_active": True
            }
        ]

        for trigger_data in default_triggers:
            try:
                response = await client.post("/sentinela/triggers", json=trigger_data)
                response.raise_for_status()
                print(f"  Trigger '{trigger_data['name']}' created successfully (or already exists).")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 409:
                    print(f"  Trigger '{trigger_data['name']}' already exists, skipping creation.")
                else:
                    print(f"  Failed to create trigger '{trigger_data['name']}': {e.response.text}")
            except httpx.RequestError as e:
                print(f"  Network error creating trigger '{trigger_data['name']}': {e}")

    print("--- FoundLab Backend Data Initialization COMPLETE ---")
    print("Remember to configure your MongoDB connection string in .env.")
    print("If deploying to Cloud Run, ensure your GCP Service Account has sufficient permissions.")

if __name__ == "__main__":
    asyncio.run(main())
