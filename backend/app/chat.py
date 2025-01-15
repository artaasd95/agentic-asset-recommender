import os
import uuid
import logging
from datetime import datetime
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from phi.agent import Agent, AgentMemory
from phi.model.openai import OpenAIChat
from phi.memory.db.postgres import PgMemoryDb
from phi.storage.agent.postgres import PgAgentStorage
from set_prompts import get_prompts
from remote_log_handler import RemoteLogHandler
from tools import *

# Load environment variables
load_dotenv()

# Retrieve variables from .env
MODEL = os.getenv("MODEL", 'gpt-4o-mini')
DB_URL = os.getenv("DB_URL", "")
LOG_URL = os.getenv("LOG_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Configure remote logger
logger = logging.getLogger("remote_logger")
logger.setLevel(logging.INFO)

remote_handler = RemoteLogHandler(LOG_URL)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
remote_handler.setFormatter(formatter)
logger.addHandler(remote_handler)


# FastAPI application initialization
app = FastAPI()

# Define the request body
class QueryItem(BaseModel):
    query: str
    user_id: str
    session_id: str
    asset_ticker: str


instruction_list, guideline_list = get_prompts()

# Create a single agent instance
agent = Agent(
    name="Financial asset recommender",
    model=OpenAIChat(id=MODEL,
                     api_key=OPENAI_API_KEY),
    tools=[
        perform_calculations_for_tickers,
        send_raw_data_to_api,
        send_features_to_api,
    ],
    memory=AgentMemory(
        db=PgMemoryDb(table_name="fin_agent_memory_", db_url=DB_URL),
        create_user_memories=True,
        create_session_summary=True
    ),
    storage=PgAgentStorage(
        table_name="global_user_sessions_",
        db_url=DB_URL
    ),
    instructions=instruction_list,
    guidelines=guideline_list,
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
        agent.additional_context = f"current datetime is: {str(datetime.datetime.now())}"
        agent.user_id = request.user_id or str(uuid.uuid4())
        agent.session_id = request.session_id or str(uuid.uuid4())

        # Add logic to process the query using the agent
        response = agent.run(f"{request.query} and the ticker is {request.asset_ticker}")
        logger.info("Query processed successfully.")
        return JSONResponse(content=response.content)
    except Exception as e:
        logger.error(f"Error initiating query: {str(e)}")
        raise HTTPException(status_code=500, detail="Error initiating request processing")
