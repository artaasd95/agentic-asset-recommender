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


# --------------------------------------------------------------------------
# Helpers to store daily candlestick data and computed features
# --------------------------------------------------------------------------
def store_daily_data(df: pd.DataFrame, ticker: str) -> None:
    logger.info(f"Storing daily data for ticker: {ticker}")
    df = df.reset_index()  # Typically adds a 'Date' column if df is from yfinance

    for _, row in df.iterrows():
        try:
            data = MainData(
                ticker=ticker,
                date_time=row["Date"],
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"])
            )
            logger.info(f"Sending raw data to API for {ticker} on {row['Date']}")
            send_raw_data_to_api(data.model_dump())
        except Exception as e:
            logger.error(f"Failed to store raw data for {ticker}: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to store raw data: {str(e)}")
    
    logger.info(f"Finished storing daily data for {ticker}")


def store_computed_features(ticker: str, features_dict: dict) -> None:
    logger.info(f"Storing computed features for ticker: {ticker}")
    
    doc_id = f"{ticker}_features_{datetime.datetime.utcnow().isoformat()}"
    text_content = str(features_dict)

    payload = {
        "id": doc_id,
        "text": text_content
    }
    try:
        logger.info(f"Sending computed features for {ticker} to vector store")
        send_features_to_api(payload)
    except Exception as e:
        logger.error(f"Failed to store computed features for {ticker}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to store computed features: {str(e)}")
    
    logger.info(f"Successfully stored computed features for {ticker}")


def resolve_dates(
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple[str, str]:
    logger.info("Resolving date range for data fetching")
    
    if end_date:
        end_date_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date_dt = datetime.datetime.today()

    if start_date:
        start_date_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date_dt = end_date_dt - datetime.timedelta(days=365 * 2)
    
    resolved_start = start_date_dt.strftime('%Y-%m-%d')
    resolved_end = end_date_dt.strftime('%Y-%m-%d')
    logger.info(f"Resolved start date: {resolved_start}, end date: {resolved_end}")
    
    return resolved_start, resolved_end


@app.post("/perform_calculations")
async def perform_calculations_for_ticker(request: TickerRequest):
    logger.info(f"Received calculation request for ticker: {request.ticker}")
    
    ticker = request.ticker
    start_date, end_date = resolve_dates(request.start_date, request.end_date)
    
    logger.info(f"Fetching candlestick data for {ticker} from {start_date} to {end_date}")
    df = fetch_candlestick_data(ticker, start_date, end_date)
    if df.empty:
        logger.error(f"No data found for {ticker} between {start_date} and {end_date}")
        raise HTTPException(status_code=404, detail=f"No data found for {ticker} between {start_date} and {end_date}")

    if request.store_raw:
        logger.info(f"Storing raw candlestick data for {ticker}")
        store_daily_data(df, ticker)
    
    logger.info(f"Performing calculations for {ticker}")
    calculations_str = perform_calculations_for_tickers(
        ticker, start_date, end_date
    )
    
    import ast
    try:
        calculations = ast.literal_eval(calculations_str)
        logger.info(f"Calculations completed successfully for {ticker}")
    except Exception as e:
        logger.error(f"Failed to parse calculations for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse calculations: {str(e)}")
    
    if request.store_features:
        ticker_features = calculations.get(ticker, {})
        logger.info(f"Storing computed features for {ticker}")
        store_computed_features(ticker, ticker_features)
    
    logger.info(f"Completed processing request for {ticker}")
    return {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "calculations": calculations
    }
