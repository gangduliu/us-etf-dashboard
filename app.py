import os

# 本地代理软件的 HTTP/SOCKS 端口
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'


import streamlit as st
import pandas as pd
import plotly.express as px

# 导入自定义模块
from data import (
    load_stock_or_etf_data, load_etf_holdings_and_sectors, 
    load_all_historical_returns, filter_by_range, calculate_ttm_dividend_yield,
    get_asset_size_or_market_cap, get_range_years_limit,
    load_portfolio_market_data, get_portfolio_sector_breakdown,
    load_portfolio_from_file, export_portfolio_to_json, export_portfolio_to_csv
)
from strategy import (
    analyze_trading_signal, calculate_portfolio_metrics,
    analyze_portfolio_health, calculate_portfolio_rebalance,
    calculate_portfolio_dividends
)
from ui import (
    inject_custom_css, render_header, render_kpi_cards, 
    render_advice_card, render_comparison_chart,
    render_portfolio_summary_cards, render_portfolio_charts,
    render_portfolio_advisory, render_rebalance_dashboard,
    render_dividend_dashboard
)

# 1. 页面基本配置
st.set_page_config(
    page_title="US Stock & ETF Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 侧边栏：自由搜索美股代码 + 热门快捷切换
with st.sidebar:
    st.markdown("### 🔍 查询美股 / ETF")
    
    # 初始化输入框状态 (默认 VOO)
    if "ticker_input" not in st.session_state:
        st.session_state.ticker_input = "VOO"
        
    # 3 个核心 ETF 快捷按钮
    st.caption("热门快捷标的：")
    col_quick1, col_quick2, col_quick3 = st.columns(3)
    
    if col_quick1.button("VOO", use_container_width=True):
        st.session_state.ticker_input = "VOO"
    if col_quick2.button("VGT", use_container_width=True):
        st.session_state.ticker_input = "VGT"
    if col_quick3.button("SCHD", use_container_width=True):
        st.session_state.ticker_input = "SCHD"
        
    # 代码文本输入框 (自动绑定快捷按钮的选择)
    user_ticker = st.text_input(
        "输入任意美股/ETF代码 (如: TSLA, MSFT, BRK-B)",
        value=st.session_state.ticker_input
    ).strip().upper()
    
    st.divider()
    st.markdown("### ⚙️ 看板配置")
    time_range = st.selectbox(
        "时间跨度筛选",
        options=["1Y", "3Y", "5Y", "10Y", "Max"],
        index=3
    )

# 3. 注入 CSS 与通用数据加载
inject_custom_css()

if not user_ticker:
    st.warning("请输入有效的美股或 ETF 代码。")
    st.stop()

try:
    hist, info, dividends, is_etf = load_stock_or_etf_data(user_ticker)
except Exception as e:
    st.error(f"❌ 数据加载失败: {e}")
    st.stop()

filtered_hist = filter_by_range(hist, time_range)

# 计算通用核心指标
latest_price = hist['Close'].iloc[-1]
prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
price_change = latest_price - prev_price
pct_change = (price_change / prev_price) * 100 if prev_price > 0 else 0

week_52_high = info.get('fiftyTwoWeekHigh', hist['Close'].tail(252).max())
week_52_low = info.get('fiftyTwoWeekLow', hist['Close'].tail(252).min())
div_yield = calculate_ttm_dividend_yield(dividends, latest_price, info, user_ticker)
size_val = get_asset_size_or_market_cap(info)

# 4. 渲染 Banner & 动态 KPI 卡片
render_header(user_ticker, info, is_etf)
render_kpi_cards(latest_price, price_change, pct_change, week_52_high, week_52_low, div_yield, info, is_etf, size_val)

# 5. 动态 Tab 命名
tab2_title = "🧩 行业分布与重仓股" if is_etf else "🏢 核心财务与公司概况"
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"📊 {user_ticker} 走势与策略", 
    tab2_title, 
    "💰 历史回报与分红", 
    "⚔️ 热门美股/ETF 走势对比",
    "💼 投资组合管理" # <--- 新增 Tab
])

