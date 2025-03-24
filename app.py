import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from stock_analyzer import StockAnalyzer

# Page configuration
st.set_page_config(
    page_title="Stock Analyzer with Predictive Candles",
    page_icon="📈",
    layout="wide"
)

# App title and description
st.title("📊 Stock Analyzer with Predictive Candles")
st.markdown("""
This application provides real-time stock analysis with historical data visualization and predictive simulation.
Enter a stock symbol to see current metrics, historical performance, and customize your prediction timeframe.
""")

# Add a link to the portfolio analysis page
st.sidebar.markdown("""
### 📘 Naviga

[Analisi Titolo Singolo](/) | [**Nuovo!** Analisi Portafoglio eToro](/Portfolio_Analysis)
""")

# Input for stock symbol
stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, GOOGL)", "AAPL").upper()

# Prediction days selector
prediction_days = st.slider("Giorni di previsione", min_value=1, max_value=14, value=5, 
                           help="Seleziona il numero di giorni per cui vuoi prevedere l'andamento dell'azione")

# Information about trading days
st.info("""
**Nota sui giorni di trading**: Per le azioni, le previsioni considerano solo i giorni di mercato aperto 
(lunedì-venerdì). Per criptovalute e altri asset che operano 7 giorni su 7, verranno considerati tutti i giorni.
""")

