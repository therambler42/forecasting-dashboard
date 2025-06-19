from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import json
from datetime import datetime
from typing import Optional
import os

from models import ForecastResponse, ForecastPoint, ModelMetrics, CostAnalysis
from forecasting_service import ForecastingService

# Initialize FastAPI app
app = FastAPI(
    title="Demand Forecasting & Cost Trends API",
    description="REST API for demand and price forecasting with cost analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize forecasting service
forecasting_service = ForecastingService()

# Load historical data
def load_historical_data():
    """Load historical data from JSON file"""
    data_path = "/home/ubuntu/forecasting-dashboard/data/historical_data.json"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Historical data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    return pd.DataFrame(data)

# Global variable to store data
historical_df = None

@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    global historical_df
    try:
        historical_df = load_historical_data()
        print(f"Loaded {len(historical_df)} historical records")
    except Exception as e:
        print(f"Error loading historical data: {e}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Demand Forecasting & Cost Trends API",
        "version": "1.0.0",
        "endpoints": {
            "forecast": "/forecast/{item_id}?days=90&model=prophet",
            "items": "/items",
            "metrics": "/metrics/{item_id}",
            "cost_analysis": "/cost-analysis/{item_id}"
        }
    }

@app.get("/items")
async def get_items():
    """Get list of available items"""
    if historical_df is None:
        raise HTTPException(status_code=500, detail="Historical data not loaded")
    
    items = historical_df['item_id'].unique().tolist()
    return {"items": items}

@app.get("/forecast/{item_id}")
async def get_forecast(
    item_id: str,
    days: int = Query(default=90, ge=1, le=365, description="Number of days to forecast"),
    model: str = Query(default="prophet", regex="^(prophet|arima)$", description="Forecasting model to use")
):
    """
    Generate demand and price forecasts for a specific item
    
    - **item_id**: Item identifier
    - **days**: Number of days to forecast (1-365)
    - **model**: Forecasting model ('prophet' or 'arima')
    """
    if historical_df is None:
        raise HTTPException(status_code=500, detail="Historical data not loaded")
    
    # Check if item exists
    if item_id not in historical_df['item_id'].values:
        available_items = historical_df['item_id'].unique().tolist()
        raise HTTPException(
            status_code=404, 
            detail=f"Item {item_id} not found. Available items: {available_items}"
        )
    
    try:
        # Generate forecast
        forecast_result = forecasting_service.generate_forecast(
            historical_df, item_id, days, model
        )
        
        # Transform to API response format
        forecast_points = []
        demand_data = next(f for f in forecast_result['forecasts'] if f['target'] == 'demand')['data']
        price_data = next(f for f in forecast_result['forecasts'] if f['target'] == 'price')['data']
        
        for i in range(len(demand_data['dates'])):
            point = ForecastPoint(
                date=demand_data['dates'][i],
                demand_forecast=round(demand_data['forecast'][i], 2),
                demand_lower=round(demand_data['lower'][i], 2),
                demand_upper=round(demand_data['upper'][i], 2),
                price_forecast=round(price_data['forecast'][i], 2),
                price_lower=round(price_data['lower'][i], 2),
                price_upper=round(price_data['upper'][i], 2),
                confidence=0.8  # 80% confidence interval
            )
            forecast_points.append(point)
        
        # Extract MAE metrics
        demand_mae = None
        price_mae = None
        
        if 'demand_metrics' in forecast_result['metrics']:
            demand_mae = round(forecast_result['metrics']['demand_metrics'].get('mae', 0), 4)
        
        if 'price_metrics' in forecast_result['metrics']:
            price_mae = round(forecast_result['metrics']['price_metrics'].get('mae', 0), 4)
        
        response = ForecastResponse(
            item_id=item_id,
            forecast_days=days,
            model_type=model,
            generated_at=datetime.now().isoformat(),
            mae_demand=demand_mae,
            mae_price=price_mae,
            forecasts=forecast_points
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")

@app.get("/metrics/{item_id}")
async def get_model_metrics(
    item_id: str,
    model: str = Query(default="prophet", regex="^(prophet|arima)$", description="Model to evaluate")
):
    """Get model accuracy metrics for a specific item"""
    if historical_df is None:
        raise HTTPException(status_code=500, detail="Historical data not loaded")
    
    if item_id not in historical_df['item_id'].values:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    try:
        item_df = historical_df[historical_df['item_id'] == item_id].copy()
        
        # Calculate metrics for both demand and price
        demand_metrics = forecasting_service.backtest_model(item_df, 'demand', item_id, model)
        price_metrics = forecasting_service.backtest_model(item_df, 'price', item_id, model)
        
        return {
            "item_id": item_id,
            "model_type": model,
            "demand_metrics": {
                "mae": round(demand_metrics['mae'], 4),
                "mape": round(demand_metrics['mape'], 2),
                "rmse": round(demand_metrics['rmse'], 4),
                "r2_score": round(demand_metrics['r2_score'], 4)
            },
            "price_metrics": {
                "mae": round(price_metrics['mae'], 4),
                "mape": round(price_metrics['mape'], 2),
                "rmse": round(price_metrics['rmse'], 4),
                "r2_score": round(price_metrics['r2_score'], 4)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics calculation error: {str(e)}")

@app.get("/cost-analysis/{item_id}")
async def get_cost_analysis(
    item_id: str,
    period: str = Query(default="30d", regex="^(7d|30d|90d|1y)$", description="Analysis period")
):
    """Get cost analysis and waste metrics for a specific item"""
    if historical_df is None:
        raise HTTPException(status_code=500, detail="Historical data not loaded")
    
    if item_id not in historical_df['item_id'].values:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    try:
        item_df = historical_df[historical_df['item_id'] == item_id].copy()
        item_df['date'] = pd.to_datetime(item_df['date'])
        
        # Filter by period
        period_days = {'7d': 7, '30d': 30, '90d': 90, '1y': 365}
        days = period_days[period]
        
        cutoff_date = item_df['date'].max() - pd.Timedelta(days=days)
        period_df = item_df[item_df['date'] >= cutoff_date]
        
        # Calculate cost analysis metrics
        avg_cost = period_df['cost'].mean()
        cost_variance = period_df['cost'].var()
        avg_waste_rate = period_df['waste_rate'].mean()
        total_waste_cost = (period_df['waste_quantity'] * period_df['price']).sum()
        
        analysis = CostAnalysis(
            item_id=item_id,
            period=period,
            avg_cost=round(avg_cost, 2),
            cost_variance=round(cost_variance, 2),
            waste_rate=round(avg_waste_rate, 4),
            total_waste_cost=round(total_waste_cost, 2)
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost analysis error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_loaded": historical_df is not None,
        "total_records": len(historical_df) if historical_df is not None else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

