import os
from fastapi import FastAPI, HTTPException
from datetime import date
import logging
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel
from dotenv import load_dotenv
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
load_dotenv()
# ----------------------------
# Configure your remote logger
# ----------------------------
LOG_URL = os.getenv("LOG_URL")
logger = logging.getLogger("remote_logger")
logger.setLevel(logging.INFO)

remote_handler = RemoteLogHandler(LOG_URL)
formatter = logging.Formatter('Data Service log: - %(asctime)s - %(name)s - %(levelname)s - %(message)s')
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


# ---------------------------------------------------------------------------------
# Vector DB services
# ---------------------------------------------------------------------------------


# Connect to Qdrant and define a collection
QDRANT_URI = os.getenv("QDRANT_URI", ":memory:")
client = QdrantClient(QDRANT_URI)  # for in-memory DB, or replace with "http://<Qdrant server address>:<port>"

collection_name = "demo_collection"
client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# Initialize Vector Store with Langchain
vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=OpenAIEmbeddings(),
)

# Pydantic model for storing data
class Document(BaseModel):
    id: str
    text: str

@app.post("/store")
async def store_vector(doc: Document):
    logger.info(f"Starting to store document with ID: {doc.id}")
    try:
        # Store vector in the Qdrant database
        logger.info(f"Storing document with ID: {doc.id}")
        vector_store.store(documents=[{'id': doc.id, 'text': doc.text}])
        logger.info(f"Document with ID: {doc.id} stored successfully")
        return {"message": "Document stored successfully"}
    except Exception as e:
        logger.error(f"Failed to store document with ID: {doc.id}. Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store document: {str(e)}")

@app.get("/load/{doc_id}")
async def load_vector(doc_id: str):
    logger.info(f"Starting to load document with ID: {doc_id}")
    try:
        # Load vector data by document ID
        logger.info(f"Loading document with ID: {doc_id}")
        document = vector_store.load({'id': doc_id})
        if document:
            logger.info(f"Document with ID: {doc_id} loaded successfully")
            return {"document": document}
        else:
            logger.warning(f"Document with ID: {doc_id} not found")
            return {"message": "Document not found"}
    except Exception as e:
        logger.error(f"Failed to load document with ID: {doc_id}. Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load document: {str(e)}")