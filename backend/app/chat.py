import os
import re
import uuid
import logging
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from phi.agent import Agent, AgentMemory
from phi.model.openai import OpenAIChat
from phi.memory.db.postgres import PgMemoryDb
from phi.storage.agent.postgres import PgAgentStorage

# Load environment variables
load_dotenv()

# Retrieve variables from .env
MODEL = os.getenv("MODEL", 'gpt-4o-mini')
DB_URL = os.getenv("DB_URL")
LOG_URL = os.getenv("LOG_URL")

# Configure remote logger
logger = logging.getLogger("remote_logger")
logger.setLevel(logging.INFO)

log_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)

# Optional: Integrate remote logging URL if required
if LOG_URL:
    try:
        from logging.handlers import HTTPHandler
        remote_handler = HTTPHandler(
            host=LOG_URL,
            url="/",
            method="POST"
        )
        remote_handler.setLevel(logging.ERROR)
        logger.addHandler(remote_handler)
        logger.info("Remote logger configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure remote logger: {str(e)}")

# FastAPI application initialization
app = FastAPI()

# Define the request body
class QueryItem(BaseModel):
    query: str
    user_id: str
    session_id: str
    asset_ticker: str

# Create a single agent instance
agent = Agent(
    name="Financial asset recommender",
    model=OpenAIChat(id=MODEL),
    tools=[],
    memory=AgentMemory(
        db=PgMemoryDb(table_name="fin_agent_memory", db_url=DB_URL),
        create_user_memories=True,
        create_session_summary=True
    ),
    storage=PgAgentStorage(
        table_name="global_user_sessions",
        db_url=DB_URL
    ),
    session_id=str(uuid.uuid4()),
    user_id="global_agent",
    markdown=False,
    show_tool_calls=True,
    read_chat_history=True,
    add_history_to_messages=True,
    num_history_responses=3,
    debug_mode=False,
    prevent_prompt_leakage=True
)

@app.post("/v1/query")
async def query_agent(request: QueryItem):
    logger.info(f"Query received: {request.query}")
    try:
        # Update agent with new user ID and session ID
        agent.user_id = request.user_id or str(uuid.uuid4())
        agent.session_id = request.session_id or str(uuid.uuid4())

        # Add logic to process the query using the agent
        response = {}  # Placeholder for agent response logic
        logger.info("Query processed successfully.")
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error initiating query: {str(e)}")
        raise HTTPException(status_code=500, detail="Error initiating request processing")
