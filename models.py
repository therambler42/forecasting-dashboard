from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class HistoricalDataPoint(BaseModel):
    """Model for historical data points"""
    date: str
    item_id: str
    demand: float
    price: float
    cost: float
    waste_quantity: float
    waste_rate: float

class ForecastRequest(BaseModel):
    """Model for forecast request parameters"""
    item_id: str
    days: int = 90
    model_type: Optional[str] = "prophet"  # "prophet" or "arima"

class ForecastPoint(BaseModel):
    """Model for individual forecast data points"""
    date: str
    demand_forecast: float
    demand_lower: float
    demand_upper: float
    price_forecast: float
    price_lower: float
    price_upper: float
    confidence: float

class ForecastResponse(BaseModel):
    """Model for forecast API response"""
    item_id: str
    forecast_days: int
    model_type: str
    generated_at: str
    mae_demand: Optional[float] = None
    mae_price: Optional[float] = None
    forecasts: List[ForecastPoint]

class ModelMetrics(BaseModel):
    """Model for forecast accuracy metrics"""
    mae: float
    mape: float
    rmse: float
    r2_score: float

class CostAnalysis(BaseModel):
    """Model for cost analysis data"""
    item_id: str
    period: str
    avg_cost: float
    cost_variance: float
    waste_rate: float
    total_waste_cost: float

