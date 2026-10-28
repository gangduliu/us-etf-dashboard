import streamlit as st
import pandas as pd
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

st.set_page_config(page_title="走势与策略", page_icon="📊", layout="wide")
inject_custom_css()

# 1. 初始化 Session State
if "ticker_input" not in st.session_state:
    st.session_state.ticker_input = "SPYM"

# 定义快捷按钮点击的回调函数
def set_ticker(val):
    st.session_state.ticker_input = val

# 2. 页面顶部搜索与时间跨度筛选控制栏
st.markdown("#### 🔍 标的查询与参数配置")

# 左右两列大布局：左侧放输入框与快捷按钮，右侧放时间跨度筛选
col_left, col_middle, col_right = st.columns([2, 1, 1], gap="small")

with col_left:
    # 快捷按钮紧凑排列在输入框下方，整洁不拥挤
    st.markdown('<div style="font-size: 0.8rem; opacity: 0.7; margin-bottom: 6px;">常用快捷标的：</div>', unsafe_allow_html=True)
    q_cols = st.columns(3)
    q_cols[0].button("SPYM", on_click=set_ticker, args=("SPYM",), use_container_width=True)
    q_cols[1].button("SCHG", on_click=set_ticker, args=("SCHG",), use_container_width=True)
    q_cols[2].button("QQQ", on_click=set_ticker, args=("QQQ",), use_container_width=True)

with col_middle:
    user_ticker = st.text_input(
        "输入任意美股 / ETF 代码",
        value=st.session_state.ticker_input,
        key="ticker_input",
        placeholder="例如: TSLA, MSFT, QQQ"
    ).strip().upper()

with col_right:
    time_range = st.selectbox(
        "时间跨度筛选",
        options=["1Y", "3Y", "5Y", "10Y", "Max"],
        index=3
    )

st.divider()

if not user_ticker:
    st.warning("请输入有效的美股或 ETF 代码。")
    st.stop()

try:
    hist, info, dividends, is_etf = load_stock_or_etf_data(user_ticker)
except Exception as e:
    st.error(f"❌ 数据加载失败: {e}")
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

# 渲染头部与 KPI 卡片
render_header(user_ticker, info, is_etf)
render_kpi_cards(latest_price, price_change, pct_change, week_52_high, week_52_low, div_yield, info, is_etf, size_val)

# 量化交易策略建议 Banner
trading_advice = analyze_trading_signal(hist, latest_price, week_52_high, week_52_low, div_yield)
render_advice_card(trading_advice)

# 历史价格走势曲线
st.markdown(f'<div class="section-title">📉 {user_ticker} 历史价格走势曲线</div>', unsafe_allow_html=True)
fig_price = px.line(
    filtered_hist, 
    x=filtered_hist.index,  # type: ignore
    y='Close',
    labels={'Close': '收盘价 (USD)', 'Date': '日期'},
    template="plotly"
)
fig_price.update_traces(
    line_color="#0F766E", 
    line_width=2.5,
    hovertemplate="日期: %{x|%Y-%m-%d}<br>价格: <b>$%{y:.2f}</b><extra></extra>"
)
fig_price.update_layout(
    height=400,
    margin=dict(l=0, r=0, t=10, b=0),
    hovermode="x unified",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, title="")
)
st.plotly_chart(fig_price, use_container_width=True)

total_ret, cagr_val, mdd_val = calculate_ticker_performance_metrics(filtered_hist)

perf_df = pd.DataFrame([{
    "统计时间跨度": time_range,
    "起始日期": filtered_hist.index[0].strftime("%Y-%m-%d"), # type: ignore
    "最新日期": filtered_hist.index[-1].strftime("%Y-%m-%d"), # type: ignore
    "阶段累计回报率 (Total Return)": f"{total_ret * 100:+.2f}%",
    "年化回报率 (CAGR)": f"{cagr_val * 100:+.2f}%",
    "最大回撤 (Max Drawdown)": f"{mdd_val * 100:.2f}%"
}])

st.markdown("##### 📋 走势图阶段风险与收益指标明细")
st.dataframe(
    perf_df,
    hide_index=True,
    use_container_width=True
)

st.divider()
title = "🧩 行业分布与重仓股" if is_etf else "🏢 核心财务与公司概况"
st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

if is_etf:
    sector_data, top_holdings = load_etf_holdings_and_sectors(user_ticker)
    col_sector, col_holdings = st.columns([1, 1.1])
    with col_sector:
        st.markdown(f'<div class="section-title">🧱 {user_ticker} 行业分布</div>', unsafe_allow_html=True)
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
            st.info("暂无行业分布数据。")

    with col_holdings:
        st.markdown(f'<div class="section-title">🏆 {user_ticker} Top 10 核心重仓股</div>', unsafe_allow_html=True)
        if not top_holdings.empty:
            st.dataframe(
                top_holdings,
                column_config={
                    "Ticker": st.column_config.TextColumn("代码"),
                    "Company": st.column_config.TextColumn("公司名称"),
                    "Weight (%)": st.column_config.ProgressColumn("权重占比", format="%.1f%%", min_value=0, max_value=20)
                },
                hide_index=True,
                use_container_width=True,
                height=360
            )
        else:
            st.info("暂无重仓股明细数据。")
else:
    st.markdown(f'<div class="section-title">🏢 {user_ticker} 公司关键财务指标</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("市盈率 P/E (TTM)", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A")
    c2.metric("远期市盈率 Forward P/E", f"{info.get('forwardPE', 0):.2f}" if info.get('forwardPE') else "N/A")
    c3.metric("市净率 P/B", f"{info.get('priceToBook', 0):.2f}" if info.get('priceToBook') else "N/A")
    c4.metric("净利润率 Profit Margin", f"{info.get('profitMargins', 0)*100:.1f}%" if info.get('profitMargins') else "N/A") # type: ignore

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📝 公司业务简介")
    st.write(info.get('longBusinessSummary', '暂无详细介绍。'))

# ==================== 恢复：历史回报与分红图表模块 ====================
st.divider()
st.markdown(f'<div class="section-title">💰 历史回报与分红</div>', unsafe_allow_html=True)
years_limit = get_range_years_limit(time_range)

st.markdown(f'<div class="section-title">📅 近 {time_range if time_range != "Max" else "历史"} 年度收益率 (%)</div>', unsafe_allow_html=True)
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


st.markdown(f'<div class="section-title">💵 近 {time_range if time_range != "Max" else "历史"} 每股年度分红 (USD)</div>', unsafe_allow_html=True)
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
        hovertemplate="年份: %{x}<br>每股分红: <b>$%{y:.2f}</b><extra></extra>"
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
    st.info("该标的近一年内无派息记录（或不分红）。")