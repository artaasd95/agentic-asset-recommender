from typing import List
from datetime import datetime, date
from pymongo.results import InsertOneResult

from models import MainData, FeatureData
from motor.motor_asyncio import AsyncIOMotorClient

# Create a global, shared Mongo client (no event handlers).
mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
database = mongo_client["mydatabase"]


async def store_main_data_logic(data: MainData) -> str:
    """
    Stores MainData into the 'main_data' collection and returns the inserted ID.
    """
    # Use model_dump() instead of .dict() for Pydantic v2 compatibility.
    doc = data.model_dump()
    result: InsertOneResult = await database["main_data"].insert_one(doc)
    return str(result.inserted_id)


async def load_main_data_logic(ticker: str) -> List[dict]:
    """
    Returns all documents matching a given ticker from 'main_data'.
    """
    cursor = database["main_data"].find({"ticker": ticker})
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        docs.append(doc)
    return docs


async def store_feature_data_logic(data: FeatureData) -> str:
    """
    Stores FeatureData into the 'feature_data' collection and returns the inserted ID.
    """
    doc = data.model_dump()
    result: InsertOneResult = await database["feature_data"].insert_one(doc)
    return str(result.inserted_id)


async def load_feature_data_logic(ticker: str) -> List[dict]:
    """
    Returns all documents matching a given ticker from 'feature_data'.
    """
    cursor = database["feature_data"].find({"ticker": ticker})
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


async def query_feature_data_logic(name: str, start: date, end: date) -> List[dict]:
    """
    Query feature data by name, start date, and end date.
    """
    query = {
        "name": name,
        "start_date": {"$gte": start},
        "end_date": {"$lte": end},
    }
    cursor = database["feature_data"].find(query)
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs
