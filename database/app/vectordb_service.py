from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_openai import OpenAIEmbeddings

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
    try:
        # Store vector in the Qdrant database
        vector_store.store(documents=[{'id': doc.id, 'text': doc.text}])
        return {"message": "Document stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store document: {str(e)}")

@app.get("/load/{doc_id}")
async def load_vector(doc_id: str):
    try:
        # Load vector data by document ID
        document = vector_store.load({'id': doc_id})
        if document:
            return {"document": document}
        else:
            return {"message": "Document not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load document: {str(e)}")

# Run the FastAPI application