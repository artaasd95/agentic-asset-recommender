# main.py

from typing import List, Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel
from datetime import datetime
from pymongo import MongoClient

app = FastAPI()

# ---- Configure your MongoDB connection here ----
# Point to your Mongo container or local Mongo instance
MONGO_URL = "mongodb://mongodb:27017"  # or "mongodb://mongo:27017" if using docker-compose
client = MongoClient(MONGO_URL)
db = client["logs_db"]
logs_collection = db["logs"]


class LogEntry(BaseModel):
    loggerName: str
    logLevel: str
    message: str
    filename: str
    lineNo: int
    created: float


@app.post("/logs")
def create_log(entry: LogEntry):
    """
    Store the log entry in the MongoDB collection.
    """
    # Convert to dictionary
    entry_dict = entry.dict()
    # Insert into MongoDB
    logs_collection.insert_one(entry_dict)
    return {"message": "Log entry stored successfully"}


@app.get("/logs")
def get_logs(
    level: Optional[str] = Query(None, description="Optional log level filter (e.g. INFO, ERROR)"),
    limit: int = Query(50, description="Limit the number of returned logs"),
    skip: int = Query(0, description="Number of logs to skip for pagination"),
):
    """
    Retrieve logs from MongoDB.
    Optional query params:
      - level: filter logs by level
      - limit: limit the number of logs returned
      - skip: skip logs for pagination
    """
    query = {}
    if level:
        query["logLevel"] = level

    # Retrieve logs from DB
    cursor = logs_collection.find(query).skip(skip).limit(limit)
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])  # convert ObjectId to string for JSON serialization
        results.append(doc)

    return {"count": len(results), "logs": results}


@app.delete("/logs")
def delete_logs():
    """
    Danger zone:
    Deletes all logs from the database.
    """
    logs_collection.delete_many({})
    return {"message": "All logs have been deleted."}
