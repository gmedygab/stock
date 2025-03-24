import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class PredictiveModel:
    """
    Class for generating predictive stock price models based on historical data.
    """
    
    def __init__(self):
        """Initialize the PredictiveModel."""
        pass
    
    def analyze_trend(self, historical_data, prediction_data):
        """
        Analyze the trend of the stock based on historical and predicted data.
        
        Args:
            historical_data (pandas.DataFrame): Historical OHLC data
            prediction_data (dict): Predicted price data
            
        Returns:
            dict: Dictionary containing trend analysis results including:
                - trend_direction: 'upward', 'downward', or 'sideways'
                - strength: value from 0-100 indicating trend strength
                - support_level: estimated support price
                - resistance_level: estimated resistance price
                - momentum_indicators: additional momentum metrics
        """
        if historical_data is None or historical_data.empty or not prediction_data['prices']:
            return {
                'trend_direction': 'unknown',
                'strength': 0,
                'support_level': 0,
                'resistance_level': 0,
                'momentum_indicators': {'rsi': 50, 'macd': 0}
            }
            
        # Get recent closing prices
        recent_closes = historical_data['close'].tail(20).values
        predicted_closes = np.array(prediction_data['prices'])
        
        # Calculate overall trend direction based on linear regression
        x_hist = np.arange(len(recent_closes))
        x_pred = np.arange(len(predicted_closes))
        
        # Historical slope
        hist_slope, _ = np.polyfit(x_hist, recent_closes, 1)
        
        # Predicted slope
        pred_slope, _ = np.polyfit(x_pred, predicted_closes, 1)
        
        # Determine trend direction
        if pred_slope > 0.001:
            trend_direction = 'upward'
        elif pred_slope < -0.001:
            trend_direction = 'downward'
        else:
            trend_direction = 'sideways'
            
        # Calculate trend strength (0-100)
        # Normalize based on historical volatility
        hist_volatility = np.std(historical_data['close'].pct_change().dropna())
        norm_pred_slope = abs(pred_slope) / (hist_volatility * 10)  # Normalize to 0-1 range
        strength = min(100, max(0, norm_pred_slope * 100))  # Convert to 0-100
        
        # Find support and resistance levels
        support_level = min(np.min(recent_closes), np.min(predicted_closes)) * 0.98
        resistance_level = max(np.max(recent_closes), np.max(predicted_closes)) * 1.02
        
        # Calculate basic momentum indicators
        # Simple RSI calculation
        diff = np.diff(np.append(recent_closes, predicted_closes))
        gains = np.sum(diff[diff > 0])
        losses = abs(np.sum(diff[diff < 0]))
        
        if losses == 0:
            rsi = 100
        else:
            rs = gains / losses
            rsi = 100 - (100 / (1 + rs))
            
        # Simple MACD calculation (difference between fast and slow EMA)
        ema12 = historical_data['close'].ewm(span=12).mean().iloc[-1]
        ema26 = historical_data['close'].ewm(span=26).mean().iloc[-1]
        macd = ema12 - ema26
        
        return {
            'trend_direction': trend_direction,
            'strength': strength,
            'support_level': support_level,
            'resistance_level': resistance_level,
            'momentum_indicators': {
                'rsi': rsi,
                'macd': macd
            }
        }
    
    def generate_predictions(self, historical_data, current_price, days=5):
        """
        Generate predictive stock prices for the specified number of days.
        
        Args:
            historical_data (pandas.DataFrame): Historical OHLC data
            current_price (float): Current stock price
            days (int): Number of days to predict
            
        Returns:
            dict: Dictionary containing predicted prices and percentage changes
        """
        if historical_data is None or historical_data.empty:
            return {
                'prices': [],
                'percentage_changes': [],
                'open_prices': [],
                'high_prices': [],
                'low_prices': []
            }
        
        # Calculate daily returns and volatility from historical data
        historical_returns = historical_data['close'].pct_change().dropna()
        mean_return = historical_returns.mean()
        volatility = historical_returns.std()
        
        # Calculate high-low spread ratio for the historical data
        high_low_ratio = (historical_data['high'] - historical_data['low']) / historical_data['close']
        mean_high_low_ratio = high_low_ratio.mean()
        
        # Calculate open-close relationship
        open_close_diff = (historical_data['open'] - historical_data['close'].shift(1)) / historical_data['close'].shift(1)
        mean_open_close_diff = open_close_diff.dropna().mean()
        
        # Generate future prices with a bit of randomness but based on historical patterns
        predicted_prices = []
        predicted_percentage_changes = []
        predicted_open_prices = []
        predicted_high_prices = []
        predicted_low_prices = []
        
        last_price = current_price
        
        for _ in range(days):
            # Add some randomness to the daily return but keep it within a realistic range
            random_factor = np.random.normal(0, 1)
            daily_return = mean_return + (random_factor * volatility)
            
            # Calculate percentage change for the day
            percentage_change = daily_return * 100
            predicted_percentage_changes.append(percentage_change)
            
            # Calculate new price
            new_price = last_price * (1 + daily_return)
            predicted_prices.append(new_price)
            
            # Calculate open price based on previous close
            open_price = last_price * (1 + mean_open_close_diff + np.random.normal(0, volatility/2))
            predicted_open_prices.append(open_price)
            
            # Calculate high and low prices
            price_range = new_price * mean_high_low_ratio * (0.8 + 0.4 * np.random.random())
            high_price = max(new_price, open_price) + (price_range / 2)
            low_price = min(new_price, open_price) - (price_range / 2)
            
            predicted_high_prices.append(high_price)
            predicted_low_prices.append(low_price)
            
            # Update last price for next iteration
            last_price = new_price
        
        return {
            'prices': predicted_prices,
            'percentage_changes': predicted_percentage_changes,
            'open_prices': predicted_open_prices,
            'high_prices': predicted_high_prices,
            'low_prices': predicted_low_prices
        }
