import streamlit as st
import pandas as pd
import plotly.express as px
import time

# --- 🛠️ CONFIGURATION ZONE 🛠️ ---
st.set_page_config(page_title="Darwin 2.0 🧬 | Live Monitor", layout="wide", page_icon="🧬")

# Your Sheet ID from the URL 🔒
SHEET_ID = "1v_5DVdLPntHfPXjHSKK605f5l0m0F4LOTXTsXm1HbIo"

# 🗂️ SHEET OPTIONS (Add your GIDs here)
SHEET_OPTIONS = {
    "Darwin (Sheet4)": "420875998",
    "Goldie Locks(Sheet5)": "1687533",  # 👈 Replace with real GID for Sheet5
    "Sheet6 (YOLO Account)": "987654321"   # 👈 Add as many as you want
}

# How often to check for new trades (in seconds)
REFRESH_RATE = 60

# --- 🎨 SIDEBAR SETUP ---
with st.sidebar:
    st.title("🧬 Control Panel")
    st.markdown("Select your trading journal tab below.")
    
    # The Dropdown
    selected_sheet_name = st.selectbox("Select Sheet Tab", list(SHEET_OPTIONS.keys()))
    
    # Get the GID based on selection
    selected_gid = SHEET_OPTIONS[selected_sheet_name]
    
    st.divider()
    st.caption(f"Currently monitoring: **{selected_sheet_name}**")
    st.caption(f"Refresh Rate: **{REFRESH_RATE}s**")
    
    if st.button("Force Refresh 🔄"):
        st.rerun()

# Construct the URL dynamically based on sidebar selection
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={selected_gid}"

# --- DATA LOADER ---
@st.cache_data(ttl=REFRESH_RATE)
def get_data(url):
    try:
        # Pulling fresh data straight from the cloud ☁️
        df = pd.read_csv(url)
        
        # Data Hygiene 🧼
        if 'Open Time' in df.columns:
            df['Open Time'] = pd.to_datetime(df['Open Time'])
        
        # Ensure numbers are numbers (handling any messy Excel formatting)
        cols_to_numeric = ['PnL', 'Running', 'Balance']
        for col in cols_to_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        return None

# --- MAIN DASHBOARD ---
st.title(f"🧬 Darwin 2.0: {selected_sheet_name}")
st.markdown(f"**Status:** `ONLINE` 🟢 | **Source:** `{selected_sheet_name}`")

# Fetch Data
df = get_data(CSV_URL)

if df is not None and not df.empty:
    # --- 1. THE METRICS ---
    # Filtering for 'Darwin_2.0' to ignore any manual noise
    if 'Strategy' in df.columns:
        df_strat = df[df['Strategy'] == 'Darwin_2.0']
    else:
        df_strat = df

    # Filter closed trades (PnL not 0)
    closed = df_strat[df_strat['PnL'] != 0]
    
    # Key Stats
    total_profit = df['Running'].iloc[-1] if 'Running' in df.columns else 0.0
    total_trades = len(closed)
    
    # Win Rate & Profit Factor Logic
    wins = closed[closed['PnL'] > 0]
    losses = closed[closed['PnL'] < 0]
    
    win_rate = (len(wins) / len(closed) * 100) if len(closed) > 0 else 0.0
    
    gross_win = wins['PnL'].sum()
    gross_loss = abs(losses['PnL'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else 0.0

    # Display KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("💰 Net Profit", f"${total_profit:.2f}", delta_color="normal")
    kpi2.metric("🎯 Win Rate", f"{win_rate:.1f}%")
    kpi3.metric("⚖️ Profit Factor", f"{pf:.2f}")
    kpi4.metric("📊 Total Trades", total_trades)

    st.markdown("---")

    # --- 2. THE VISUALS ---
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📈 The Compounding Curve")
        if 'Open Time' in df.columns and 'Running' in df.columns:
            fig_equity = px.area(df, x='Open Time', y='Running', 
                                    title='Account Growth Over Time',
                                    labels={'Running': 'Balance ($)', 'Open Time': 'Date'})
            
            fig_equity.update_traces(line_color='#00FF7F', fillcolor='rgba(0, 255, 127, 0.1)')
            fig_equity.update_layout(height=450)
            st.plotly_chart(fig_equity, use_container_width=True)

    with col_right:
        st.subheader("📋 Last 5 Events")
        # Showing the latest action
        cols_to_show = ['Pair', 'Type', 'PnL', 'Reason']
        valid_cols = [c for c in cols_to_show if c in df.columns]
        
        if valid_cols:
            recent_trades = df[valid_cols].tail(5).iloc[::-1]
            st.dataframe(recent_trades, use_container_width=True, hide_index=True)
        
        st.info(f"Next refresh in {REFRESH_RATE}s... ⚡")

else:
    # Error handling if the link is broken
    st.error("🚫 Connection Failed!")
    st.warning("1. Check if the Google Sheet is set to 'Anyone with the link' -> 'Viewer'.")
    st.warning(f"2. Make sure the GID for '{selected_sheet_name}' is correct in the code.")
    st.code(CSV_URL)

# --- AUTO-REFRESH LOGIC ---
time.sleep(REFRESH_RATE)
st.rerun()