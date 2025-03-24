import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

from data_fetcher import DataFetcher
from predictive_model import PredictiveModel

class StockAnalyzer:
    """
    Main class for analyzing stock data, combining real-time information,
    historical data and predictive modeling.
    """
    
    def __init__(self, symbol):
        """
        Initialize the StockAnalyzer with a stock symbol.
        
        Args:
            symbol (str): The stock symbol to analyze (e.g., 'AAPL')
        """
        self.symbol = symbol.upper()
        self.data_fetcher = DataFetcher()
        self.predictive_model = PredictiveModel()
        
        # Cache for storing fetched data to avoid redundant API calls
        self._real_time_data_cache = None
        self._historical_data_cache = None
        self._predictive_data_cache = None
    
    def get_real_time_data(self):
        """
        Get real-time data for the stock.
        
        Returns:
            dict: Real-time stock data including price, change, and previous close
        """
        if self._real_time_data_cache is None:
            self._real_time_data_cache = self.data_fetcher.fetch_real_time_data(self.symbol)
        return self._real_time_data_cache
    
    def get_historical_data(self, days=30):
        """
        Get historical OHLC data for the specified number of days.
        
        Args:
            days (int): Number of days of historical data to retrieve
            
        Returns:
            pandas.DataFrame: DataFrame with historical OHLC data
        """
        if self._historical_data_cache is None:
            self._historical_data_cache = self.data_fetcher.fetch_historical_data(self.symbol, days)
        return self._historical_data_cache
    
    def get_news(self, limit=5):
        """
        Get the latest news for the stock.
        
        Args:
            limit (int): Maximum number of news items to retrieve
            
        Returns:
            list: List of news articles
        """
        return self.data_fetcher.fetch_news(self.symbol, limit)
    
    def get_predictive_data(self, days=5):
        """
        Generate predictive data for the specified number of future days.
        
        Args:
            days (int): Number of days to predict
            
        Returns:
            dict: Dictionary containing predicted prices and percentage changes
        """
        # We'll regenerate predictions if:
        # 1. The cache is None, or
        # 2. The requested days is different from previous request
        regenerate = (self._predictive_data_cache is None or 
                     (self._predictive_data_cache is not None and 
                      'prices' in self._predictive_data_cache and 
                      len(self._predictive_data_cache['prices']) != days))
        
        if regenerate:
            # Get historical data to base predictions on
            historical_data = self.get_historical_data()
            
            if historical_data is not None and not historical_data.empty:
                # Get current price from real-time data
                real_time_data = self.get_real_time_data()
                current_price = real_time_data['price']
                
                # Generate predictions
                self._predictive_data_cache = self.predictive_model.generate_predictions(
                    historical_data,
                    current_price,
                    days
                )
        
        return self._predictive_data_cache
    
    def get_trend_analysis(self, days=5):
        """
        Get trend analysis for the stock based on historical and predictive data.
        
        Args:
            days (int): Number of days to predict
            
        Returns:
            dict: Dictionary containing trend analysis data
        """
        historical_data = self.get_historical_data()
        predictive_data = self.get_predictive_data(days=days)
        
        return self.predictive_model.analyze_trend(historical_data, predictive_data)
    
    def combine_historical_and_predictive(self, days=5):
        """
        Combine historical and predictive data into a single DataFrame.
        
        Args:
            days (int): Number of days to predict
            
        Returns:
            pandas.DataFrame: Combined historical and predictive data
        """
        # Get historical data
        historical_df = self.get_historical_data().copy()
        historical_df['type'] = 'historical'
        
        # Get predictive data with the specified number of days
        predictive_data = self.get_predictive_data(days=days)
        
        # Create a DataFrame for predictive data
        # Handle the case when historical_df might be empty or None
        if historical_df is None or len(historical_df) == 0:
            # If we don't have historical data, use current date as reference
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Create a list of dates for the predictive data points, skipping weekends for stock market
            dates = []
            
            # We should only have trading days (Mon-Fri) for stocks
            # For crypto and other assets that trade on weekends, this could be adjusted
            current_date = start_date
            days_added = 0
            
            while days_added < len(predictive_data['prices']):
                current_date = current_date + timedelta(days=1)
                # Skip weekends (5 = Saturday, 6 = Sunday)
                if self.symbol.endswith('.X') or self.symbol.endswith('-USD'):
                    # For crypto and certain assets, include all days
                    dates.append(current_date)
                    days_added += 1
                elif current_date.weekday() < 5:  # Monday to Friday
                    # For stocks, only include weekdays
                    dates.append(current_date)
                    days_added += 1
        else:
            # Get the last date from historical data
            last_date = historical_df.index[-1]
            
            # Convert pandas Timestamp to Python datetime to avoid arithmetic issues
            if isinstance(last_date, pd.Timestamp):
                last_date = last_date.to_pydatetime()
            
            # Create a list of dates for the predictive data points, skipping weekends for stock market
            dates = []
            
            # We should only have trading days (Mon-Fri) for stocks
            # For crypto and other assets that trade on weekends, this could be adjusted
            current_date = last_date
            days_added = 0
            
            while days_added < len(predictive_data['prices']):
                current_date = current_date + timedelta(days=1)
                # Skip weekends (5 = Saturday, 6 = Sunday)
                if self.symbol.endswith('.X') or self.symbol.endswith('-USD'):
                    # For crypto and certain assets, include all days
                    dates.append(current_date)
                    days_added += 1
                elif current_date.weekday() < 5:  # Monday to Friday
                    # For stocks, only include weekdays
                    dates.append(current_date)
                    days_added += 1
        
        predictive_df = pd.DataFrame({
            'open': predictive_data['open_prices'],
            'high': predictive_data['high_prices'],
            'low': predictive_data['low_prices'],
            'close': predictive_data['prices'],
            'type': ['predictive'] * len(predictive_data['prices'])
        }, index=dates)
        
        # Combine the DataFrames
        combined_df = pd.concat([historical_df, predictive_df])
        
        return combined_df
