import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import io
import requests
from bs4 import BeautifulSoup
from stock_analyzer import StockAnalyzer

class PortfolioAnalyzer:
    """
    Class for analyzing a portfolio of stocks, calculating aggregate metrics,
    and generating portfolio-level predictions.
    """
    
    def __init__(self, portfolio_data=None):
        """
        Initialize the PortfolioAnalyzer with portfolio data.
        
        Args:
            portfolio_data (dict): Dictionary with stock symbols as keys and their weights/quantities as values
        """
        self.portfolio_data = portfolio_data if portfolio_data else {}
        self.stock_analyzers = {}
        self.portfolio_summary = None
        
    def parse_etoro_portfolio(self, etoro_url):
        """
        Parse portfolio data from eToro public portfolio URL.
        
        Args:
            etoro_url (str): URL of the eToro public portfolio
            
        Returns:
            dict: Dictionary with stock symbols as keys and their quantities as values
            or tuple(None, error_message) in case of error
        """
        try:
            if not etoro_url.startswith("https://www.etoro.com/people/"):
                return None, "L'URL deve iniziare con 'https://www.etoro.com/people/'"
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(etoro_url, headers=headers, timeout=10)
            
            if response.status_code == 404:
                return None, "Portfolio non trovato. Verifica che l'URL sia corretto."
            elif response.status_code == 403:
                return None, "Accesso negato. Verifica che il portfolio sia pubblico."
            elif response.status_code != 200:
                return None, f"Errore nel caricamento (Status code: {response.status_code})"
                
            soup = BeautifulSoup(response.text, 'html.parser')
            portfolio = {}
            
            # Look for portfolio elements in the page
            portfolio_elements = soup.find_all('a', class_='user-portfolio-card-table-asset-cell')
            
            # Extract stock data
            for element in portfolio_elements:
                try:
                    symbol = element.text.strip().upper()
                    if symbol and len(symbol) > 0:
                        portfolio[symbol] = {
                            'quantity': 1.0,
                            'position_type': 'Long'
                        }
                except Exception as e:
                    print(f"Error parsing element: {str(e)}")
            
            return portfolio
            
        except Exception as e:
            print(f"Error parsing eToro portfolio: {str(e)}")
            return None
        
    def parse_portfolio_csv(self, csv_content):
        """
        Parse a portfolio CSV file from any source.
        
        Args:
            csv_content (str): CSV content as string
            
        Returns:
            dict: Dictionary with stock symbols as keys and their quantities as values
        """
        portfolio = {}
        
        # Use StringIO to parse the CSV content
        f = io.StringIO(csv_content)
        
        try:
            # Read CSV and detect format
            reader = csv.reader(f)
            headers = [h.strip().lower().strip('"') for h in next(reader)]
            headers = [h.split(',')[0] if ',' in h else h for h in headers]  # Handle merged cells
            
            # Find columns for symbol and quantity/units
            symbol_col = None
            quantity_col = None
            
            # Common column names in various portfolio exports
            possible_symbol_cols = ['symbol', 'ticker', 'stock', 'asset', 'instrument', 'security', 'position id']
            possible_quantity_cols = ['units', 'amount', 'quantity', 'shares', 'position units', 'holdings', 'position']

            # Try to find exact matches first
            symbol_col = next((i for i, h in enumerate(headers) if h in possible_symbol_cols), None)
            quantity_col = next((i for i, h in enumerate(headers) if h in possible_quantity_cols), None)

            # If not found, try partial matches
            if symbol_col is None:
                symbol_col = next((i for i, h in enumerate(headers) if any(col in h for col in possible_symbol_cols)), 0)
            if quantity_col is None:
                quantity_col = next((i for i, h in enumerate(headers) if any(col in h for col in possible_quantity_cols)), 1)
            
            for i, header in enumerate(headers):
                if any(possible_symbol in header for possible_symbol in possible_symbol_cols):
                    symbol_col = i
                if any(possible_quantity in header for possible_quantity in possible_quantity_cols):
                    quantity_col = i
            
            # If we couldn't identify the columns, use default positions
            if symbol_col is None:
                symbol_col = 0  # Assume first column is symbol
            if quantity_col is None:
                quantity_col = 1  # Assume second column is quantity
            
            # Read the portfolio data
            for row in reader:
                if len(row) > max(symbol_col, quantity_col):
                    # Clean the row data and handle merged cells
                    cleaned_row = [cell.strip().strip('"') for cell in row]
                    cleaned_row = [cell.split(',')[0] if ',' in cell else cell for cell in cleaned_row]
                    
                    if not cleaned_row[symbol_col]:  # Skip empty rows
                        continue
                        
                    symbol = cleaned_row[symbol_col].strip().upper()
                    
                    # Clean up the symbol to ensure compatibility
                    # Replace common eToro suffixes with standard ticker symbols
                    if '.' in symbol:
                        symbol = symbol.split('.')[0]
                    if '-' in symbol and not symbol.endswith('-USD'):  # Preserve crypto symbols
                        symbol = symbol.split('-')[0]
                    
                    # Try to convert quantity to float, default to 1 if not possible
                    try:
                        quantity = float(row[quantity_col].replace(',', ''))
                    except (ValueError, TypeError):
                        quantity = 1
                    
                    # Only add if the symbol seems valid
                    # Check for position type (Long/Short)
                    position_type = 'Long'  # Default to Long
                    if len(cleaned_row) > 5:  # If we have a position column
                        position = cleaned_row[5].strip().upper()
                        position_type = 'Short' if 'SHORT' in position else 'Long'
                    
                    if symbol and len(symbol) > 0 and not symbol.isdigit():
                        if symbol in portfolio:
                            portfolio[symbol] += quantity
                        else:
                            portfolio[symbol] = quantity
            
            # Remove any potential non-standard symbols
            cleaned_portfolio = {}
            for symbol, quantity in portfolio.items():
                # Basic validation: symbols are typically 1-5 letters (sometimes with a suffix)
                if 1 <= len(symbol) <= 10 and not any(c.isdigit() for c in symbol[:2]):
                    cleaned_portfolio[symbol] = quantity
            
            return cleaned_portfolio
            
        except Exception as e:
            print(f"Error parsing eToro CSV: {str(e)}")
            return {}
    
    def load_portfolio(self, portfolio_data):
        """
        Load a portfolio for analysis.
        
        Args:
            portfolio_data (dict): Dictionary with stock symbols as keys and their weights/quantities as values
        """
        self.portfolio_data = portfolio_data
        self.stock_analyzers = {}
        
    def analyze_portfolio(self, prediction_days=5):
        """
        Analyze all stocks in the portfolio and generate portfolio-level metrics.
        
        Args:
            prediction_days (int): Number of days to predict
            
        Returns:
            dict: Portfolio analysis summary
        """
        if not self.portfolio_data:
            return None
            
        # Initialize analyzers for each stock in the portfolio
        for symbol in self.portfolio_data.keys():
            try:
                self.stock_analyzers[symbol] = StockAnalyzer(symbol)
            except Exception as e:
                print(f"Error initializing analyzer for {symbol}: {str(e)}")
        
        # Collect the analysis results for each stock
        stock_analysis = {}
        total_value = 0
        total_prediction = 0
        portfolio_trends = {"upward": 0, "downward": 0, "sideways": 0, "unknown": 0}
        
        for symbol, quantity in self.portfolio_data.items():
            if symbol in self.stock_analyzers:
                analyzer = self.stock_analyzers[symbol]
                
                try:
                    # Get real-time data
                    real_time_data = analyzer.get_real_time_data()
                    
                    if real_time_data:
                        current_price = real_time_data['price']
                        quantity = portfolio_data[symbol]['quantity']
                        position_type = portfolio_data[symbol]['position_type']
                        
                        # Per le posizioni short, il profitto è inverso
                        current_value = current_price * quantity
                        if position_type == 'Short':
                            current_value = -current_value  # Il valore è negativo per gli short
                        
                        total_value += abs(current_value)  # Usiamo il valore assoluto per il totale
                        
                        # Get trend analysis
                        trend_data = analyzer.get_trend_analysis(days=prediction_days)
                        portfolio_trends[trend_data['trend_direction']] += 1
                        
                        # Get predictive data
                        predictive_data = analyzer.get_predictive_data(days=prediction_days)
                        if predictive_data and len(predictive_data['prices']) > 0:
                            final_predicted_price = predictive_data['prices'][-1]
                            predicted_value = final_predicted_price * quantity
                            total_prediction += predicted_value
                            
                            # Calculate percentage change
                            predicted_change = ((final_predicted_price - current_price) / current_price) * 100
                        else:
                            final_predicted_price = current_price
                            predicted_value = current_value
                            predicted_change = 0
                            
                        # Store the analysis
                        stock_analysis[symbol] = {
                            'name': real_time_data.get('name', symbol),
                            'quantity': quantity,
                            'current_price': current_price,
                            'current_value': current_value,
                            'predicted_price': final_predicted_price,
                            'predicted_value': predicted_value,
                            'predicted_change': predicted_change,
                            'trend': trend_data['trend_direction'],
                            'trend_strength': trend_data['strength'],
                            'rsi': trend_data['momentum_indicators']['rsi']
                        }
                except Exception as e:
                    print(f"Error analyzing {symbol}: {str(e)}")
        
        # Calculate portfolio-level metrics
        portfolio_prediction_change = ((total_prediction - total_value) / total_value) * 100 if total_value > 0 else 0
        
        # Determine overall portfolio trend
        if portfolio_trends["upward"] > portfolio_trends["downward"] + portfolio_trends["sideways"]:
            overall_trend = "upward"
        elif portfolio_trends["downward"] > portfolio_trends["upward"] + portfolio_trends["sideways"]:
            overall_trend = "downward"
        else:
            overall_trend = "sideways"
            
        # Calculate the percentage of stocks in each trend
        total_stocks = sum(portfolio_trends.values())
        trend_percentages = {
            trend: (count / total_stocks) * 100 if total_stocks > 0 else 0 
            for trend, count in portfolio_trends.items()
        }
        
        # Prepare the portfolio summary
        self.portfolio_summary = {
            'total_value': total_value,
            'total_prediction': total_prediction,
            'portfolio_prediction_change': portfolio_prediction_change,
            'overall_trend': overall_trend,
            'trend_percentages': trend_percentages,
            'stocks': stock_analysis
        }
        
        return self.portfolio_summary
    
    def get_portfolio_composition(self):
        """
        Get the composition of the portfolio for visualization.
        
        Returns:
            pd.DataFrame: DataFrame with portfolio composition data
        """
        if not self.portfolio_summary:
            return pd.DataFrame()
            
        # Create a DataFrame with portfolio composition data
        data = []
        for symbol, analysis in self.portfolio_summary['stocks'].items():
            data.append({
                'Symbol': symbol,
                'Name': analysis['name'],
                'Current Value': analysis['current_value'],
                'Percentage': (analysis['current_value'] / self.portfolio_summary['total_value']) * 100
            })
            
        df = pd.DataFrame(data)
        return df.sort_values('Current Value', ascending=False)
    
    def get_trend_distribution(self):
        """
        Get the distribution of trends in the portfolio.
        
        Returns:
            dict: Dictionary with trend distribution data
        """
        if not self.portfolio_summary:
            return {'labels': [], 'values': []}
            
        trend_counts = {
            'labels': ['Upward', 'Sideways', 'Downward'],
            'values': [
                self.portfolio_summary['trend_percentages']['upward'],
                self.portfolio_summary['trend_percentages']['sideways'],
                self.portfolio_summary['trend_percentages']['downward']
            ]
        }
        
        return trend_counts
    
    def get_stocks_performance_comparison(self):
        """
        Get a comparison of the performance of stocks in the portfolio.
        
        Returns:
            pd.DataFrame: DataFrame with stock performance data
        """
        if not self.portfolio_summary:
            return pd.DataFrame()
            
        # Create a DataFrame with stock performance data
        data = []
        for symbol, analysis in self.portfolio_summary['stocks'].items():
            data.append({
                'Symbol': symbol,
                'Name': analysis['name'],
                'Current Price': analysis['current_price'],
                'Predicted Price': analysis['predicted_price'],
                'Predicted Change %': analysis['predicted_change'],
                'Trend': analysis['trend'],
                'RSI': analysis['rsi']
            })
            
        df = pd.DataFrame(data)
        return df.sort_values('Predicted Change %', ascending=False)