# Analyze button
if st.button("Analyze Stock"):
    with st.spinner(f"Analyzing {stock_symbol}..."):
        try:
            # Initialize the stock analyzer
            analyzer = StockAnalyzer(stock_symbol)
            
            # Get real-time data
            real_time_data = analyzer.get_real_time_data()
            
            if real_time_data:
                # Create two columns for layout
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("📈 Current Stock Data")
                    
                    # Format the price change with appropriate color
                    price_change_pct = real_time_data['price_change_percentage']
                    change_color = "green" if price_change_pct >= 0 else "red"
                    change_symbol = "▲" if price_change_pct >= 0 else "▼"
                    
                    # Display current price and stats
                    st.markdown(f"### {stock_symbol} - {real_time_data['name']}")
                    st.markdown(f"💰 **Current Price:** ${real_time_data['price']:.2f}")
                    st.markdown(f"📊 **Change:** <span style='color:{change_color}'>{change_symbol} {abs(price_change_pct):.2f}%</span>", unsafe_allow_html=True)
                    st.markdown(f"📉 **Previous Close:** ${real_time_data['previous_close']:.2f}")
                    
                    st.subheader("🔮 Predictive Simulation")
                    
                    # Get and display predictive data with the user-selected number of days
                    predictive_data = analyzer.get_predictive_data(days=prediction_days)
                    
                    # Calculate the cumulative effect
                    cumulative_change = 100 * (1 + sum(predictive_data['percentage_changes']) / 100)
                    cumulative_color = "green" if cumulative_change > 100 else "red"
                    
                    st.markdown(f"### {prediction_days}-Day Prediction")
                    st.markdown(f"**Cumulative Effect:** <span style='color:{cumulative_color}'>{cumulative_change:.2f}%</span> of current price", unsafe_allow_html=True)
                    
                    # Create a table of daily predictions based on the selected number of days
                    pred_df = pd.DataFrame({
                        'Day': [f"Day {i+1}" for i in range(prediction_days)],
                        'Predicted Change': [f"{change:.2f}%" for change in predictive_data['percentage_changes']],
                        'Predicted Price': [f"${price:.2f}" for price in predictive_data['prices']]
                    })
                    
                    st.table(pred_df)
                
                with col2:
                    st.subheader("📊 Historical & Predictive Chart")
                    
                    # Get historical and combined data with the user-selected prediction days
                    historical_data = analyzer.get_historical_data()
                    combined_data = analyzer.combine_historical_and_predictive(prediction_days)
                    
                    # Get latest news
                    news_data = analyzer.get_news(limit=5)
                    
                    # Remove debug information that was used for troubleshooting
                    
                    # Create candlestick chart
                    fig = go.Figure()
                    
                    # Add historical candlesticks
                    fig.add_trace(go.Candlestick(
                        x=historical_data.index,
                        open=historical_data['open'],
                        high=historical_data['high'],
                        low=historical_data['low'],
                        close=historical_data['close'],
                        name="Historical",
                        increasing_line_color='green',
                        decreasing_line_color='red'
                    ))
                    
                    # Filter predictive data
                    predictive_df = combined_data[combined_data['type'] == 'predictive']
                    
                    # Add predictive candlesticks with different color
                    fig.add_trace(go.Candlestick(
                        x=predictive_df.index,
                        open=predictive_df['open'],
                        high=predictive_df['high'],
                        low=predictive_df['low'],
                        close=predictive_df['close'],
                        name="Predictive",
                        increasing_line_color='rgba(0, 128, 0, 0.7)',
                        decreasing_line_color='rgba(255, 0, 0, 0.7)'
                    ))
                    
                    # Add a vertical line to separate historical from predictive
                    # Convert to Python datetime to avoid pandas Timestamp issues
                    last_historical_date = historical_data.index[-1]
                    if isinstance(last_historical_date, pd.Timestamp):
                        # Using timestamp value avoids issues with Plotly/pandas compatibility
                        last_historical_date = last_historical_date.timestamp() * 1000  # Convert to milliseconds
                    
                    fig.add_vline(
                        x=last_historical_date, 
                        line_width=2, 
                        line_dash="dash", 
                        line_color="gray",
                        annotation_text="Prediction Start", 
                        annotation_position="top right"
                    )
                    
                    # Update layout for better visualization with dynamic prediction days
                    fig.update_layout(
                        title=f"{stock_symbol} - 30-Day History & {prediction_days}-Day Prediction",
                        xaxis_title="Date",
                        yaxis_title="Price (USD)",
                        height=600,
                        xaxis_rangeslider_visible=True,
                        legend_title="Data Type",
                        hovermode="x unified"
                    )
                    
                    # Display the interactive chart
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.caption("**Note:** Predicted values are simulations based on historical patterns and are not financial advice.")
                    
                    # Get predictive data
                    prediction_data = analyzer.get_predictive_data(days=prediction_days)
                    
                    # Get trend analysis
                    trend_data = analyzer.get_trend_analysis(days=prediction_days)
                    
                    # Display trend visualization section
                    st.subheader("📈 Analisi Predittiva delle Tendenze")
                    
                    # Create two columns for the trend visualization
                    trend_col1, trend_col2 = st.columns(2)
                    
                    with trend_col1:
                        # Display trend direction with an appropriate icon
                        direction_icon = "↗️" if trend_data['trend_direction'] == 'upward' else "↘️" if trend_data['trend_direction'] == 'downward' else "↔️"
                        direction_color = "green" if trend_data['trend_direction'] == 'upward' else "red" if trend_data['trend_direction'] == 'downward' else "gray"
                        
                        st.markdown(f"""
                        <h3 style='color:{direction_color};'>Direzione: {direction_icon} {trend_data['trend_direction'].title()}</h3>
                        <p>Forza della tendenza: {trend_data['strength']:.1f}%</p>
                        """, unsafe_allow_html=True)
                        
                        # Display support and resistance levels
                        st.markdown(f"""
                        <div style='margin-top: 20px;'>
                            <p><strong>Livello di supporto:</strong> ${trend_data['support_level']:.2f}</p>
                            <p><strong>Livello di resistenza:</strong> ${trend_data['resistance_level']:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with trend_col2:
                        # Create a gauge chart for RSI
                        rsi = trend_data['momentum_indicators']['rsi']
                        
                        fig_rsi = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = rsi,
                            title = {'text': "RSI (Relative Strength Index)"},
                            gauge = {
                                'axis': {'range': [0, 100], 'tickwidth': 1},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 30], 'color': "red"},
                                    {'range': [30, 70], 'color': "yellow"},
                                    {'range': [70, 100], 'color': "green"}
                                ],
                                'threshold': {
                                    'line': {'color': "black", 'width': 4},
                                    'thickness': 0.75,
                                    'value': rsi
                                }
                            }
                        ))
                        
                        fig_rsi.update_layout(height=250)
                        st.plotly_chart(fig_rsi, use_container_width=True)
                        
                        # Interpretation of RSI
                        if rsi > 70:
                            st.info("RSI sopra 70 suggerisce una condizione di ipercomprato. Potrebbe verificarsi una correzione.")
                        elif rsi < 30:
                            st.info("RSI sotto 30 suggerisce una condizione di ipervenduto. Potrebbe verificarsi un rimbalzo.")
                        else:
                            st.info("RSI tra 30 e 70 suggerisce condizioni di mercato normali.")
                    
                    # Line chart showing predicted price movement with support and resistance
                    hist_data = historical_data.tail(10)['close'].to_list()
                    hist_dates = [d.strftime('%m-%d') if isinstance(d, pd.Timestamp) else d.strftime('%m-%d') for d in historical_data.tail(10).index]
                    
                    pred_data = prediction_data['prices']
                    
                    # Get predicted dates (excluding weekends for stocks)
                    pred_dates = []
                    last_date = historical_data.index[-1]
                    if isinstance(last_date, pd.Timestamp):
                        last_date = last_date.to_pydatetime()
                        
                    current_date = last_date
                    days_added = 0
                    
                    while days_added < len(pred_data):
                        current_date = current_date + timedelta(days=1)
                        if stock_symbol.endswith('.X') or stock_symbol.endswith('-USD'):
                            # For crypto and certain assets, include all days
                            pred_dates.append(current_date.strftime('%m-%d'))
                            days_added += 1
                        elif current_date.weekday() < 5:  # Monday to Friday
                            # For stocks, only include weekdays
                            pred_dates.append(current_date.strftime('%m-%d'))
                            days_added += 1
                    
                    # Create trend chart
                    fig_trend = go.Figure()
                    
                    # Add historical prices
                    fig_trend.add_trace(go.Scatter(
                        x=hist_dates,
                        y=hist_data,
                        name="Storico",
                        line=dict(color='blue', width=2)
                    ))
                    
                    # Add predicted prices
                    fig_trend.add_trace(go.Scatter(
                        x=pred_dates,
                        y=pred_data,
                        name="Previsione",
                        line=dict(color='orange', width=2, dash='dash')
                    ))
                    
                    # Add support level
                    fig_trend.add_trace(go.Scatter(
                        x=pred_dates,
                        y=[trend_data['support_level']] * len(pred_dates),
                        name="Supporto",
                        line=dict(color='green', width=1, dash='dot')
                    ))
                    
                    # Add resistance level
                    fig_trend.add_trace(go.Scatter(
                        x=pred_dates,
                        y=[trend_data['resistance_level']] * len(pred_dates),
                        name="Resistenza",
                        line=dict(color='red', width=1, dash='dot')
                    ))
                    
                    # Update layout
                    fig_trend.update_layout(
                        title=f"Previsione tendenza per {stock_symbol} nei prossimi {prediction_days} giorni",
                        xaxis_title="Data",
                        yaxis_title="Prezzo ($)",
                        hovermode="x unified",
                        height=400
                    )
                    
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # Display news section
                    st.subheader("📰 Notizie rilevanti")
                    
                    if news_data and len(news_data) > 0:
                        for i, news in enumerate(news_data):
                            with st.expander(f"{i+1}. {news['title']} ({news['date']})"):
                                st.markdown(f"**Fonte:** {news['source']}")
                                if news.get('text'):
                                    st.markdown(news['text'][:500] + "..." if len(news['text']) > 500 else news['text'])
                                st.markdown(f"[Leggi l'articolo completo]({news['url']})")
                    else:
                        st.info(f"Nessuna notizia trovata per {stock_symbol}")
            else:
                st.error(f"Could not retrieve data for {stock_symbol}. Please check if the symbol is correct.")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("Try another stock symbol or check your internet connection.")

# Add disclaimer at the bottom
st.markdown("---")
st.caption("""
**Disclaimer:** The information provided by this tool is for informational purposes only and does not constitute financial advice. 
Predictive values are simulations based on historical patterns and should not be used for investment decisions.
""")
