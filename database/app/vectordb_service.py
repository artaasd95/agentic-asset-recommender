from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_openai import OpenAIEmbeddings
import logging
from remote_log_handler import RemoteLogHandler


logger = logging.getLogger("remote_logger")
logger.setLevel(logging.INFO)

remote_handler = RemoteLogHandler("http://localhost:8000/logs")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
remote_handler.setFormatter(formatter)
logger.addHandler(remote_handler)


# Initialize FastAPI app
app = FastAPI()

# Connect to Qdrant and define a collection
client = QdrantClient(":memory:")  # for in-memory DB, or replace with "http://<Qdrant server address>:<port>"
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