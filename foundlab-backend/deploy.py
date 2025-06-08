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
    load_dotenv()

    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    gcp_region = os.getenv("GCP_REGION")
    cloud_run_service_name = os.getenv("CLOUD_RUN_SERVICE_NAME")

    secret_key = os.getenv("SECRET_KEY")
    mongo_db_url = os.getenv("MONGO_DB_URL")
    mongo_db_name = os.getenv("MONGO_DB_NAME")
    app_name = os.getenv("APP_NAME", "FoundLab Backend")
    app_version = os.getenv("APP_VERSION", "0.1.0")

    if not all([gcp_project_id, gcp_region, cloud_run_service_name, secret_key, mongo_db_url, mongo_db_name]):
        print("Error: Required GCP/MongoDB/Secret environment variables are not set in .env.")
        print("Please ensure GCP_PROJECT_ID, GCP_REGION, CLOUD_RUN_SERVICE_NAME, SECRET_KEY, MONGO_DB_URL, MONGO_DB_NAME are configured.")
        print("IMPORTANT: For MONGO_DB_URL, use a MongoDB Atlas connection string (e.g., 'mongodb+srv://...').")
        exit(1)

    print(f"--- Deploying FoundLab Backend to Google Cloud Run ---")
    print(f"  Project: {gcp_project_id}, Region: {gcp_region}, Service: {cloud_run_service_name}")

    run_command(["gcloud", "auth", "configure-docker", gcp_region + "-docker.pkg.dev"])

    artifact_registry_repo = "foundlab-repo"
    image_tag = f"{gcp_region}-docker.pkg.dev/{gcp_project_id}/{artifact_registry_repo}/{cloud_run_service_name}:latest"
    print(f"Building Docker image: {image_tag}")
    run_command(["docker", "build", "-t", image_tag, "."])

    print("Pushing Docker image to Artifact Registry...")
    run_command(["docker", "push", image_tag])

    env_vars = (
        f"SECRET_KEY='{secret_key}',"
        f"MONGO_DB_URL='{mongo_db_url}',"
        f"MONGO_DB_NAME='{mongo_db_name}',"
        f"APP_NAME='{app_name}',"
        f"APP_VERSION='{app_version}',"
        f"ENVIRONMENT=production,DEBUG=False"
    )

    deploy_command_parts = [
        "gcloud", "run", "deploy", cloud_run_service_name,
        "--image", image_tag,
        "--region", gcp_region,
        "--project", gcp_project_id,
        "--allow-unauthenticated",
        "--set-env-vars", env_vars,
        "--platform", "managed",
        "--port", "8000",
        "--min-instances", "0",
        "--max-instances", "1",
        "--cpu", "1",
        "--memory", "512Mi",
        "--timeout", "300s"
    ]
    print("--- Deploying service to Cloud Run ---")
    deploy_output = run_command(deploy_command_parts)

    service_url_line = [line for line in deploy_output.splitlines() if "Service URL:" in line]
    service_url = None
    if service_url_line:
        service_url = service_url_line[0].split("Service URL:")[1].strip()
        print(f"Deployment successful! 🚀")
        print(f"Your FoundLab Backend is available at: {service_url}")
        print(f"Swagger UI: {service_url}/docs")
        print(f"ReDoc: {service_url}/redoc")

        with open(".env", "r") as f:
            lines = f.readlines()
        with open(".env", "w") as f:
            for line in lines:
                if not line.strip().startswith("API_URL="):
                    f.write(line)
            f.write(f'API_URL="{service_url}"\n')
        print(f"Updated local .env file with API_URL={service_url} for next steps (init/Postman).")
        print("Please import the 'foundlab_collection.json' into Postman and ensure 'baseUrl' variable is set to this URL.")
    else:
        print("Could not retrieve service URL from deploy output.")
        print("Please check the Cloud Run console for the service URL.")

    print("--- Deployment process finished ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
