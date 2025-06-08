from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

from app.config import settings

client: AsyncIOMotorClient = None  # type: ignore


async def connect_to_mongo():
    """Establishes connection to MongoDB."""
    global client
    try:
        client = AsyncIOMotorClient(settings.MONGO_DB_URL)
        await client.admin.command('ping')
        print(f"Connected to MongoDB at {settings.MONGO_DB_URL}")
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
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
    return client[settings.MONGO_DB_NAME][collection_name]
