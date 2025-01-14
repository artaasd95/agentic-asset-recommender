from fastapi import FastAPI
from datetime import date
import logging

# Local imports
from remote_log_handler import RemoteLogHandler
from models import MainData, FeatureData
from services import (
    store_main_data_logic,
    load_main_data_logic,
    store_feature_data_logic,
    load_feature_data_logic,
    query_feature_data_logic
)

# ----------------------------
# Configure your remote logger
# ----------------------------
logger = logging.getLogger("remote_logger")
logger.setLevel(logging.INFO)

remote_handler = RemoteLogHandler("http://localhost:8000/logs")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
remote_handler.setFormatter(formatter)
logger.addHandler(remote_handler)

# ----------------------------
# Create your FastAPI instance
# ----------------------------
app = FastAPI()


# ----------------------------
# Endpoints
# ----------------------------

@app.post("/store_data")
async def store_data_endpoint(data: MainData):
    """
    Store main data in MongoDB. 
    """
    logger.info("Starting to store main data.")
    try:
        inserted_id = await store_main_data_logic(data)
        logger.info(f"Document stored with ID: {inserted_id}")
        return {"message": "Data stored successfully", "id": inserted_id}
    except Exception as e:
        logger.exception("Exception while storing main data.")
        return {"error": str(e)}

@app.get("/load_data/{ticker}")
async def load_data_endpoint(ticker: str):
    """
    Load all main data documents for a given ticker.
    """
    logger.info(f"Starting to load main data for ticker: {ticker}")
    try:
        docs = await load_main_data_logic(ticker)
        logger.info(f"Data loaded successfully for ticker: {ticker}")
        return docs
    except Exception as e:
        logger.exception("Exception while loading main data.")
        return {"error": str(e)}

@app.post("/store_features")
async def store_features_endpoint(data: FeatureData):
    """
    Store feature data in MongoDB.
    """
    logger.info("Starting to store feature data.")
    try:
        inserted_id = await store_feature_data_logic(data)
        logger.info(f"Feature document stored with ID: {inserted_id}")
        return {"message": "Feature data stored successfully", "id": inserted_id}
    except Exception as e:
        logger.exception("Exception while storing feature data.")
        return {"error": str(e)}

@app.get("/load_features/{ticker}")
async def load_features_endpoint(ticker: str):
    """
    Load all feature data documents for a given ticker.
    """
    logger.info(f"Starting to load features for ticker: {ticker}")
    try:
        docs = await load_feature_data_logic(ticker)
        logger.info(f"Features loaded successfully for ticker: {ticker}")
        return docs
    except Exception as e:
        logger.exception("Exception while loading feature data.")
        return {"error": str(e)}

@app.get("/query_features")
async def query_features_endpoint(name: str, start: date, end: date):
    """
    Query feature data by name, start date, and end date.
    """
    logger.info(f"Starting to query features with name={name}, start={start}, end={end}")
    try:
        docs = await query_feature_data_logic(name, start, end)
        logger.info("Features queried successfully.")
        return docs
    except Exception as e:
        logger.exception("Exception while querying feature data.")
        return {"error": str(e)}
