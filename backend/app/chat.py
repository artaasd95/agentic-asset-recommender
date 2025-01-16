import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional
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
        response = agent.run(f"{request.query}")
        logger.info("Query processed successfully.")
        return JSONResponse(content=response.content)
    except Exception as e:
        logger.error(f"Error initiating query: {str(e)}")
        raise HTTPException(status_code=500, detail="Error initiating request processing")



# ------------------------------------------------------------------
# Endpoint for feature calculation and data gathering
# ------------------------------------------------------------------

class TickerRequest(BaseModel):
    """
    Model for the incoming request body.
    """
    ticker: str
    start_date: Optional[str] = None  # 'YYYY-MM-DD'
    end_date: Optional[str] = None    # 'YYYY-MM-DD'
    store_raw: bool = False
    store_features: bool = False

class MainData(BaseModel):
    """
    Mirroring the API code's MainData for storing raw candlestick data.
    """
    ticker: str
    date_time: datetime.datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class TickerRequest(BaseModel):
    """
    Model for the incoming request body.
    """
    ticker: str
    start_date: Optional[str] = None  # 'YYYY-MM-DD'
    end_date: Optional[str] = None    # 'YYYY-MM-DD'
    store_raw: bool = False
    store_features: bool = False

class MainData(BaseModel):
    """
    Mirroring the API code's MainData for storing raw candlestick data.
    """
    ticker: str
    date_time: datetime.datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


# --------------------------------------------------------------------------
# Helpers to store daily candlestick data and computed features
# --------------------------------------------------------------------------
def store_daily_data(df: pd.DataFrame, ticker: str) -> None:
    """
    For each row in the DataFrame, send to the MongoDB API using the MainData model.
    The DataFrame is assumed to have columns: [Open, High, Low, Close, Volume],
    and a DateTimeIndex or a 'Date' column after reset_index().
    """
    # Reset index to move date/time from index to a column
    df = df.reset_index()  # Typically adds a 'Date' column if df is from yfinance

    for _, row in df.iterrows():
        try:
            data = MainData(
                ticker=ticker,
                date_time=row["Date"],  # or row["index"] if it was named differently
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"])
            )
            # Convert to dict and send
            send_raw_data_to_api(data.dict())  # .dict() is JSON-serializable
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to store raw data: {str(e)}")

def store_computed_features(ticker: str, features_dict: dict) -> None:
    """
    Send computed features to the vector store. 
    Example: you might convert them into a text or JSON representation
    for your vector DB, or pass them as-is if your vector DB expects that shape.
    """
    # For illustration, create an ID + text structure
    doc_id = f"{ticker}_features_{datetime.datetime.utcnow().isoformat()}"
    text_content = str(features_dict)  # or use json.dumps(features_dict)

    payload = {
        "id": doc_id,
        "text": text_content
    }
    # Send to the vector database
    try:
        send_features_to_api(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to store computed features: {str(e)}")

def resolve_dates(
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple[str, str]:
    """
    Resolve start_date and end_date. 
    If none provided, defaults to two years ago until today.
    """
    # Convert strings (if present) to datetime objects
    if end_date:
        end_date_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date_dt = datetime.datetime.today()

    if start_date:
        start_date_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    else:
        # Two years prior to `end_date_dt`
        start_date_dt = end_date_dt - datetime.timedelta(days=365 * 2)

    # Return in 'YYYY-MM-DD' format
    return start_date_dt.strftime('%Y-%m-%d'), end_date_dt.strftime('%Y-%m-%d')

# --------------------------------------------------------------------------
# The FastAPI endpoint
# --------------------------------------------------------------------------
@app.post("/perform_calculations")
async def perform_calculations_for_ticker(request: TickerRequest):
    """
    1. Resolve start/end dates (default to two years if not provided).
    2. Fetch candlestick data from Yahoo Finance.
    3. If store_raw = True, store each daily row in MongoDB.
    4. Compute risk/volatility/annualized_return for the ticker.
    5. If store_features = True, store them in the vector DB.
    6. Return the computed results.
    """
    ticker = request.ticker
    start_date, end_date = resolve_dates(request.start_date, request.end_date)

    # 1) Fetch data
    df = fetch_candlestick_data(ticker, start_date, end_date)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker} between {start_date} and {end_date}")

    # 2) Optionally store daily candlestick data
    if request.store_raw:
        store_daily_data(df, ticker)

    # 3) Perform calculations (the function returns a string representation of a dict)
    calculations_str = perform_calculations_for_tickers(
        ticker, start_date, end_date
    )

    # Convert that string back to a dict
    import ast
    try:
        calculations = ast.literal_eval(calculations_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse calculations: {str(e)}")

    # 4) Optionally store computed features
    if request.store_features:
        ticker_features = calculations.get(ticker, {})
        store_computed_features(ticker, ticker_features)

    return {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "calculations": calculations
    }
