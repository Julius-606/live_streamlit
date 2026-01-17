import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- 🛠️ CONFIGURATION ZONE 🛠️ ---
# 1. Grab the long string between /d/ and /edit in your URL
SHEET_ID = "YOUR_SHEET_ID_GOES_HERE" 

# 2. Grab the number after 'gid=' in your URL (Sheet4's specific ID)
SHEET_GID = "0" # Change this! (e.g., '123456789')

# 3. Refresh Rate (60s is the sweet spot)
REFRESH_RATE = 60

# Construct the magic URL
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

st.set_page_config(page_title="Darwin 2.0 🧬 | Cloud Monitor", layout="wide", page_icon="🧬")

# --- DATA LOADER (CLOUD EDITION) ☁️ ---
# We don't cache this strictly because we want live updates in the loop
def get_data():
    try:
        # Read directly from the Google cloud
        df = pd.read_csv(CSV_URL)
        
        # Cleanups - similar to before
        if 'Open Time' in df.columns:
            df['Open Time'] = pd.to_datetime(df['Open Time'])
        
        # Numeric conversion for safety
        cols_to_numeric = ['PnL', 'Running']
        for col in cols_to_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        # If it fails, it's usually a permission thing or wrong ID
        return None

# --- MAIN DASHBOARD ---
st.title("🧬 Darwin 2.0: Live Cloud Link")
st.caption(f"Tracking Sheet4 via Google Cloud • Refreshing every {REFRESH_RATE}s")

# Container for auto-refreshing content
placeholder = st.empty()

while True:
    df = get_data()
    
    if df is not None and not df.empty:
        with placeholder.container():
            # 1. TOP METRICS
            # Filter actual trades
            # Adjust 'Strategy' column name if it varies in your live sheet
            if 'Strategy' in df.columns:
                real_trades = df[df['Strategy'] == 'Darwin_2.0']
            else:
                real_trades = df # Fallback if column missing

            closed_trades = real_trades[real_trades['PnL'] != 0] 
            
            total_pnl = df['Running'].iloc[-1]
            total_trades = len(closed_trades)
            
            # Win Rate Calculation
            wins = closed_trades[closed_trades['PnL'] > 0]
            losses = closed_trades[closed_trades['PnL'] < 0]
            
            if len(closed_trades) > 0:
                win_rate = (len(wins) / len(closed_trades) * 100)
            else:
                win_rate = 0
            
            # Profit Factor
            gross_profit = wins['PnL'].sum()
            gross_loss = abs(losses['PnL'].sum())
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

            # Metric Cards
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("💰 Net Profit", f"${total_pnl:.2f}")
            kpi2.metric("🎯 Win Rate", f"{win_rate:.1f}%")
            kpi3.metric("⚖️ Profit Factor", f"{profit_factor:.2f}")
            kpi4.metric("📊 Total Trades", total_trades)

            st.markdown("---")

            # 2. THE COMPOUNDING CURVE
            col_chart, col_recent = st.columns([2, 1])
            
            with col_chart:
                st.subheader("📈 Account Growth")
                if 'Open Time' in df.columns and 'Running' in df.columns:
                    fig_equity = px.area(df, x='Open Time', y='Running', 
                                         title='Cumulative PnL',
                                         labels={'Running': 'Balance ($)'})
                    fig_equity.update_traces(line_color='#00FF7F', fill_color='rgba(0, 255, 127, 0.1)')
                    st.plotly_chart(fig_equity, use_container_width=True)
                else:
                    st.warning("Waiting for more data points...")

            with col_recent:
                st.subheader("📋 Last 5 Trades")
                cols_to_show = ['Pair', 'Type', 'PnL', 'Reason'] # Adjusted based on your CSV headers
                # Check if columns exist before showing
                available_cols = [c for c in cols_to_show if c in df.columns]
                
                if available_cols:
                    recent = df[available_cols].tail(5).iloc[::-1]
                    st.dataframe(recent, use_container_width=True, hide_index=True)
    
    elif df is None:
        with placeholder.container():
            st.error("🚫 Connection Error! Double check your SHEET_ID and make sure the sheet is Public (Viewer).")
            st.code(f"Current URL being tried:\n{CSV_URL}")
            
    time.sleep(REFRESH_RATE)
