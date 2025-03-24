import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import os

class DataFetcher:
    """
    Class responsible for fetching stock data from various sources
    including Financial Modeling Prep API and Yahoo Finance.
    """
    
    def __init__(self):
        """Initialize the DataFetcher with API keys."""
        # Get the API key from environment variables
        self.fmp_api_key = os.getenv("FMP_API_KEY", "")
        
    def fetch_real_time_data(self, symbol):
        """
        Fetch real-time stock data using FMP API with Yahoo Finance as fallback.
        
        Args:
            symbol (str): Stock symbol to fetch data for
            
        Returns:
            dict: Dictionary containing real-time stock data
        """
        # Try Financial Modeling Prep first
        if self.fmp_api_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={self.fmp_api_key}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data and len(data) > 0:
                        stock_data = data[0]
                        return {
                            'name': stock_data.get('name', ''),
                            'price': stock_data.get('price', 0.0),
                            'price_change_percentage': stock_data.get('changesPercentage', 0.0),
                            'previous_close': stock_data.get('previousClose', 0.0)
                        }
            except Exception as e:
                print(f"Error fetching from FMP API: {e}")
        
        # Fallback to Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price_history = ticker.history(period="2d")
            
            # Calculate price change percentage
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            previous_close = info.get('previousClose', 0.0)
            
            if current_price and previous_close:
                price_change_percentage = ((current_price - previous_close) / previous_close) * 100
            else:
                price_change_percentage = 0.0
            
            return {
                'name': info.get('shortName', ''),
                'price': current_price,
                'price_change_percentage': price_change_percentage,
                'previous_close': previous_close
            }
        except Exception as e:
            print(f"Error fetching from Yahoo Finance: {e}")
            return None
            
    def fetch_historical_data(self, symbol, days=30):
        """
        Fetch historical OHLC data for the specified symbol.
        
        Args:
            symbol (str): Stock symbol to fetch data for
            days (int): Number of days of historical data to retrieve
            
        Returns:
            pandas.DataFrame: DataFrame with historical OHLC data
        """
        # Try Financial Modeling Prep first if API key is available
        if self.fmp_api_key:
            try:
                # Calculate the start date
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=days+5)).strftime('%Y-%m-%d')  # Add buffer days
                
                url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={start_date}&to={end_date}&apikey={self.fmp_api_key}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'historical' in data and len(data['historical']) > 0:
                        # Convert to DataFrame
                        df = pd.DataFrame(data['historical'])
                        
                        # Rename columns to match expected format
                        df = df.rename(columns={
                            'date': 'date',
                            'open': 'open',
                            'high': 'high',
                            'low': 'low',
                            'close': 'close',
                            'volume': 'volume'
                        })
                        
                        # Convert date to datetime and set as index
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')
                        
                        # Sort by date (newest last)
                        df = df.sort_index()
                        
                        # Limit to the requested number of days
                        if len(df) > days:
                            df = df.iloc[-days:]
                            
                        return df
            except Exception as e:
                print(f"Error fetching historical data from FMP API: {e}")
        
        # Fallback to Yahoo Finance
        try:
            # Calculate the start date (add buffer days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days+5)  # Add buffer days for weekends and holidays
            
            # Fetch data from Yahoo Finance
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            # Process the DataFrame
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df.columns = df.columns.str.lower()
            
            # Limit to the requested number of days
            if len(df) > days:
                df = df.iloc[-days:]
                
            return df
        except Exception as e:
            print(f"Error fetching historical data from Yahoo Finance: {e}")
            return pd.DataFrame()
            
    def fetch_news(self, symbol, limit=5):
        """
        Fetch latest news for the specified stock symbol.
        
        Args:
            symbol (str): Stock symbol to fetch news for
            limit (int): Maximum number of news items to retrieve
            
        Returns:
            list: List of news articles with title, date, and URL
        """
        try:
            # Use Yahoo Finance API for news, which is more widely available
            ticker = yf.Ticker(symbol)
            news_list = []
            
            # Get news from Yahoo Finance
            news_data = ticker.news
            
            if news_data:
                for article in news_data[:limit]:  # Limit number of articles
                    # Format date
                    if 'providerPublishTime' in article:
                        published_date = datetime.fromtimestamp(article['providerPublishTime'])
                        formatted_date = published_date.strftime('%Y-%m-%d')
                    else:
                        formatted_date = "N/A"
                    
                    news_list.append({
                        'title': article.get('title', 'No title available'),
                        'date': formatted_date,
                        'url': article.get('link', '#'),
                        'source': article.get('publisher', 'Yahoo Finance'),
                        'text': article.get('summary', 'No summary available')
                    })
                
                return news_list
            
            return []
            
        except Exception as e:
            print(f"Error fetching news data: {str(e)}")
            return []
