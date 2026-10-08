import os

# 本地代理软件的 HTTP/SOCKS 端口
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'


import streamlit as st
import pandas as pd
import plotly.express as px

# 导入自定义模块
from data import (
    ETF_METADATA, load_etf_data, load_etf_holdings_and_sectors, 
    load_all_historical_returns, filter_by_range, calculate_ttm_dividend_yield,
    get_etf_aum, get_range_years_limit
)
from strategy import analyze_trading_signal
from ui import (
    inject_custom_css, render_header, render_kpi_cards,
    render_advice_card, render_comparison_chart
)

# 1. 页面基本配置
st.set_page_config(
    page_title="US ETF Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 侧边栏：标的选择器与参数配置
with st.sidebar:
    st.markdown("### 🎯 标的选择")
    selected_ticker = st.selectbox(
        "选择要查看的 ETF",
        options=["VOO", "VGT", "SCHD"],
        index=0
    )
    
    st.divider()
    st.markdown("### ⚙️ 看板配置")
    time_range = st.selectbox(
        "时间跨度筛选",
        options=["1Y", "3Y", "5Y", "10Y", "Max"],
        index=3
    )

# 3. 注入CSS与数据加载
inject_custom_css()
meta = ETF_METADATA[selected_ticker]

try:
    hist, info, dividends = load_etf_data(selected_ticker)
    sector_data, top_holdings = load_etf_holdings_and_sectors(selected_ticker)
except Exception as e:
    st.error(f"获取 {selected_ticker} 数据失败，请检查网络设置: {e}")
    st.stop()

filtered_hist = filter_by_range(hist, time_range)

# 计算核心指标
latest_price = hist['Close'].iloc[-1]
prev_price = hist['Close'].iloc[-2]
price_change = latest_price - prev_price
pct_change = (price_change / prev_price) * 100

week_52_high = info.get('fiftyTwoWeekHigh', hist['Close'].tail(252).max())
week_52_low = info.get('fiftyTwoWeekLow', hist['Close'].tail(252).min())
div_yield = calculate_ttm_dividend_yield(dividends, latest_price, info)
# 获取费率 (VGT 0.10%, VOO 0.03%, SCHD 0.06%)
expense_ratio = info.get('expenseRatio', 0.03 if selected_ticker=="VOO" else (0.10 if selected_ticker=="VGT" else 0.06))
if isinstance(expense_ratio, (int, float)) and expense_ratio < 0.01:
    expense_ratio = expense_ratio * 100
total_assets = get_etf_aum(info, selected_ticker)

# 4. 渲染 Banner & KPI 卡片
render_header(selected_ticker, meta)
render_kpi_cards(latest_price, price_change, pct_change, week_52_high, week_52_low, div_yield, expense_ratio, total_assets)

# 5. 渲染 Tabs（新增对比页）
tab1, tab2, tab3, tab4 = st.tabs([
    f"📊 {selected_ticker} 走势与策略", 
    "🧩 行业分布与重仓股", 
    "💰 历史回报与分红", 
    "⚔️ 三大 ETF 走势对比"
])

# Tab 1: 走势与交易建议
with tab1:
    buy_advice = analyze_trading_signal(hist, latest_price, week_52_high, week_52_low, div_yield)
    render_advice_card(buy_advice)

    col_chart, col_calc = st.columns([2.2, 1])
    
    with col_chart:
        st.markdown(f'<div class="section-title">📉 {selected_ticker} 历史价格走势曲线</div>', unsafe_allow_html=True)
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

    with col_calc:
        st.markdown('<div class="section-title">🧮 模拟定投/复利计算器</div>', unsafe_allow_html=True)
        initial_invest = st.number_input("初始投入 ($)", value=10000, step=1000)
        monthly_invest = st.number_input("每月定投 ($)", value=500, step=100)
        invest_years = st.slider("投资期限 (年)", min_value=1, max_value=30, value=10)
        
        default_return = 11.0 if selected_ticker == "VGT" else (8.0 if selected_ticker == "SCHD" else 8.5)
        expected_return = st.slider("预期年化收益率 (%)", min_value=1.0, max_value=20.0, value=default_return, step=0.5)

        months = invest_years * 12
        monthly_rate = (1 + expected_return / 100) ** (1/12) - 1
        total_principal = initial_invest + monthly_invest * months
        total_balance = initial_invest * ((1 + monthly_rate) ** months)
        for m in range(1, months + 1):
            total_balance += monthly_invest * ((1 + monthly_rate) ** (months - m))
        profit = total_balance - total_principal

        st.markdown(f"""
        <div style="background-color: rgba(15, 118, 110, 0.1); border: 1px solid rgba(15, 118, 110, 0.3); padding: 16px; border-radius: 10px; margin-top: 10px;">
            <div style="font-size: 0.85rem; color: #0F766E; font-weight: 600;">预估期末资产 ({invest_years}年后)</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #0F766E; margin: 4px 0;">${total_balance:,.0f}</div>
            <div style="font-size: 0.85rem; opacity: 0.85;">
                累计本金: <b>${total_principal:,.0f}</b><br>
                预计纯收益: <b>${profit:,.0f}</b> (+{(profit/total_principal)*100:.1f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)

# Tab 2: 行业分布与重仓股
with tab2:
    col_sector, col_holdings = st.columns([1, 1.1])
    with col_sector:
        st.markdown(f'<div class="section-title">🧱 {selected_ticker} 行业分布</div>', unsafe_allow_html=True)
        fig_pie = px.pie(
            sector_data, 
            values='Weight', 
            names='Sector', 
            hole=0.5,
            template="plotly",
            color_discrete_sequence=['#0F766E', '#0D9488', '#14B8A6', '#2DD4BF', '#5EEAD4', '#99F6E4', '#CCFBF1', '#334155']
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(
            margin=dict(l=0, r=0, t=10, b=0), 
            height=360,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_holdings:
        st.markdown(f'<div class="section-title">🏆 {selected_ticker} Top 10 核心重仓股</div>', unsafe_allow_html=True)
        st.dataframe(
            top_holdings,
            column_config={
                "Ticker": st.column_config.TextColumn("代码"),
                "Company": st.column_config.TextColumn("公司名称"),
                "Weight (%)": st.column_config.ProgressColumn(
                    "权重占比",
                    format="%.1f%%",
                    min_value=0,
                    max_value=20
                )
            },
            hide_index=True,
            use_container_width=True,
            height=360
        )

# Tab 3: 历史回报与分红 (联动 time_range)
with tab3:
    col_annual, col_div = st.columns([1, 1])
    years_limit = get_range_years_limit(time_range)
    
    with col_annual:
        st.markdown(f'<div class="section-title">📅 {"近 " + time_range if time_range != "Max" else "全历史"} 年度收益率 (%)</div>', unsafe_allow_html=True)
        annual_hist = hist['Close'].resample('YE').last()
        annual_returns = annual_hist.pct_change().dropna() * 100
        annual_df = pd.DataFrame({
            "Year": annual_returns.index.year, # type: ignore
            "Return": annual_returns.values
        }).tail(years_limit)  # 👈 联动限制显示年数
        
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

    with col_div:
        st.markdown(f'<div class="section-title">💵 {"近 " + time_range if time_range != "Max" else "全历史"} 每股年度分红 (USD)</div>', unsafe_allow_html=True)
        if not dividends.empty:
            div_df = dividends.resample('YE').sum().reset_index()
            div_df['Year'] = div_df['Date'].dt.year
            # 👈 动态根据选择的时间跨度筛选分红历史
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
            st.info("暂无分红数据")

# Tab 4: 收益对比页 (精确计算区间累计收益率)
with tab4:
    try:
        # 1. 获取所有标的的原始收盘价
        df_raw_prices = load_all_historical_returns(["VOO", "VGT", "SCHD"])
        
        # 2. 根据选定的时间跨度进行时间切片
        df_filtered_prices = filter_by_range(df_raw_prices, time_range)
        
        if not df_filtered_prices.empty: # type: ignore
            # 3. 正确计算区间真实累计收益率 (%)：(当前价格 / 起点价格 - 1) * 100
            start_prices = df_filtered_prices.iloc[0] # type: ignore
            df_cumulative_returns = ((df_filtered_prices / start_prices) - 1) * 100
            
            # 4. 渲染图表
            render_comparison_chart(df_cumulative_returns, time_range)
        else:
            st.warning("所选时间段内无足够的数据进行对比。")
    except Exception as e:
        st.error(f"加载对比数据失败: {e}")

# 页脚
st.divider()
st.caption("💡 声明：本看板仅供个人数据展示与学术研究，不构成任何投资建议。数据源自 Yahoo Finance。用户可在右上角 Settings 菜单中自由切换 Light / Dark 主题。")