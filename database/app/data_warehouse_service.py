from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import yfinance as yf
import numpy as np
import requests

# Initialize FastAPI app
app = FastAPI()

# Initialize MongoDB client
client = MongoClient("mongodb://localhost:27017/")
db = client.financial_data

# Define Pydantic models
class CandleData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class AssetFeatures(BaseModel):
    name: str
    data: dict

# Functions to calculate financial metrics
def calculate_return(prices):
    return np.diff(prices) / prices[:-1]

def calculate_risk(prices):
    returns = calculate_return(prices)
    return np.std(returns)

# FastAPI routes

@app.get("/load_data/{asset_name}")
async def load_data(asset_name: str):
    try:
        ticker = yf.Ticker(asset_name)
        data = ticker.history(period="1y")
    except Exception as e:
        raise HTTPException(status_code=404, detail="Asset not available")

    if data.empty:
        raise HTTPException(status_code=404, detail="No data found for this asset")

    prices = data['Close'].values
    asset_return = calculate_return(prices)
    asset_risk = calculate_risk(prices)

    candles = [
        CandleData(
            date=str(index), open=row['Open'], high=row['High'],
            low=row['Low'], close=row['Close'], volume=row['Volume']
        ).dict() for index, row in data.iterrows()
    ]

    features = AssetFeatures(
        name=asset_name,
        data={
            "return": asset_return.tolist(),
            "risk": asset_risk.tolist(),
        }
    ).dict()

    db.candles.insert_many(candles)
    db.features.insert_one(features)

    return {"message": f"Data for asset {asset_name} loaded successfully"}

@app.post("/load_all_data")
async def load_all_data():
    pass

@app.post("/send_features/{asset_name}")
async def send_features(asset_name: str, api_url: str):
    # Fetch asset features from MongoDB
    feature_doc = db.features.find_one({"name": asset_name})
    
    if not feature_doc:
        raise HTTPException(status_code=404, detail="Features not found for the asset")

    # Construct the payload for the destination API
    payload = {
        "name": feature_doc['name'],
        "data": feature_doc['data']
    }

    # Send the data to the external API
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send data: {e}")

    return {"message": f"Features for asset {asset_name} sent successfully"}

# Run the FastAPI application