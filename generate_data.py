import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_sample_data():
    """Generate sample historical data for demand forecasting and cost analysis"""
    
    # Generate date range for 2 years of historical data
    start_date = datetime.now() - timedelta(days=730)
    dates = pd.date_range(start=start_date, periods=730, freq='D')
    
    # Sample item IDs
    item_ids = ['ITEM001', 'ITEM002', 'ITEM003', 'ITEM004', 'ITEM005']
    
    all_data = []
    
    for item_id in item_ids:
        # Generate base demand with seasonal patterns
        base_demand = 100 + np.random.normal(0, 10, len(dates))
        seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
        weekly_factor = 1 + 0.1 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)
        trend = 0.001 * np.arange(len(dates))  # Small upward trend
        
        demand = base_demand * seasonal_factor * weekly_factor + trend
        demand = np.maximum(demand, 0)  # Ensure non-negative demand
        
        # Generate pricing data with some correlation to demand
        base_price = 50 + np.random.normal(0, 5, len(dates))
        price_trend = 0.01 * np.arange(len(dates))  # Inflation trend
        demand_price_correlation = 0.1 * (demand - np.mean(demand)) / np.std(demand)
        
        price = base_price + price_trend + demand_price_correlation
        price = np.maximum(price, 10)  # Minimum price
        
        # Generate cost data
        base_cost = price * 0.7  # 70% of price as base cost
        cost_variance = np.random.normal(0, price * 0.05, len(dates))
        cost = base_cost + cost_variance
        cost = np.maximum(cost, 5)  # Minimum cost
        
        # Generate waste data (percentage of demand)
        waste_rate = np.random.beta(2, 8, len(dates)) * 0.15  # 0-15% waste
        waste_quantity = demand * waste_rate
        
        for i, date in enumerate(dates):
            all_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'item_id': item_id,
                'demand': round(demand[i], 2),
                'price': round(price[i], 2),
                'cost': round(cost[i], 2),
                'waste_quantity': round(waste_quantity[i], 2),
                'waste_rate': round(waste_rate[i], 4)
            })
    
    return all_data

def save_sample_data():
    """Generate and save sample data to files"""
    data = generate_sample_data()
    
    # Save as JSON
    with open('/home/ubuntu/forecasting-dashboard/data/historical_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Save as CSV
    df = pd.DataFrame(data)
    df.to_csv('/home/ubuntu/forecasting-dashboard/data/historical_data.csv', index=False)
    
    # Generate summary statistics
    summary = df.groupby('item_id').agg({
        'demand': ['mean', 'std', 'min', 'max'],
        'price': ['mean', 'std', 'min', 'max'],
        'cost': ['mean', 'std', 'min', 'max'],
        'waste_rate': ['mean', 'std', 'min', 'max']
    }).round(2)
    
    summary.to_csv('/home/ubuntu/forecasting-dashboard/data/data_summary.csv')
    
    print(f"Generated {len(data)} records for {len(df['item_id'].unique())} items")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print("\nSample data preview:")
    print(df.head(10))
    print("\nData summary:")
    print(summary)

if __name__ == "__main__":
    save_sample_data()

