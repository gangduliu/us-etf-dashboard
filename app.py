import os

# 本地代理软件的 HTTP/SOCKS 端口
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'


import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 导入自定义模块
from data import load_voo_data, load_voo_holdings_and_sectors, filter_by_range, calculate_ttm_dividend_yield
from strategy import analyze_buy_signal
from ui import get_theme_config, inject_custom_css, render_header, render_kpi_cards, render_advice_card

# 1. 页面基本配置
st.set_page_config(
    page_title="VOO Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 侧边栏及主题初始化
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

with st.sidebar:
    st.markdown("### ⚙️ 看板配置")
    st.caption("界面与数据参数")
    st.session_state.dark_mode = st.toggle("🌙 深色模式 (Dark Mode)", value=st.session_state.dark_mode)
    
    time_range = st.selectbox(
        "时间跨度筛选",
        options=["1Y", "3Y", "5Y", "10Y", "Max"],
        index=2
    )

# 3. 加载数据与主题设置
theme = get_theme_config(st.session_state.dark_mode)
inject_custom_css(theme)

try:
    hist, info, dividends = load_voo_data()
    sector_data, top_holdings = load_voo_holdings_and_sectors()
except Exception as e:
    st.error(f"获取数据失败，请检查网络设置或稍后再试: {e}")
    st.stop()

filtered_hist = filter_by_range(hist, time_range)

# 计算指标数据
latest_price = hist['Close'].iloc[-1]
prev_price = hist['Close'].iloc[-2]
price_change = latest_price - prev_price
pct_change = (price_change / prev_price) * 100

week_52_high = info.get('fiftyTwoWeekHigh', hist['Close'].tail(252).max())
week_52_low = info.get('fiftyTwoWeekLow', hist['Close'].tail(252).min())
div_yield = calculate_ttm_dividend_yield(dividends, latest_price, info)
expense_ratio = 0.03
total_assets = info.get('totalAssets', 0)

# 4. 渲染 Header 与 KPI 指标栏
render_header()
render_kpi_cards(latest_price, price_change, pct_change, week_52_high, week_52_low, div_yield, expense_ratio, total_assets)

# 5. 渲染 Tabs
tab1, tab2, tab3 = st.tabs(["📊 价格走势与投资计算器", "🧩 行业分布与重仓股", "💰 历史回报与分红"])

# Tab 1: 价格走势、买入建议与投资计算器
with tab1:
    buy_advice = analyze_buy_signal(hist, latest_price, week_52_high, week_52_low)
    render_advice_card(buy_advice)

    col_chart, col_calc = st.columns([2.2, 1])
    
    with col_chart:
        st.markdown('<div class="section-title">📉 历史价格走势曲线</div>', unsafe_allow_html=True)
        fig_price = px.line(
            filtered_hist, 
            x=filtered_hist.index, 
            y='Close',
            labels={'Close': '收盘价 (USD)', 'Date': '日期'},
            template=theme['PLOTLY_TEMPLATE']
        )
        fig_price.update_traces(
            line_color=theme['THEME_MAIN'], 
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
            yaxis=dict(showgrid=True, gridcolor=theme['THEME_BORDER'], title="")
        )
        st.plotly_chart(fig_price, use_container_width=True)

    with col_calc:
        st.markdown('<div class="section-title">🧮 模拟定投/复利计算器</div>', unsafe_allow_html=True)
        initial_invest = st.number_input("初始投入 ($)", value=10000, step=1000)
        monthly_invest = st.number_input("每月定投 ($)", value=500, step=100)
        invest_years = st.slider("投资期限 (年)", min_value=1, max_value=30, value=10)
        expected_return = st.slider("预期年化收益率 (%)", min_value=1.0, max_value=15.0, value=8.5, step=0.5)

        months = invest_years * 12
        monthly_rate = (1 + expected_return / 100) ** (1/12) - 1
        total_principal = initial_invest + monthly_invest * months
        total_balance = initial_invest * ((1 + monthly_rate) ** months)
        for m in range(1, months + 1):
            total_balance += monthly_invest * ((1 + monthly_rate) ** (months - m))
        profit = total_balance - total_principal

        st.markdown(f"""
        <div style="background-color: {theme['CALC_BG']}; border: 1px solid {theme['CALC_BORDER']}; padding: 16px; border-radius: 10px; margin-top: 10px;">
            <div style="font-size: 0.85rem; color: {theme['CALC_TEXT']}; font-weight: 500;">预估期末资产 ({invest_years}年后)</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: {theme['CALC_TEXT']}; margin: 4px 0;">${total_balance:,.0f}</div>
            <div style="font-size: 0.85rem; color: {theme['THEME_TEXT_MUTED']};">
                累计本金: <b>${total_principal:,.0f}</b><br>
                预计纯收益: <b>${profit:,.0f}</b> (+{(profit/total_principal)*100:.1f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)

# Tab 2: 行业分布与重仓股
with tab2:
    col_sector, col_holdings = st.columns([1, 1.1])
    with col_sector:
        st.markdown('<div class="section-title">🧱 行业板块分布 (Sector Weight)</div>', unsafe_allow_html=True)
        fig_pie = px.pie(
            sector_data, 
            values='Weight', 
            names='Sector', 
            hole=0.5,
            template=theme['PLOTLY_TEMPLATE'],
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
        st.markdown('<div class="section-title">🏆 Top 10 核心重仓股</div>', unsafe_allow_html=True)
        st.dataframe(
            top_holdings,
            column_config={
                "Ticker": st.column_config.TextColumn("代码"),
                "Company": st.column_config.TextColumn("公司名称"),
                "Weight (%)": st.column_config.ProgressColumn(
                    "权重占比",
                    format="%.1f%%",
                    min_value=0,
                    max_value=10
                )
            },
            hide_index=True,
            use_container_width=True,
            height=360
        )

# Tab 3: 历史回报与分红
with tab3:
    col_annual, col_div = st.columns([1, 1])
    with col_annual:
        st.markdown('<div class="section-title">📅 近 10 年年度收益率 (%)</div>', unsafe_allow_html=True)
        annual_hist = hist['Close'].resample('YE').last()
        annual_returns = annual_hist.pct_change().dropna() * 100
        annual_df = pd.DataFrame({
            "Year": annual_returns.index.year, # type: ignore
            "Return": annual_returns.values
        }).tail(10)
        annual_df['Color'] = annual_df['Return'].apply(lambda x: theme['THEME_MAIN'] if x >= 0 else '#F43F5E')
        
        fig_bar = px.bar(
            annual_df, 
            x='Year', 
            y='Return', 
            text_auto='.1f', # type: ignore
            template=theme['PLOTLY_TEMPLATE']
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
            yaxis=dict(showgrid=True, gridcolor=theme['THEME_BORDER'])
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_div:
        st.markdown('<div class="section-title">💵 每股年度累计分红 (USD)</div>', unsafe_allow_html=True)
        if not dividends.empty:
            div_df = dividends.resample('YE').sum().reset_index()
            div_df['Year'] = div_df['Date'].dt.year
            div_df = div_df[div_df['Year'] >= datetime.now().year - 10]
            
            fig_div = px.line(
                div_df, 
                x='Year', 
                y='Dividends', 
                markers=True,
                template=theme['PLOTLY_TEMPLATE']
            )
            fig_div.update_traces(
                line_color=theme['THEME_MAIN'], 
                marker_color=theme['THEME_MAIN_LIGHT'], 
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
                yaxis=dict(showgrid=True, gridcolor=theme['THEME_BORDER'])
            )
            st.plotly_chart(fig_div, use_container_width=True)
        else:
            st.info("暂无分红数据")

# 全局页脚
st.divider()
st.caption("💡 声明：本看板仅供个人数据展示与学术研究，不构成任何投资建议。数据源自 Yahoo Finance。")