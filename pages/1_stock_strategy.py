import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from data import (
    load_stock_or_etf_data, load_etf_holdings_and_sectors, 
    filter_by_range, calculate_ttm_dividend_yield,
    get_asset_size_or_market_cap, get_range_years_limit
)
from strategy import analyze_trading_signal, calculate_ticker_performance_metrics
from ui import (
    inject_custom_css, render_header, render_kpi_cards, 
    render_advice_card
)

st.set_page_config(page_title="Trend & Strategy", page_icon="📊", layout="wide")
inject_custom_css()

# 1. Initialize Session State / 初始化 Session State
if "ticker_input" not in st.session_state:
    st.session_state.ticker_input = "SPYM"

# Callback function for quick ticker buttons / 定义快捷按钮点击的回调函数
def set_ticker(val):
    st.session_state.ticker_input = val

# 2. Header Search and Time Range Control Bar / 页面顶部搜索与时间跨度筛选控制栏
st.markdown("#### 🔍 Ticker Search & Configuration")

col_left, col_middle, col_right = st.columns([2, 1, 1], gap="small")

with col_left:
    st.markdown('<div style="font-size: 0.8rem; opacity: 0.7; margin-bottom: 6px;">Popular Tickers:</div>', unsafe_allow_html=True)
    q_cols = st.columns(3)
    q_cols[0].button("SPYM", on_click=set_ticker, args=("SPYM",), use_container_width=True)
    q_cols[1].button("SCHG", on_click=set_ticker, args=("SCHG",), use_container_width=True)
    q_cols[2].button("QQQ", on_click=set_ticker, args=("QQQ",), use_container_width=True)

with col_middle:
    user_ticker = st.text_input(
        "Enter US Stock / ETF Ticker",
        value=st.session_state.ticker_input,
        key="ticker_input",
        placeholder="e.g. TSLA, MSFT, AAPL"
    ).strip().upper()

with col_right:
    time_range = st.selectbox(
        "Time Horizon",
        options=["1Y", "3Y", "5Y", "10Y", "Max"],
        index=3
    )

st.divider()

if not user_ticker:
    st.warning("Please enter a valid US Stock or ETF Ticker")
    st.stop()

try:
    hist, info, dividends, is_etf = load_stock_or_etf_data(user_ticker)
except Exception as e:
    st.error(f"❌ Data Load Failed: {e}")
    st.stop()

filtered_hist = filter_by_range(hist, time_range)

latest_price = hist['Close'].iloc[-1]
prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
price_change = latest_price - prev_price
pct_change = (price_change / prev_price) * 100 if prev_price > 0 else 0

week_52_high = info.get('fiftyTwoWeekHigh', hist['Close'].tail(252).max())
week_52_low = info.get('fiftyTwoWeekLow', hist['Close'].tail(252).min())
div_yield = calculate_ttm_dividend_yield(dividends, latest_price, info, user_ticker)
size_val = get_asset_size_or_market_cap(info)

# Render Header & KPI Cards / 渲染头部与 KPI 卡片
render_header(user_ticker, info, is_etf)
render_kpi_cards(latest_price, price_change, pct_change, week_52_high, week_52_low, div_yield, info, is_etf, size_val)

# Quantitative Trading Advice Banner / 量化交易策略建议 Banner
trading_advice = analyze_trading_signal(hist, latest_price, week_52_high, week_52_low, div_yield)
render_advice_card(trading_advice)

total_ret, cagr_val, mdd_val = calculate_ticker_performance_metrics(filtered_hist)

# Historical Price Trend Chart / 历史价格走势曲线
st.markdown(f'<div class="section-title">📉 {user_ticker} Historical Price Trend ({time_range})</div>', unsafe_allow_html=True)
fig_price = px.line(
    filtered_hist, 
    x=filtered_hist.index,  # type: ignore
    y='Close',
    labels={'Close': 'Price (USD)', 'Date': 'Date'},
    template="plotly"
)
fig_price.update_traces(
    line_color="#0F766E", 
    line_width=2.5,
    hovertemplate="Date: %{x|%Y-%m-%d}<br>Price: <b>$%{y:.2f}</b><extra></extra>"
)
fig_price.update_layout(
    height=380,
    margin=dict(l=0, r=0, t=10, b=0),
    hovermode="x unified",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, title="")
)
st.plotly_chart(fig_price, use_container_width=True)

# Performance Metrics Table Below Chart / 折线图下方：以表格形式展示风险收益指标
perf_df = pd.DataFrame([{
    "Time Range": time_range,
    "Start Date": filtered_hist.index[0].strftime("%Y-%m-%d"), # type: ignore
    "End Date": filtered_hist.index[-1].strftime("%Y-%m-%d"), # type: ignore
    "Total Return": f"{total_ret * 100:+.2f}%",
    "CAGR": f"{cagr_val * 100:+.2f}%",
    "Max Drawdown": f"{mdd_val * 100:.2f}%"
}])

