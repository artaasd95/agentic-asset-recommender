# server/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import time

# Elasticsearch / OpenSearch client
from elasticsearch import Elasticsearch

app = FastAPI()

# Initialize the Elasticsearch client
# Adjust host/port/credentials to match your environment
es = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=("elastic", "changeme"),  # or omit if security is disabled
    verify_certs=False
)

# Define a Pydantic model for incoming log records
class LogRecord(BaseModel):
    loggerName: str
    logLevel: str
    message: str
    filename: str
    lineNo: int
    created: float  # Unix timestamp
    extra: Optional[dict] = None  # In case you have extra fields


@app.post("/logs")
async def receive_logs(log_record: LogRecord):
    """
    Receive logs via POST request and store them in Elasticsearch.
    """
    # Prepare the document for indexing in Elasticsearch
    doc = {
        "loggerName": log_record.loggerName,
        "logLevel": log_record.logLevel,
        "message": log_record.message,
        "filename": log_record.filename,
        "lineNo": log_record.lineNo,
        "created": log_record.created,
        "timestamp_indexed": time.time(),  # time the log was indexed
        "extra": log_record.extra or {},
    }

    # Index the document into Elasticsearch
    # You can name the index e.g. "python-logs"
    try:
        response = es.index(index="python-logs", document=doc)
        return {"status": "success", "es_response": response}
    except Exception as e:
        return {"status": "error", "details": str(e)}
