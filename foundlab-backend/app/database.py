from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

from pymongo import ASCENDING, DESCENDING # Importe ASCENDING e DESCENDING
from app.config import settings

client: AsyncIOMotorClient = None  # type: ignore


async def connect_to_mongo():
    """Establishes connection to MongoDB and ensures necessary indexes are created."""
    global client
    try:
        client = AsyncIOMotorClient(settings.MONGO_DB_URL)
        await client.admin.command('ping')
        print(f"Connected to MongoDB at {settings.MONGO_DB_URL}")

        # Ensure index on 'entity_id' for scores collection
        scores_collection = get_collection("scores") # Use get_collection para obter a instância da coleção
        await scores_collection.create_index([("entity_id", ASCENDING)])
        print("Ensured index on 'entity_id' for 'scores' collection.")

        # Ensure index on 'name' for flags collection
        flags_collection = get_collection("flags")
        await flags_collection.create_index([("name", ASCENDING)], unique=True)
        print("Ensured index on 'name' for 'flags' collection.")

        # Ensure index on 'entity_id' for sherlock_results collection
        sherlock_results_collection = get_collection("sherlock_results")
        await sherlock_results_collection.create_index([("entity_id", ASCENDING)])
        print("Ensured index on 'entity_id' for 'sherlock_results' collection.")

        # Ensure index on 'name' for risk_triggers collection
        risk_triggers_collection = get_collection("risk_triggers")
        await risk_triggers_collection.create_index([("name", ASCENDING)], unique=True) # Assuming trigger names are unique
        print("Ensured index on 'name' for 'risk_triggers' collection.")

        # Ensure compound index on 'entity_id' and 'created_at' for risk_assessments collection
        risk_assessments_collection = get_collection("risk_assessments")
        await risk_assessments_collection.create_index([("entity_id", ASCENDING), ("created_at", DESCENDING)])
        print("Ensured compound index on 'entity_id' and 'created_at' for 'risk_assessments' collection.")

 # Ensure compound index on 'entity_id' and 'timestamp' for gas_records collection
 gas_records_collection = get_collection("gas_records")
 await gas_records_collection.create_index([("entity_id", ASCENDING), ("timestamp", DESCENDING)])
 print("Ensured compound index on 'entity_id' and 'timestamp' for 'gas_records' collection.")
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
        raise
    except Exception as e:
        print(f"An error occurred during MongoDB connection or index creation: {e}")
        raise


async def close_mongo_connection():
    """Closes the MongoDB connection."""
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")


def get_collection(collection_name: str):
    """
    Returns a MongoDB collection instance.

    Args:
        collection_name (str): The name of the collection to retrieve.
    """
    if client is None:
        raise ConnectionFailure("MongoDB client is not initialized. Call connect_to_mongo() first.")
    # Use settings.MONGO_DB_NAME para acessar o nome do banco de dados
    return client[settings.MONGO_DB_NAME][collection_name]