st.markdown("##### 📋 Risk & Return Metrics")
st.dataframe(
    perf_df,
    hide_index=True,
    use_container_width=True
)

st.divider()
title = "🧩 Sector Breakdown & Top Holdings" if is_etf else "🏢 Key Financials & Company Overview"
st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

if is_etf:
    sector_data, top_holdings = load_etf_holdings_and_sectors(user_ticker)
    col_sector, col_holdings = st.columns([1, 1.1])
    with col_sector:
        st.markdown(f'<div class="section-title">🧱 {user_ticker} Sector Allocation</div>', unsafe_allow_html=True)
        if not sector_data.empty:
            fig_pie = px.pie(
                sector_data, 
                values='Weight', 
                names='Sector', 
                hole=0.5,
                template="plotly",
                color_discrete_sequence=['#0F766E', '#0D9488', '#14B8A6', '#2DD4BF', '#5EEAD4', '#99F6E4', '#CCFBF1', '#334155']
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=360, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No sector breakdown data available.")

    with col_holdings:
        st.markdown(f'<div class="section-title">🏆 {user_ticker} Top 10 Holdings</div>', unsafe_allow_html=True)
        if not top_holdings.empty:
            st.dataframe(
                top_holdings,
                column_config={
                    "Ticker": st.column_config.TextColumn("Ticker"),
                    "Company": st.column_config.TextColumn("Company"),
                    "Weight (%)": st.column_config.ProgressColumn("Weight", format="%.1f%%", min_value=0, max_value=20)
                },
                hide_index=True,
                use_container_width=True,
                height=360
            )
        else:
            st.info("No holdings data available.")
else:
    st.markdown(f'<div class="section-title">🏢 {user_ticker} Key Financial Metrics</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("P/E (TTM)", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A")
    c2.metric("Forward P/E", f"{info.get('forwardPE', 0):.2f}" if info.get('forwardPE') else "N/A")
    c3.metric("P/B Ratio", f"{info.get('priceToBook', 0):.2f}" if info.get('priceToBook') else "N/A")
    c4.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.1f}%" if info.get('profitMargins') else "N/A") # type: ignore

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📝 Business Profile")
    st.write(info.get('longBusinessSummary', 'No detailed profile available.'))

# Historical Returns & Dividend Analysis Module / 历史回报与分红模块
st.divider()
st.markdown(f'<div class="section-title">💰 Historical Performance & Dividend Analysis</div>', unsafe_allow_html=True)
years_limit = get_range_years_limit(time_range)

col_annual, col_dividend = st.columns([1, 1])

with col_annual:
    st.markdown(f'<div class="section-title">📅 Annual Return (%)</div>', unsafe_allow_html=True)
    annual_hist = hist['Close'].resample('YE').last()
    annual_returns = annual_hist.pct_change().dropna() * 100
    annual_df = pd.DataFrame({
        "Year": annual_returns.index.year, # type: ignore
        "Return": annual_returns.values
    }).tail(years_limit)

    annual_df['Color'] = annual_df['Return'].apply(lambda x: '#0F766E' if x >= 0 else '#F43F5E')

    fig_bar = px.bar(
        annual_df, 
        x='Year', 
        y='Return', 
        text_auto='.1f', # type: ignore
        template="plotly"
    )
    fig_bar.update_traces(marker_color=annual_df['Color'], textposition='outside')
    fig_bar.update_layout(
        yaxis_title="", 
        xaxis_title="",
        height=360,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, dtick=1),
        yaxis=dict(showgrid=True)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_dividend:
    st.markdown(f'<div class="section-title">💵 Annual Dividend Per Share (USD)</div>', unsafe_allow_html=True)
    if not dividends.empty:
        div_df = dividends.resample('YE').sum().reset_index()
        div_df['Year'] = div_df['Date'].dt.year
        div_df = div_df.tail(years_limit)
        
        fig_div = px.line(
            div_df, 
            x='Year', 
            y='Dividends', 
            markers=True,
            template="plotly"
        )
        fig_div.update_traces(
            line_color="#0F766E", 
            marker_color="#14B8A6", 
            marker_size=8,
            hovertemplate="Year: %{x}<br>Dividend: <b>$%{y:.2f}</b><extra></extra>"
        )
        fig_div.update_layout(
            yaxis_title="", 
            xaxis_title="",
            height=360,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, dtick=1),
            yaxis=dict(showgrid=True)
        )
        st.plotly_chart(fig_div, use_container_width=True)
    else:
        st.info("No dividend payout history in the past year.")