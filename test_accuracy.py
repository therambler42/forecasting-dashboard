import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add backend directory to path
sys.path.append('/home/ubuntu/forecasting-dashboard/backend')

from forecasting_service import ForecastingService
from models import ForecastResponse

class TestForecastingAccuracy(unittest.TestCase):
    """Test suite for forecasting model accuracy"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.forecasting_service = ForecastingService()
        
        # Load test data
        self.test_data = pd.read_csv('/home/ubuntu/forecasting-dashboard/data/historical_data.csv')
        self.test_items = ['ITEM001', 'ITEM002', 'ITEM003']
        
    def test_prophet_demand_accuracy(self):
        """Test Prophet model accuracy for demand forecasting"""
        for item_id in self.test_items:
            with self.subTest(item=item_id):
                item_df = self.test_data[self.test_data['item_id'] == item_id].copy()
                
                # Perform backtest
                metrics = self.forecasting_service.backtest_model(
                    item_df, 'demand', item_id, 'prophet', test_days=30
                )
                
                # Assert MAE <= 5% requirement
                mae = metrics['mae']
                self.assertLessEqual(mae, 5.0, 
                    f"Prophet demand MAE {mae:.4f} exceeds 5.0 threshold for {item_id}")
                
                # Additional quality checks
                self.assertGreater(metrics['r2_score'], 0.5, 
                    f"Prophet demand R² {metrics['r2_score']:.4f} too low for {item_id}")
                self.assertLess(metrics['mape'], 15.0, 
                    f"Prophet demand MAPE {metrics['mape']:.2f}% too high for {item_id}")
    
    def test_prophet_price_accuracy(self):
        """Test Prophet model accuracy for price forecasting"""
        for item_id in self.test_items:
            with self.subTest(item=item_id):
                item_df = self.test_data[self.test_data['item_id'] == item_id].copy()
                
                # Perform backtest
                metrics = self.forecasting_service.backtest_model(
                    item_df, 'price', item_id, 'prophet', test_days=30
                )
                
                # Assert MAE <= 5% requirement
                mae = metrics['mae']
                self.assertLessEqual(mae, 5.0, 
                    f"Prophet price MAE {mae:.4f} exceeds 5.0 threshold for {item_id}")
                
                # Additional quality checks
                self.assertGreater(metrics['r2_score'], 0.3, 
                    f"Prophet price R² {metrics['r2_score']:.4f} too low for {item_id}")
    
    def test_arima_demand_accuracy(self):
        """Test ARIMA model accuracy for demand forecasting"""
        for item_id in self.test_items:
            with self.subTest(item=item_id):
                item_df = self.test_data[self.test_data['item_id'] == item_id].copy()
                
                # Perform backtest
                metrics = self.forecasting_service.backtest_model(
                    item_df, 'demand', item_id, 'arima', test_days=30
                )
                
                # Assert MAE <= 5% requirement
                mae = metrics['mae']
                self.assertLessEqual(mae, 5.0, 
                    f"ARIMA demand MAE {mae:.4f} exceeds 5.0 threshold for {item_id}")
    
    def test_arima_price_accuracy(self):
        """Test ARIMA model accuracy for price forecasting"""
        for item_id in self.test_items:
            with self.subTest(item=item_id):
                item_df = self.test_data[self.test_data['item_id'] == item_id].copy()
                
                # Perform backtest
                metrics = self.forecasting_service.backtest_model(
                    item_df, 'price', item_id, 'arima', test_days=30
                )
                
                # Assert MAE <= 5% requirement
                mae = metrics['mae']
                self.assertLessEqual(mae, 5.0, 
                    f"ARIMA price MAE {mae:.4f} exceeds 5.0 threshold for {item_id}")
    
    def test_forecast_generation_prophet(self):
        """Test end-to-end forecast generation with Prophet"""
        item_id = 'ITEM001'
        
        result = self.forecasting_service.generate_forecast(
            self.test_data, item_id, days=30, model_type='prophet'
        )
        
        # Validate response structure
        self.assertEqual(result['item_id'], item_id)
        self.assertEqual(result['model_type'], 'prophet')
        self.assertEqual(result['forecast_days'], 30)
        self.assertEqual(len(result['forecasts']), 2)  # demand and price
        
        # Validate forecast data
        demand_forecast = next(f for f in result['forecasts'] if f['target'] == 'demand')
        price_forecast = next(f for f in result['forecasts'] if f['target'] == 'price')
        
        self.assertEqual(len(demand_forecast['data']['dates']), 30)
        self.assertEqual(len(price_forecast['data']['dates']), 30)
        
        # Check that forecasts are reasonable (positive values)
        self.assertTrue(all(v > 0 for v in demand_forecast['data']['forecast']))
        self.assertTrue(all(v > 0 for v in price_forecast['data']['forecast']))
    
    def test_forecast_generation_arima(self):
        """Test end-to-end forecast generation with ARIMA"""
        item_id = 'ITEM001'
        
        result = self.forecasting_service.generate_forecast(
            self.test_data, item_id, days=30, model_type='arima'
        )
        
        # Validate response structure
        self.assertEqual(result['item_id'], item_id)
        self.assertEqual(result['model_type'], 'arima')
        self.assertEqual(result['forecast_days'], 30)
        self.assertEqual(len(result['forecasts']), 2)  # demand and price
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data scenarios"""
        # Create minimal dataset
        minimal_data = self.test_data.head(10)
        
        with self.assertRaises(ValueError):
            self.forecasting_service.generate_forecast(
                minimal_data, 'ITEM001', days=30, model_type='prophet'
            )
    
    def test_invalid_item_handling(self):
        """Test handling of invalid item IDs"""
        with self.assertRaises(ValueError):
            self.forecasting_service.generate_forecast(
                self.test_data, 'INVALID_ITEM', days=30, model_type='prophet'
            )

class TestModelPerformance(unittest.TestCase):
    """Test suite for model performance benchmarks"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.forecasting_service = ForecastingService()
        self.test_data = pd.read_csv('/home/ubuntu/forecasting-dashboard/data/historical_data.csv')
    
    def test_forecast_generation_speed(self):
        """Test that forecast generation completes within reasonable time"""
        import time
        
        start_time = time.time()
        
        result = self.forecasting_service.generate_forecast(
            self.test_data, 'ITEM001', days=90, model_type='prophet'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within 30 seconds for 90-day forecast
        self.assertLess(duration, 30.0, 
            f"Forecast generation took {duration:.2f}s, exceeds 30s threshold")
    
    def test_model_consistency(self):
        """Test that models produce consistent results across runs"""
        item_id = 'ITEM001'
        
        # Generate two forecasts with same parameters
        result1 = self.forecasting_service.generate_forecast(
            self.test_data, item_id, days=30, model_type='prophet'
        )
        
        result2 = self.forecasting_service.generate_forecast(
            self.test_data, item_id, days=30, model_type='prophet'
        )
        
        # Extract demand forecasts
        demand1 = next(f for f in result1['forecasts'] if f['target'] == 'demand')['data']['forecast']
        demand2 = next(f for f in result2['forecasts'] if f['target'] == 'demand')['data']['forecast']
        
        # Calculate correlation between forecasts
        correlation = np.corrcoef(demand1, demand2)[0, 1]
        
        # Should be highly correlated (>0.95)
        self.assertGreater(correlation, 0.95, 
            f"Forecast consistency correlation {correlation:.4f} too low")

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestForecastingAccuracy))
    test_suite.addTest(unittest.makeSuite(TestModelPerformance))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"- {test}: {error_msg}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"- {test}: {error_msg}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)

