from pydantic import BaseModel
from datetime import datetime, date

class MainData(BaseModel):
    ticker: str
    date_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class FeatureData(BaseModel):
    ticker: str
    name: str
    start_date: date
    end_date: date
    value: float
