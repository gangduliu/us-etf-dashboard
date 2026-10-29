import streamlit as st
from data import load_all_historical_returns, filter_by_range, fetch_ticker_fundamentals
from strategy import calculate_performance_metrics
from ui import inject_custom_css, render_advanced_comparison_chart

st.set_page_config(page_title="Asset Performance & Risk Comparison", page_icon="⚔️", layout="wide")
inject_custom_css()

# 页面顶部标的筛选与时间跨度控制栏
st.markdown("#### 🎯 Ticker Comparison & Time Horizon Configuration")

col_select, col_input, col_range = st.columns([2, 1.5, 1], gap="medium")

default_tickers = ["SPYM", "SCHG", "QQQ"]
extended_universe = list(
    dict.fromkeys(default_tickers + ["AAPL", "NVDA", "MSFT"])
)

with col_select:
    selected_from_preset = st.multiselect(
        "Select or Search Tickers (Max 5)",
        options=extended_universe,
        default=default_tickers,
        max_selections=5,
        help="Quickly select popular US Stocks & ETFs",
    )

with col_input:
    custom_input = st.text_input(
        "✍️ Custom Tickers (Optional)",
        placeholder="e.g. TSLA, NFLX",
        help="Separate multiple tickers with commas",
    )

with col_range:
    time_range = st.selectbox(
        "📅 Time Range",
        options=["1Y", "3Y", "5Y", "10Y", "Max"],
        index=3,
    )

custom_list = [t.strip().upper() for t in custom_input.split(",") if t.strip()] if custom_input else []
selected_tickers = list(dict.fromkeys(selected_from_preset + custom_list))[:5]

if not selected_tickers:
    st.warning("⚠️ Please select at least one ticker to compare.")
else:
    try:
        df_raw_prices = load_all_historical_returns(selected_tickers)
        df_filtered_prices = filter_by_range(df_raw_prices, time_range)
        
        if not df_filtered_prices.empty and len(df_filtered_prices) > 1: # type: ignore
            start_prices = df_filtered_prices.iloc[0] # type: ignore
            df_plot = ((df_filtered_prices / start_prices) - 1) * 100
            
            render_advanced_comparison_chart(df_plot, "Cumulative Return")
            
            # Fundamental Market Overview Section
            st.markdown("### 🏷️ Overview & Fundamentals")
            df_fundamentals = fetch_ticker_fundamentals(selected_tickers)
            st.dataframe(df_fundamentals, use_container_width=True)
            
            st.markdown("### 📊 Key Risk & Return Metrics")
            df_metrics = calculate_performance_metrics(df_filtered_prices)
            
            format_dict = {}
            for col in df_metrics.columns:
                if 'Cumulative Return' in col or 'CAGR' in col or 'Volatility' in col or 'Drawdown' in col:
                    format_dict[col] = '{:.2f}%'
                elif 'Sharpe' in col:
                    format_dict[col] = '{:.2f}'

            st.dataframe(
                df_metrics.style.format(format_dict),
                use_container_width=True
            )
        else:
            st.warning("Insufficient data in the selected range to generate chart and metrics.")
    except Exception as e:
        st.error(f"Failed to load comparison data: {e}")