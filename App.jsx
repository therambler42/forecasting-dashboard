import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Badge } from './components/ui/badge';
import { Loader2, TrendingUp, TrendingDown, AlertTriangle, DollarSign } from 'lucide-react';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [items, setItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState('');
  const [forecastData, setForecastData] = useState(null);
  const [costAnalysis, setCostAnalysis] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [forecastDays, setForecastDays] = useState(90);
  const [modelType, setModelType] = useState('prophet');

  // Load available items on component mount
  useEffect(() => {
    const fetchItems = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/items`);
        setItems(response.data.items);
        if (response.data.items.length > 0) {
          setSelectedItem(response.data.items[0]);
        }
      } catch (err) {
        setError('Failed to load items');
        console.error('Error fetching items:', err);
      }
    };

    fetchItems();
  }, []);

  // Load data when item selection changes
  useEffect(() => {
    if (selectedItem) {
      loadForecastData();
      loadCostAnalysis();
      loadMetrics();
    }
  }, [selectedItem, forecastDays, modelType]);

  const loadForecastData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/forecast/${selectedItem}?days=${forecastDays}&model=${modelType}`
      );
      setForecastData(response.data);
    } catch (err) {
      setError('Failed to load forecast data');
      console.error('Error fetching forecast:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCostAnalysis = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/cost-analysis/${selectedItem}?period=30d`);
      setCostAnalysis(response.data);
    } catch (err) {
      console.error('Error fetching cost analysis:', err);
    }
  };

  const loadMetrics = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/metrics/${selectedItem}?model=${modelType}`);
      setMetrics(response.data);
    } catch (err) {
      console.error('Error fetching metrics:', err);
    }
  };

  const createForecastChart = () => {
    if (!forecastData || !forecastData.forecasts) return null;

    const dates = forecastData.forecasts.map(f => f.date);
    const demandForecast = forecastData.forecasts.map(f => f.demand_forecast);
    const demandLower = forecastData.forecasts.map(f => f.demand_lower);
    const demandUpper = forecastData.forecasts.map(f => f.demand_upper);

    return {
      data: [
        {
          x: dates,
          y: demandForecast,
          type: 'scatter',
          mode: 'lines',
          name: 'Demand Forecast',
          line: { color: '#3b82f6', width: 3 }
        },
        {
          x: dates,
          y: demandUpper,
          type: 'scatter',
          mode: 'lines',
          name: 'Upper Bound',
          line: { color: '#3b82f6', width: 1, dash: 'dot' },
          showlegend: false
        },
        {
          x: dates,
          y: demandLower,
          type: 'scatter',
          mode: 'lines',
          name: 'Lower Bound',
          line: { color: '#3b82f6', width: 1, dash: 'dot' },
          fill: 'tonexty',
          fillcolor: 'rgba(59, 130, 246, 0.1)',
          showlegend: false
        }
      ],
      layout: {
        title: `Demand Forecast - ${selectedItem}`,
        xaxis: { title: 'Date' },
        yaxis: { title: 'Demand' },
        height: 400,
        margin: { t: 50, r: 50, b: 50, l: 50 }
      }
    };
  };

  const createPriceChart = () => {
    if (!forecastData || !forecastData.forecasts) return null;

    const dates = forecastData.forecasts.map(f => f.date);
    const priceForecast = forecastData.forecasts.map(f => f.price_forecast);
    const priceLower = forecastData.forecasts.map(f => f.price_lower);
    const priceUpper = forecastData.forecasts.map(f => f.price_upper);

    return {
      data: [
        {
          x: dates,
          y: priceForecast,
          type: 'scatter',
          mode: 'lines',
          name: 'Price Forecast',
          line: { color: '#10b981', width: 3 }
        },
        {
          x: dates,
          y: priceUpper,
          type: 'scatter',
          mode: 'lines',
          name: 'Upper Bound',
          line: { color: '#10b981', width: 1, dash: 'dot' },
          showlegend: false
        },
        {
          x: dates,
          y: priceLower,
          type: 'scatter',
          mode: 'lines',
          name: 'Lower Bound',
          line: { color: '#10b981', width: 1, dash: 'dot' },
          fill: 'tonexty',
          fillcolor: 'rgba(16, 185, 129, 0.1)',
          showlegend: false
        }
      ],
      layout: {
        title: `Price Forecast - ${selectedItem}`,
        xaxis: { title: 'Date' },
        yaxis: { title: 'Price ($)' },
        height: 400,
        margin: { t: 50, r: 50, b: 50, l: 50 }
      }
    };
  };

  const getAccuracyBadge = (mae) => {
    if (mae <= 5) return <Badge className="bg-green-500">Excellent (≤5%)</Badge>;
    if (mae <= 10) return <Badge className="bg-yellow-500">Good (≤10%)</Badge>;
    return <Badge className="bg-red-500">Needs Improvement (&gt;10%)</Badge>;
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-foreground">
            Demand Forecasting & Cost Trends Dashboard
          </h1>
          <p className="text-muted-foreground">
            Advanced analytics for demand prediction and cost optimization
          </p>
        </div>

        {/* Controls */}
        <Card>
          <CardHeader>
            <CardTitle>Forecast Configuration</CardTitle>
            <CardDescription>
              Select item and configure forecast parameters
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Item</label>
                <Select value={selectedItem} onValueChange={setSelectedItem}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select item" />
                  </SelectTrigger>
                  <SelectContent>
                    {items.map(item => (
                      <SelectItem key={item} value={item}>{item}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Forecast Days</label>
                <Select value={forecastDays.toString()} onValueChange={(value) => setForecastDays(parseInt(value))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30">30 days</SelectItem>
                    <SelectItem value="60">60 days</SelectItem>
                    <SelectItem value="90">90 days</SelectItem>
                    <SelectItem value="180">180 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Model</label>
                <Select value={modelType} onValueChange={setModelType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="prophet">Prophet</SelectItem>
                    <SelectItem value="arima">ARIMA</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-end">
                <Button onClick={loadForecastData} disabled={loading || !selectedItem}>
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Update Forecast
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2 text-red-600">
                <AlertTriangle className="w-5 h-5" />
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Metrics Cards */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Demand MAE</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.demand_metrics.mae}</div>
                <div className="mt-2">{getAccuracyBadge(metrics.demand_metrics.mae)}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Price MAE</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.price_metrics.mae}</div>
                <div className="mt-2">{getAccuracyBadge(metrics.price_metrics.mae)}</div>
              </CardContent>
            </Card>
            
            {costAnalysis && (
              <>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg Cost</CardTitle>
                    <TrendingDown className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">${costAnalysis.avg_cost}</div>
                    <p className="text-xs text-muted-foreground">Last 30 days</p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Waste Rate</CardTitle>
                    <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{(costAnalysis.waste_rate * 100).toFixed(2)}%</div>
                    <p className="text-xs text-muted-foreground">
                      ${costAnalysis.total_waste_cost} total waste cost
                    </p>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        )}

        {/* Charts */}
        {forecastData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Demand Forecast</CardTitle>
                <CardDescription>
                  {forecastDays}-day demand prediction using {modelType.toUpperCase()} model
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Plot
                  {...createForecastChart()}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Price Forecast</CardTitle>
                <CardDescription>
                  {forecastDays}-day price prediction using {modelType.toUpperCase()} model
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Plot
                  {...createPriceChart()}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </CardContent>
            </Card>
          </div>
        )}

        {/* Model Information */}
        {forecastData && (
          <Card>
            <CardHeader>
              <CardTitle>Model Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="font-medium">Model Type:</span> {forecastData.model_type.toUpperCase()}
                </div>
                <div>
                  <span className="font-medium">Forecast Period:</span> {forecastData.forecast_days} days
                </div>
                <div>
                  <span className="font-medium">Generated:</span> {new Date(forecastData.generated_at).toLocaleString()}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default App;

