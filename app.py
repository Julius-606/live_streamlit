import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# --- CONFIGURATION ---
ST_PAGE_TITLE = "Darwin 2.0 🧬 | Nursery Monitor"
DATA_FILE = 'Brain Nursery - Sheet4.csv'  # Make sure this matches your bot's output filename
REFRESH_RATE = 30  # Refresh every 30 seconds

st.set_page_config(page_title=ST_PAGE_TITLE, layout="wide", page_icon="🧬")

# --- DATA LOADER ---
def get_data():
    try:
        df = pd.read_csv(DATA_FILE)
        
        # Clean & Convert Data
        # Ensure date format matches your CSV logs
        df['Open Time'] = pd.to_datetime(df['Open Time'])
        
        # specific handling for FRIDAY_CLOSE or other non-numeric PnL if strictly needed
        df['PnL'] = pd.to_numeric(df['PnL'], errors='coerce').fillna(0)
        df['Running'] = pd.to_numeric(df['Running'], errors='coerce')
        
        return df
    except FileNotFoundError:
        st.error(f"⚠️ Waiting for data... File `{DATA_FILE}` not found yet.")
        return pd.DataFrame()

# --- MAIN DASHBOARD ---
st.title("🧬 Darwin 2.0: Construction to Live")
st.caption("Tracking the 'Small Sure-Bet' Compounding Strategy")

# Container for auto-refreshing content
placeholder = st.empty()

while True:
    df = get_data()
    
    if not df.empty:
        with placeholder.container():
            # 1. TOP METRICS
            # Filter actual trades (exclude Friday pauses for win-rate calc)
            real_trades = df[df['Strategy'] == 'Darwin_2.0'] # Filter only actual strategy rows
            closed_trades = real_trades[real_trades['PnL'] != 0] 
            
            total_pnl = df['Running'].iloc[-1]
            total_trades = len(closed_trades)
            
            # Win Rate Calculation
            wins = closed_trades[closed_trades['PnL'] > 0]
            losses = closed_trades[closed_trades['PnL'] < 0]
            win_rate = (len(wins) / len(closed_trades) * 100) if len(closed_trades) > 0 else 0
            
            # Profit Factor
            gross_profit = wins['PnL'].sum()
            gross_loss = abs(losses['PnL'].sum())
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

            # Metric Cards
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("💰 Net Profit", f"${total_pnl:.2f}", delta_color="normal")
            kpi2.metric("🎯 Win Rate", f"{win_rate:.1f}%")
            kpi3.metric("⚖️ Profit Factor", f"{profit_factor:.2f}")
            kpi4.metric("📊 Total Trades", total_trades)

            st.markdown("---")

            # 2. THE COMPOUNDING CURVE (Equity)
            # This is the most important chart for your goal
            st.subheader("📈 The Compounding Curve")
            
            # Create a specialized area chart to show growth
            fig_equity = px.area(df, x='Open Time', y='Running', 
                                 title='Account Growth Over Time',
                                 labels={'Running': 'Balance ($)', 'Open Time': 'Time'})
            
            fig_equity.update_traces(line_color='#00FF7F', fill_color='rgba(0, 255, 127, 0.2)')
            fig_equity.update_layout(height=400, xaxis_title="", yaxis_title="Profit ($)")
            
            st.plotly_chart(fig_equity, use_container_width=True)

            # 3. WIN vs LOSS ANALYSIS
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Win/Loss Distribution")
                # Histogram to see if wins are actually bigger than losses
                fig_hist = px.histogram(closed_trades, x='PnL', nbins=20, 
                                      color_discrete_sequence=['#636EFA'],
                                      title="Trade PnL Frequency")
                st.plotly_chart(fig_hist, use_container_width=True)
                
            with col_right:
                st.subheader("Recent Activity")
                # Show last 5 trades nicely
                recent = df[['Symbol', 'Type', 'PnL', 'Reason']].tail(8).iloc[::-1] # Reverse to show newest first
                st.dataframe(recent, use_container_width=True)

    # Auto-refresh logic
    time.sleep(REFRESH_RATE)
