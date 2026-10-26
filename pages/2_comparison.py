import streamlit as st
import pandas as pd
from data import load_all_historical_returns, filter_by_range, get_range_years_limit
from strategy import calculate_performance_metrics
from ui import inject_custom_css, render_advanced_comparison_chart

st.set_page_config(page_title="走势与风险对比", page_icon="⚔️", layout="wide")
inject_custom_css()

st.markdown('<div class="header-banner"><h1>⚔️ 热门美股与 ETF 走势和风险对比</h1><p>多标的同期收益率曲线及核心风险收益指标对账单</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ 对比配置")
    time_range = st.selectbox(
        "时间跨度筛选",
        options=["1Y", "3Y", "5Y", "10Y", "Max"],
        index=3
    )

default_tickers = ["SPYM", "SCHG", "QQQ"]
extended_universe = list(dict.fromkeys(default_tickers + ["AAPL", "NVDA", "MSFT", "VOO"]))

col_select, col_input = st.columns([1.5, 1], gap="medium")
with col_select:
    selected_from_preset = st.multiselect(
        "🎯 选择或搜索常用标的 (最多 5 个)",
        options=extended_universe,
        default=default_tickers,
        max_selections=5
    )
with col_input:
    custom_input = st.text_input(
        "✍️ 自定义添加代码 (可选)",
        placeholder="例如: TSLA, NFLX"
    )

custom_list = [t.strip().upper() for t in custom_input.split(",") if t.strip()] if custom_input else []
selected_tickers = list(dict.fromkeys(selected_from_preset + custom_list))[:5]

if not selected_tickers:
    st.warning("⚠️ 请至少保留或选择一个对比标的。")
else:
    try:
        df_raw_prices = load_all_historical_returns(selected_tickers)
        df_filtered_prices = filter_by_range(df_raw_prices, time_range)
        
        if not df_filtered_prices.empty and len(df_filtered_prices) > 1: # type: ignore
            start_prices = df_filtered_prices.iloc[0] # type: ignore
            df_plot = ((df_filtered_prices / start_prices) - 1) * 100
            
            render_advanced_comparison_chart(df_plot, "累计收益率 (%)")
            
            st.markdown("### 📊 核心风险收益指标对账单")
            df_metrics = calculate_performance_metrics(df_filtered_prices)
            
            st.dataframe(
                df_metrics.style.format({
                    '累计收益率': '{:.2f}%',
                    '年化收益率 (CAGR)': '{:.2f}%',
                    '年化波动率': '{:.2f}%',
                    '最大回撤': '{:.2f}%',
                    '夏普比率': '{:.2f}'
                }),
                use_container_width=True
            )
        else:
            st.warning("所选时间段内数据不足，无法生成对比图与指标。")
    except Exception as e:
        st.error(f"加载对比数据失败: {e}")