# Tab 1: 走势与量化决策
with tab1:
    trading_advice = analyze_trading_signal(hist, latest_price, week_52_high, week_52_low, div_yield)
    render_advice_card(trading_advice)

    col_chart, col_calc = st.columns([2.2, 1])
    
    with col_chart:
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

    with col_calc:
        st.markdown('<div class="section-title">🧮 模拟定投/复利计算器</div>', unsafe_allow_html=True)
        initial_invest = st.number_input("初始投入 ($)", value=10000, step=1000)
        monthly_invest = st.number_input("每月定投 ($)", value=500, step=100)
        invest_years = st.slider("投资期限 (年)", min_value=1, max_value=30, value=10)
        
        default_return = 12.0 if not is_etf else 8.5
        expected_return = st.slider("预期年化收益率 (%)", min_value=1.0, max_value=30.0, value=default_return, step=0.5)

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

# Tab 2: 智能判断 (ETF 显示持仓/行业，个股显示基本面指标)
with tab2:
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
        # 个股基本面展示
        st.markdown(f'<div class="section-title">🏢 {user_ticker} 公司关键财务指标</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("市盈率 P/E (TTM)", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A")
        c2.metric("远期市盈率 Forward P/E", f"{info.get('forwardPE', 0):.2f}" if info.get('forwardPE') else "N/A")
        c3.metric("市净率 P/B", f"{info.get('priceToBook', 0):.2f}" if info.get('priceToBook') else "N/A")
        c4.metric("净利润率 Profit Margin", f"{info.get('profitMargins', 0)*100:.1f}%" if info.get('profitMargins') else "N/A") # type: ignore

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 📝 公司业务简介")
        st.write(info.get('longBusinessSummary', '暂无详细介绍。'))

# Tab 3: 历史回报与分红
with tab3:
    col_annual, col_div = st.columns([1, 1])
    years_limit = get_range_years_limit(time_range)
    
    with col_annual:
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

    with col_div:
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

# Tab 4: 收益对比页
with tab4:
    try:
        # 对比标的池：包含当前查询的标的 + 常用基准
        compare_targets = list(set([user_ticker, "VOO", "VGT", "SCHD"]))
        df_raw_prices = load_all_historical_returns(compare_targets)
        df_filtered_prices = filter_by_range(df_raw_prices, time_range)
        
        if not df_filtered_prices.empty and len(df_filtered_prices) > 1: # type: ignore
            start_prices = df_filtered_prices.iloc[0] # type: ignore
            df_cumulative_returns = ((df_filtered_prices / start_prices) - 1) * 100
            render_comparison_chart(df_cumulative_returns, time_range)
        else:
            st.warning("所选时间段内数据不足，无法生成对比图。")
    except Exception as e:
        st.error(f"加载对比数据失败: {e}")


# 全局初始化 Session State 默认持仓与 Key 计数器
DEFAULT_PORTFOLIO = pd.DataFrame([
    {"ticker": "VOO", "shares": 5.0, "cost_price": 700.0, "target_pct": 60.0},
    {"ticker": "VGT", "shares": 6.0, "cost_price": 120.0, "target_pct": 20.0},
        {"ticker": "SCHD", "shares": 20.0, "cost_price": 30.0, "target_pct": 20.0}
])

if "portfolio_data" not in st.session_state:
  st.session_state.portfolio_data = DEFAULT_PORTFOLIO.copy()

if "uploader_key_id" not in st.session_state:
  st.session_state.uploader_key_id = 0

if "editor_key_id" not in st.session_state:
  st.session_state.editor_key_id = 0

# 2. 定义回调处理函数
def handle_file_upload():
  # 获取当前时刻上传框的 dynamic key
  current_key = f"portfolio_file_uploader_{st.session_state.uploader_key_id}"
  uploaded_file = st.session_state.get(current_key)

  if uploaded_file is not None:
    new_df = load_portfolio_from_file(uploaded_file)
    if new_df is not None and not new_df.empty:
      # 更新持仓数据
      st.session_state.portfolio_data = new_df
      st.toast("✅ 持仓数据导入成功，上传框已重置！", icon="🎉")

      # Key 自增 1，下一次渲染时会自动生成一个新的空白上传框
      st.session_state.uploader_key_id += 1


# Tab 5: 投资组合管理 & 再平衡计算器
with tab5:
    st.markdown('<div class="section-title">💼 我的投资组合配置与实盘跟踪</div>', unsafe_allow_html=True)

    # 持仓明细编辑与文件备份/恢复面板
    with st.expander("✏️ 编辑持仓明细与目标配置 (支持备份导入与一键重置)", expanded=False):
        # 工具栏标题
        st.markdown(
            '🔄 **持仓配置数据管理与恢复** &nbsp;|&nbsp; <span'
            ' style="font-size:0.85rem; opacity:0.7;">Data Transfer Toolbar</span>',
            unsafe_allow_html=True,
        )

        col_up, col_dl_json, col_dl_csv, col_reset = st.columns([1.3, 0.9, 0.9, 0.9], gap="medium")

        # 📥 1.1 文件导入（恢复）
        with col_up:
            dynamic_uploader_key = (
                f"portfolio_file_uploader_{st.session_state.uploader_key_id}"
            )
            st.file_uploader(
                "📤 恢复持仓备份 (.csv / .json)",
                type=["json", "csv"],
                key=dynamic_uploader_key,
                on_change=handle_file_upload,
                help="选择本地备份的 JSON 或 CSV 持仓文件，导入后将自动清空此框并恢复数据",
                label_visibility="visible",
            )

        # 📤 1.2 导出 JSON (结构化备份)
        with col_dl_json:
            st.markdown(
                '<label style="font-size: 0.88rem; opacity: 0.8; font-weight: 500;'
                ' display: block; margin-bottom: 8px;">💾 结构化备份</label>',
                unsafe_allow_html=True,
            )
            json_str = export_portfolio_to_json(st.session_state.portfolio_data)
            st.download_button(
                label="下载 JSON 备份",
                data=json_str,
                file_name="portfolio_backup.json",
                mime="application/json",
                use_container_width=True,
                help="推荐：格式完全无损，包含所有持仓与目标配置权重",
            )

        # 📤 1.3 导出 CSV (Excel 可读)
        with col_dl_csv:
            st.markdown(
                '<label style="font-size: 0.88rem; opacity: 0.8; font-weight: 500;'
                ' display: block; margin-bottom: 8px;">📊 表格兼容备份</label>',
                unsafe_allow_html=True,
            )
            csv_str = export_portfolio_to_csv(st.session_state.portfolio_data)
            st.download_button(
                label="导出 CSV (Excel)",
                data=csv_str,
                file_name="portfolio_backup.csv",
                mime="text/csv",
                use_container_width=True,
                help="适合用 Excel 批量修改持股数与成本价后重新导入",
            )

        # 🔄 1.4 一键重置为默认持仓按钮
        with col_reset:
            st.markdown(
                '<label style="font-size: 0.88rem; opacity: 0.8; font-weight: 500;'
                ' display: block; margin-bottom: 8px;">⚠️ 恢复初始状态</label>',
                unsafe_allow_html=True,
            )
            if st.button(
                "🔄 重置默认持仓",
                use_container_width=True,
                help="点击后将清空当前表格，恢复为默认的 VOO/VGT/SCHD 示例持仓",
            ):
                # 重置数据
                st.session_state.portfolio_data = DEFAULT_PORTFOLIO.copy()
                # 强制更新编辑器 key，让表格组件彻底重新渲染
                st.session_state.editor_key_id += 1
                st.toast("🔄 已成功恢复为默认示例持仓！", icon="💡")

        st.markdown("</div>", unsafe_allow_html=True)

        # 2. 交互式持仓数据在线编辑器
        st.caption("直接在下方表格修改持股数与成本价，修改后可随时通过上方按钮备份到本地：")

        # 动态拼接 data_editor 的 key，确保重置时表格能同步刷新
        dynamic_editor_key = f"portfolio_editor_{st.session_state.editor_key_id}"

        edited_portfolio = st.data_editor(
            st.session_state.portfolio_data,
            column_config={
                "ticker": st.column_config.TextColumn("代码 (Ticker)", required=True, width="small"),
                "shares": st.column_config.NumberColumn("持股数", min_value=0.01, step=1.0, format="%.2f"),
                "cost_price": st.column_config.NumberColumn("成本单价 ($)", min_value=0.01, step=0.01, format="$%.2f"),
                "target_pct": st.column_config.NumberColumn("目标权重 (%)", min_value=0.0, max_value=100.0, step=5.0, format="%.1f%%")
            },
            num_rows="dynamic",
            use_container_width=True,
            key=dynamic_editor_key
        )
        st.session_state.portfolio_data = edited_portfolio

    # 3. 核心计算与数据准备
    valid_portfolio = st.session_state.portfolio_data.dropna()
    
    if not valid_portfolio.empty:
        portfolio_tickers = valid_portfolio['ticker'].unique().tolist()
        market_data = load_portfolio_market_data(portfolio_tickers)
        p_metrics = calculate_portfolio_metrics(valid_portfolio, market_data)
        sector_p_df = get_portfolio_sector_breakdown(valid_portfolio, market_data)

        # 4. 顶部核心概览 KPI 卡片
        render_portfolio_summary_cards(p_metrics)
        
        # 5. 中层图表分析 (宽屏排版，不挡图例)
        render_portfolio_charts(p_metrics, sector_p_df)
        
        st.divider()

        # 6. 新增：一键再平衡计算器模块 (结合新资金 DCA)
        col_rebal_title, col_cash_input = st.columns([2, 1])
        with col_rebal_title:
            st.write("")
        with col_cash_input:
            new_cash = st.number_input("💵 拟新增投入资金 ($USD):", min_value=0.0, value=0.0, step=500.0, help="输入您本次计划加仓的金额，计算器将自动以存量+新资金综合平衡分配")

        rebalance_df, total_curr_val, target_tot_val = calculate_portfolio_rebalance(valid_portfolio, market_data, new_cash)
        render_rebalance_dashboard(rebalance_df, total_curr_val, target_tot_val, new_cash)

        st.divider()

        if not valid_portfolio.empty:
            # 批量获取各持仓标的原始分红数据 (供现金流月度分布计算)
            raw_dividends_dict = {}
            for _, row in valid_portfolio.iterrows():
                t = row['ticker'].strip().upper()
                try:
                    _, _, divs, _ = load_stock_or_etf_data(t)
                    raw_dividends_dict[t] = divs
                except Exception:
                    pass

        # 计算并渲染 股息现金流预估看板
        div_metrics = calculate_portfolio_dividends(valid_portfolio, market_data, raw_dividends_dict)
        render_dividend_dashboard(div_metrics)

        st.divider()

        # 7. 组合健康诊断
        suggestions = analyze_portfolio_health(valid_portfolio, market_data, sector_p_df)
        render_portfolio_advisory(suggestions)
        
        st.divider()

        # 8. 底层持仓盈亏明细表格
        st.markdown('<div class="section-title">📋 持仓资产盈亏明细表</div>', unsafe_allow_html=True)
        st.dataframe(
            p_metrics['details_df'],
            column_config={
                "代码": st.column_config.TextColumn("代码", width="small"),
                "名称": st.column_config.TextColumn("名称", width="large"),
                "持仓股数": st.column_config.NumberColumn("持股数", format="%.2f"),
                "持仓成本价 ($)": st.column_config.NumberColumn("成本价", format="$%.2f"),
                "当前现价 ($)": st.column_config.NumberColumn("当前现价", format="$%.2f"),
                "当前总市值 ($)": st.column_config.NumberColumn("总市值", format="$%.2f"),
                "持仓成本总额 ($)": st.column_config.NumberColumn("成本总额", format="$%.2f"),
                "累计盈亏 ($)": st.column_config.NumberColumn("累计盈亏", format="$%.2f"),
                "累计收益率 (%)": st.column_config.NumberColumn("收益率", format="%.2f%%"),
                "当日盈亏 ($)": st.column_config.NumberColumn("当日盈亏", format="$%.2f")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("💡 请展开上方编辑面板，添加至少一只持仓标的。")

# 全局页脚
st.divider()
st.caption("💡 声明：本看板支持查询美股所有上市个股与 ETF。数据源自 Yahoo Finance。仅供个人数据展示与研究使用，不构成任何投资建议。")