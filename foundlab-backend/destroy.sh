#!/usr/bin/env python3
import os
import subprocess
from dotenv import load_dotenv

def run_command(command_parts: list, check: bool = True, capture_output: bool = True):
    command_str = " ".join(command_parts)
    print(f"Executing: {command_str}")
    try:
        process = subprocess.run(command_parts, check=check, capture_output=capture_output, text=True)
        if process.stdout:
            print(f"STDOUT:\n{process.stdout}")
        if process.stderr:
            print(f"STDERR:\n{process.stderr}")
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed: {e.cmd}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        raise

async def main():
    load_dotenv()  # Carrega variáveis de ambiente

    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    gcp_region = os.getenv("GCP_REGION")
    cloud_run_service_name = os.getenv("CLOUD_RUN_SERVICE_NAME")

    if not all([gcp_project_id, gcp_region, cloud_run_service_name]):
        print("Error: GCP project ID, region, and Cloud Run service name must be set in .env.")
        exit(1)

    print(f"--- Destroying FoundLab Backend service '{cloud_run_service_name}' in Google Cloud Run ---")
    print(f"  Project: {gcp_project_id}, Region: {gcp_region}")

    destroy_command_parts = [
        "gcloud", "run", "services", "delete", cloud_run_service_name,
        "--region", gcp_region,
        "--project", gcp_project_id,
        "--quiet"  # Do not prompt for confirmation
    ]

    try:
        run_command(destroy_command_parts)
        print(f"Service '{cloud_run_service_name}' successfully deleted.")
    except Exception as e:
        print(f"Failed to delete service '{cloud_run_service_name}'. It might not exist or you lack sufficient permissions.")
        print(f"Details: {e}")

    print("--- Destruction process finished ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
