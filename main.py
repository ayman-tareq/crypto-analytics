import streamlit as st
import requests
import datetime
import plotly.graph_objs as go
import re, os, time
from datetime import timezone

# Set page config
st.set_page_config(
    page_title="Crypto Analytics Dashboard",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Title and description
st.title("Crypto Analytics Dashboard")
st.markdown("Track cryptocurrency metrics including FDV and Market Cap")

# Sidebar inputs
with st.sidebar:
    st.header("Input Parameters")
    
    # Token ID input
    token_id = st.text_input("Enter the Token ID:", value="bitcoin").strip()
    
    # Period selection
    period_options = {
        "1 Week": "1w",
        "1 Month": "1mo",
        "6 Months": "6m",
        "1 Year": "1y",
        "Custom Dates": "custom"
    }
    period_selection = st.selectbox("Select Timeframe:", options=list(period_options.keys()))
    
    # Custom date input
    if period_selection == "Custom Dates":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        period = f"{start_date},{end_date}"
    else:
        period = period_options[period_selection]

# Base URL for CoinGecko API
BASE_URL = "https://api.coingecko.com/api/v3"

@st.cache_data(ttl=300)  # Cache for 1 hour
def fetch_price_and_market_cap(token_id):
    url = f"{BASE_URL}/simple/price"
    params = {
        "ids": token_id,
        "vs_currencies": "usd",
        "include_market_cap": "true"
    }
    response = requests.get(url, params=params)
    return response.json()

@st.cache_data(ttl=300)
def fetch_market_chart_range(token_id, from_date, to_date):
    url = f"{BASE_URL}/coins/{token_id}/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from": from_date,
        "to": to_date
    }
    response = requests.get(url, params=params)
    return response.json()

@st.cache_data(ttl=300)
def fetch_tvl(token_id):
    url = f"{BASE_URL}/coins/{token_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching TVL for token {token_id}: {response.status_code}")
        return None

# Calculate dates based on period
if ',' in period:
    try:
        start_date, end_date = period.split(',')
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days
        period_text = f"From {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
    except ValueError:
        st.error("Invalid date format")
        st.stop()
else:
    if period == '6m':
        days, period_text = 180, '6 Months'
    elif period == '1y':
        days, period_text = 365, '1 Year'
    elif 'w' in period:
        days = int(re.findall(r'\d+', period)[0]) * 7
        period_text = f"{days//7} Week{'s' if days>7 else ''}"
    elif 'mo' in period:
        days = int(re.findall(r'\d+', period)[0]) * 30
        period_text = f"{days//30} Month{'s' if days>30 else ''}"
    elif 'd' in period:
        days = int(re.findall(r'\d+', period)[0])
        period_text = f"{days} Day{'s' if days>1 else ''}"

# Fetch data
with st.spinner("Fetching data..."):
    from_date = int((datetime.datetime.now(timezone.utc) - datetime.timedelta(days=days)).timestamp())
    to_date = int(datetime.datetime.now(timezone.utc).timestamp())

    price_and_market_cap = fetch_price_and_market_cap(token_id)
    market_chart_range = fetch_market_chart_range(token_id, from_date, to_date)
    tvl_data = fetch_tvl(token_id)

# Calculate FDV
historical_fdv = []
for point in market_chart_range.get("prices", []):
    price = point[1]
    timestamp = point[0]
    total_supply = tvl_data.get("market_data", {}).get("total_supply", 0)
    fdv = price * total_supply if total_supply else 0
    historical_fdv.append((timestamp, fdv))

# Display current metrics
col1, col2, col3 = st.columns(3)
with col1:
    current_price = tvl_data.get("market_data", {}).get("current_price", {}).get("usd", 0)
    st.metric("Current Price", f"${current_price:,.2f}")
with col2:
    market_cap = tvl_data.get("market_data", {}).get("market_cap", {}).get("usd", 0)
    st.metric("Market Cap", f"${market_cap:,.0f}")
with col3:
    total_supply = tvl_data.get("market_data", {}).get("total_supply", 0)
    st.metric("Total Supply", f"{total_supply:,.0f}")

# Plot data
timestamps = [datetime.datetime.fromtimestamp(point[0] / 1000, timezone.utc) for point in historical_fdv]
fdv_values = [point[1] for point in historical_fdv]
market_cap_values = [point[1] for point in market_chart_range.get("market_caps", [])]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=timestamps, 
    y=fdv_values, 
    mode='lines', 
    name='FDV',
    line=dict(color='blue')
))

fig.add_trace(go.Scatter(
    x=timestamps, 
    y=market_cap_values, 
    mode='lines', 
    name='Market Cap',
    line=dict(color='red')
))

fig.update_layout(
    title=f"FDV and Market Cap Over {period_text}",
    xaxis_title="Time",
    yaxis_title="Value (USD)",
    legend=dict(x=0.05, y=0.95),
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# Add download button for the chart
if st.button("Download Chart"):
    os.makedirs('./charts', exist_ok=True)
    filename = f"{token_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    fig.write_html(os.path.join('./charts', filename))
    placeholder = st.empty()
    placeholder.success(f"Chart saved as {filename} in the charts directory", icon="✅")
    time.sleep(3)
    placeholder.empty()