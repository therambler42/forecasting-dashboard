import pandas as pd
import numpy as np
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')

class ForecastingService:
    """Service for demand and price forecasting using Prophet and ARIMA models"""
    
    def __init__(self):
        self.prophet_models = {}
        self.arima_models = {}
        self.model_params = {}
    
    def prepare_data_for_prophet(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Prepare data for Prophet model (requires 'ds' and 'y' columns)"""
        prophet_df = df[['date', target_col]].copy()
        prophet_df.columns = ['ds', 'y']
        prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
        return prophet_df.dropna()
    
    def prepare_data_for_arima(self, df: pd.DataFrame, target_col: str) -> pd.Series:
        """Prepare data for ARIMA model"""
        series = df.set_index('date')[target_col].copy()
        series.index = pd.to_datetime(series.index)
        return series.dropna()
    
    def train_prophet_model(self, df: pd.DataFrame, target_col: str, item_id: str) -> Prophet:
        """Train Prophet model for given target column and item"""
        prophet_df = self.prepare_data_for_prophet(df, target_col)
        
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            interval_width=0.8
        )
        
        model.fit(prophet_df)
        model_key = f"{item_id}_{target_col}_prophet"
        self.prophet_models[model_key] = model
        
        return model
    
    def train_arima_model(self, df: pd.DataFrame, target_col: str, item_id: str) -> ARIMA:
        """Train ARIMA model for given target column and item"""
        series = self.prepare_data_for_arima(df, target_col)
        
        # Auto-select ARIMA parameters (simplified approach)
        # In production, you might want to use auto_arima from pmdarima
        try:
            model = ARIMA(series, order=(2, 1, 2))
            fitted_model = model.fit()
            
            model_key = f"{item_id}_{target_col}_arima"
            self.arima_models[model_key] = fitted_model
            
            return fitted_model
        except Exception as e:
            # Fallback to simpler model if complex one fails
            model = ARIMA(series, order=(1, 1, 1))
            fitted_model = model.fit()
            
            model_key = f"{item_id}_{target_col}_arima"
            self.arima_models[model_key] = fitted_model
            
            return fitted_model
    
    def forecast_prophet(self, model: Prophet, days: int) -> pd.DataFrame:
        """Generate forecast using Prophet model"""
        future = model.make_future_dataframe(periods=days)
        forecast = model.predict(future)
        return forecast.tail(days)
    
    def forecast_arima(self, model: ARIMA, days: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate forecast using ARIMA model"""
        forecast = model.forecast(steps=days)
        conf_int = model.get_forecast(steps=days).conf_int()
        return forecast, conf_int
    
    def calculate_metrics(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
        """Calculate forecast accuracy metrics"""
        mae = mean_absolute_error(actual, predicted)
        mse = mean_squared_error(actual, predicted)
        rmse = np.sqrt(mse)
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        # Calculate R² score
        r2 = r2_score(actual, predicted)
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape,
            'r2_score': r2
        }
    
    def backtest_model(self, df: pd.DataFrame, target_col: str, item_id: str, 
                      model_type: str = 'prophet', test_days: int = 30) -> Dict[str, float]:
        """Perform backtesting to evaluate model accuracy"""
        # Split data for backtesting
        train_df = df.iloc[:-test_days].copy()
        test_df = df.iloc[-test_days:].copy()
        
        if model_type == 'prophet':
            model = self.train_prophet_model(train_df, target_col, f"{item_id}_backtest")
            forecast_df = self.forecast_prophet(model, test_days)
            predicted = forecast_df['yhat'].values
        else:  # arima
            model = self.train_arima_model(train_df, target_col, f"{item_id}_backtest")
            predicted, _ = self.forecast_arima(model, test_days)
        
        actual = test_df[target_col].values
        metrics = self.calculate_metrics(actual, predicted)
        
        return metrics
    
    def generate_forecast(self, df: pd.DataFrame, item_id: str, days: int = 90, 
                         model_type: str = 'prophet') -> Dict[str, Any]:
        """Generate comprehensive forecast for demand and price"""
        
        # Filter data for specific item
        item_df = df[df['item_id'] == item_id].copy()
        item_df = item_df.sort_values('date')
        
        if len(item_df) < 30:
            raise ValueError(f"Insufficient data for item {item_id}. Need at least 30 data points.")
        
        results = {
            'item_id': item_id,
            'model_type': model_type,
            'forecast_days': days,
            'forecasts': [],
            'metrics': {}
        }
        
        # Generate forecasts for both demand and price
        for target in ['demand', 'price']:
            if model_type == 'prophet':
                # Train Prophet model
                model = self.train_prophet_model(item_df, target, item_id)
                forecast_df = self.forecast_prophet(model, days)
                
                # Extract forecast data
                forecast_data = {
                    'dates': forecast_df['ds'].dt.strftime('%Y-%m-%d').tolist(),
                    'forecast': forecast_df['yhat'].tolist(),
                    'lower': forecast_df['yhat_lower'].tolist(),
                    'upper': forecast_df['yhat_upper'].tolist()
                }
                
            else:  # arima
                # Train ARIMA model
                model = self.train_arima_model(item_df, target, item_id)
                forecast_values, conf_int = self.forecast_arima(model, days)
                
                # Generate future dates
                last_date = pd.to_datetime(item_df['date'].iloc[-1])
                future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), 
                                           periods=days, freq='D')
                
                forecast_data = {
                    'dates': future_dates.strftime('%Y-%m-%d').tolist(),
                    'forecast': forecast_values.tolist(),
                    'lower': conf_int.iloc[:, 0].tolist(),
                    'upper': conf_int.iloc[:, 1].tolist()
                }
            
            results['forecasts'].append({
                'target': target,
                'data': forecast_data
            })
            
            # Calculate backtest metrics
            try:
                metrics = self.backtest_model(item_df, target, item_id, model_type)
                results['metrics'][f'{target}_metrics'] = metrics
            except Exception as e:
                results['metrics'][f'{target}_metrics'] = {'error': str(e)}
        
        return results

