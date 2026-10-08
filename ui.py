import streamlit as st
import plotly.express as px

PRIMARY_COLOR = "#0F766E"
PRIMARY_LIGHT = "#14B8A6"

def inject_custom_css():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1280px;
        }}

        .header-banner {{
            background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #0D9488 100%);
            padding: 24px 32px;
            border-radius: 16px;
            color: #FFFFFF !important;
            margin-bottom: 24px;
            box-shadow: 0 10px 15px -3px rgba(15, 118, 110, 0.25);
        }}
        .header-banner h1 {{
            color: #FFFFFF !important;
            font-weight: 700;
            font-size: 1.8rem;
            margin: 0 0 6px 0;
            letter-spacing: -0.02em;
        }}
        .header-banner p {{
            color: #CCFBF1 !important;
            font-size: 0.9rem;
            margin: 0;
        }}

        [data-testid="stMetric"] {{
            background-color: rgba(125, 125, 125, 0.05);
            padding: 18px 20px;
            border-radius: 12px;
            border: 1px solid rgba(125, 125, 125, 0.15);
            transition: all 0.2s ease-in-out;
            position: relative;
            overflow: hidden;
            min-height: 110px;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-2px);
            border-color: rgba(15, 118, 110, 0.4);
        }}
        [data-testid="stMetric"]::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, {PRIMARY_COLOR}, {PRIMARY_LIGHT});
        }}
        
        [data-testid="stMetricLabel"] {{
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            opacity: 0.8;
        }}
        
        [data-testid="stMetricValue"] {{
            font-weight: 700 !important;
            font-size: 1.5rem !important;
            letter-spacing: -0.02em;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: rgba(125, 125, 125, 0.08);
            padding: 6px;
            border-radius: 10px;
        }}

        .stTabs [data-baseweb="tab"] {{
            height: 40px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.9rem;
            border: none !important;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {PRIMARY_COLOR} !important;
            color: #FFFFFF !important;
        }}
        
        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 16px;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_header(ticker_symbol, info, is_etf):
    """动态生成 Header Banner"""
    name = info.get('longName') or info.get('shortName') or ticker_symbol
    quote_type = "ETF 基金" if is_etf else "美股上市公司"
    sector = info.get('sector') or info.get('category') or ("宽基/行业 ETF" if is_etf else "综合分类")
    summary = info.get('longBusinessSummary', '暂无详细描述')
    if len(summary) > 120:
        summary = summary[:120] + "..."

    st.markdown(f"""
    <div class="header-banner">
        <h1>📈 {name} ({ticker_symbol.upper()})</h1>
        <p>类型：<b>{quote_type}</b> | 行业/领域：<b>{sector}</b> | {summary}</p>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_cards(latest_price, price_change, pct_change, week_52_high, week_52_low, div_yield, info, is_etf, size_val):
    """动态渲染 5 大 KPI 卡片 (区分个股与 ETF 关键指标)"""
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        label="最新收盘价 (USD)",
        value=f"${latest_price:.2f}",
        delta=f"{price_change:+.2f} ({pct_change:+.2f}%)"
    )
    col2.metric(
        label="52 周最高 / 最低",
        value=f"${week_52_high:.2f}",
        delta=f"最低: ${week_52_low:.2f}",
        delta_color="off"
    )
    col3.metric(
        label="股息率 (TTM)",
        value=f"{div_yield:.2f}%",
        delta="按近12月派息计算",
        delta_color="off"
    )

    if is_etf:
        expense = info.get('expenseRatio', 0.03)
        if isinstance(expense, (int, float)) and expense < 0.01:
            expense = expense * 100
        col4.metric(
            label="管理费率",
            value=f"{expense}%" if expense else "N/A",
            delta="指数基金费率",
            delta_color="off"
        )
        col5.metric(
            label="资产规模 (AUM)",
            value=f"${size_val / 1e9:.1f} B" if size_val else "N/A",
            delta="基金管理规模",
            delta_color="off"
        )
    else:
        pe_ratio = info.get('trailingPE') or info.get('forwardPE')
        col4.metric(
            label="市盈率 P/E (TTM)",
            value=f"{pe_ratio:.1f}" if pe_ratio else "N/A",
            delta="静态/滚动市盈率",
            delta_color="off"
        )
        col5.metric(
            label="总市值 (Market Cap)",
            value=f"${size_val / 1e9:.1f} B" if size_val else "N/A",
            delta="企业资产规模",
            delta_color="off"
        )
    st.write("")


def render_advice_card(advice):
    st.markdown(f"""
    <div style="background-color: {advice['badge_bg']}; border-left: 5px solid {advice['badge_color']}; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
        <div style="font-size: 1.1rem; font-weight: 700; color: {advice['badge_color']}; margin-bottom: 6px;">
            {advice['title']}
        </div>
        <div style="font-size: 0.9rem; color: #334155; line-height: 1.5;">
            {advice['desc']}
        </div>
        <div style="margin-top: 10px; font-size: 0.82rem; color: #64748B; display: flex; flex-wrap: wrap; gap: 20px;">
            <span>200日均线 (MA200): <b>${advice['ma200']:.2f}</b></span>
            <span>MA200 乖离率: <b>{advice['ma_bias']:+.1f}%</b></span>
            <span>RSI(14): <b>{advice['rsi']:.1f}</b></span>
            <span>52周相对分位数: <b>{advice['position_52w']:.1f}%</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_comparison_chart(df_compare, time_range):
    title_text = "全历史" if time_range == "Max" else f"近 {time_range}"
    st.markdown(f'<div class="section-title">⚔️ 热门美股 / ETF {title_text}累计收益率比拼 (%)</div>', unsafe_allow_html=True)
    
    fig = px.line(
        df_compare, 
        x=df_compare.index, 
        y=df_compare.columns,
        labels={'value': '累计收益率 (%)', 'Date': '日期', 'variable': '代码'},
        template="plotly"
    )
    fig.update_traces(line_width=2.5)
    fig.update_layout(
        height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, title="累计收益率 (%)")
    )
    st.plotly_chart(fig, use_container_width=True)


def render_portfolio_summary_cards(p_metrics):
    """渲染组合顶部的 4 大概览 KPI 卡片（增加外边距与排版空间）"""
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        label="组合总市值 (USD)",
        value=f"${p_metrics['total_market_value']:,.2f}",
        delta=f"总成本: ${p_metrics['total_cost']:,.2f}",
        delta_color="off"
    )
    
    profit_color = "normal" if p_metrics['total_profit'] >= 0 else "inverse"
    col2.metric(
        label="累计浮盈 / 浮亏",
        value=f"${p_metrics['total_profit']:+,.2f}",
        delta=f"{p_metrics['total_profit_pct']:+.2f}%",
        delta_color=profit_color
    )
    
    daily_color = "normal" if p_metrics['daily_gain_loss'] >= 0 else "inverse"
    col3.metric(
        label="预估当日盈亏",
        value=f"${p_metrics['daily_gain_loss']:+,.2f}",
        delta="较前一交易日收盘",
        delta_color=daily_color
    )
    
    pos_count = len(p_metrics['details_df'])
    col4.metric(
        label="持仓标的数量",
        value=f"{pos_count} 只",
        delta="资产分散配置",
        delta_color="off"
    )
    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)


def render_portfolio_charts(p_metrics, sector_p_df):
    """优化组合图表排版，彻底解决图例与饼图重叠遮挡的问题"""
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown('<div class="section-title">🍰 持仓标的资产占比 (%)</div>', unsafe_allow_html=True)
        fig_holdings_pie = px.pie(
            p_metrics['details_df'],
            values='当前总市值 ($)',
            names='代码',
            hole=0.45,
            template="plotly",
            color_discrete_sequence=['#0F766E', '#14B8A6', '#2DD4BF', '#0284C7', '#38BDF8', '#818CF8']
        )
        fig_holdings_pie.update_traces(
            textposition='inside', 
            textinfo='percent',
            hovertemplate="代码: <b>%{label}</b><br>占比: %{percent}<br>市值: <b>$%{value:,.2f}</b><extra></extra>"
        )
        fig_holdings_pie.update_layout(
            # 关键调整 1: 预留充足的底部边距 (b=80)，防止底部的图例与饼图重叠
            margin=dict(l=20, r=20, t=20, b=80), 
            height=360, 
            showlegend=True,
            # 关键调整 2: 精准控制图例在底部居中，并且位于饼图绘制区域下方
            legend=dict(
                orientation="h", 
                yanchor="top", 
                y=-0.15, 
                xanchor="center", 
                x=0.5
            ),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_holdings_pie, use_container_width=True)

    with col_p2:
        st.markdown('<div class="section-title">🧱 组合穿透综合行业配置 (%)</div>', unsafe_allow_html=True)
        if not sector_p_df.empty:
            fig_sec_pie = px.pie(
                sector_p_df,
                values='Weight',
                names='Sector',
                hole=0.45,
                template="plotly",
                color_discrete_sequence=['#0F766E', '#0D9488', '#14B8A6', '#2DD4BF', '#5EEAD4', '#99F6E4', '#334155']
            )
            fig_sec_pie.update_traces(
                textposition='inside', 
                textinfo='percent',
                hovertemplate="行业: <b>%{label}</b><br>穿透权重: <b>%{value:.1f}%</b><extra></extra>"
            )
            fig_sec_pie.update_layout(
                # 关键调整 1: 预留充足的底部边距 (b=80)
                margin=dict(l=20, r=20, t=20, b=80), 
                height=360, 
                showlegend=True,
                # 关键调整 2: 下插图例置于饼图正下方
                legend=dict(
                    orientation="h", 
                    yanchor="top", 
                    y=-0.15, 
                    xanchor="center", 
                    x=0.5
                ),
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_sec_pie, use_container_width=True)
        else:
            st.info("暂无组合行业穿透数据。")


def render_portfolio_advisory(suggestions):
    """渲染投资组合量化管理与诊断建议"""
    st.markdown('<div class="section-title">💡 投资组合健康诊断与优化建议</div>', unsafe_allow_html=True)
    
    for item in suggestions:
        if item['level'] == "WARNING":
            bg_color = "rgba(239, 68, 68, 0.1)"
            border_color = "#EF4444"
            text_color = "#991B1B"
        elif item['level'] == "SUCCESS":
            bg_color = "rgba(15, 118, 110, 0.1)"
            border_color = "#0F766E"
            text_color = "#0F766E"
        else:
            bg_color = "rgba(59, 130, 246, 0.1)"
            border_color = "#3B82F6"
            text_color = "#1E40AF"

        st.markdown(f"""
        <div style="background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 14px 18px; border-radius: 8px; margin-bottom: 12px;">
            <div style="font-size: 0.95rem; font-weight: 700; color: {text_color}; margin-bottom: 4px;">
                {item['title']}
            </div>
            <div style="font-size: 0.88rem; opacity: 0.9; line-height: 1.5;">
                {item['desc']}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_rebalance_dashboard(rebalance_df, total_current_val, target_total_val, new_cash):
    """渲染一键再平衡计算面板与可视化交易指令"""
    st.markdown('<div class="section-title">⚖️ 投资组合一键再平衡计算器 (Rebalance Assistant)</div>', unsafe_allow_html=True)
    
    # 顶部状态卡片
    col1, col2, col3 = st.columns(3)
    col1.metric("当前组合总市值", f"${total_current_val:,.2f}")
    col2.metric("计划新增入金", f"${new_cash:,.2f}")
    col3.metric("再平衡后预计总资产", f"${target_total_val:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🛒 调仓交易指令明细")
    
    if not rebalance_df.empty:
        # 显示目标权重校验警告
        total_target_pct = rebalance_df["目标权重 (%)"].sum()
        if abs(total_target_pct - 100.0) > 0.1:
            st.warning(f"⚠️ 当前目标权重之和为 **{total_target_pct:.1f}%**，建议调整编辑表格使目标权重之和等于 **100%**。")
        else:
            st.success("✅ 目标权重设定完美（合计 100%）。")

        st.dataframe(
            rebalance_df,
            column_config={
                "代码": st.column_config.TextColumn("代码", width="small"),
                "当前股价 ($)": st.column_config.NumberColumn("当前股价", format="$%.2f"),
                "当前市值 ($)": st.column_config.NumberColumn("当前市值", format="$%.2f"),
                "当前实际权重 (%)": st.column_config.NumberColumn("实际权重", format="%.1f%%"),
                "目标权重 (%)": st.column_config.NumberColumn("目标权重", format="%.1f%%"),
                "权重偏差 (%)": st.column_config.NumberColumn("偏差 (%)", format="%+.1f%%"),
                "再平衡建议动作": st.column_config.TextColumn("建议动作", width="medium"),
                "调整金额 ($)": st.column_config.NumberColumn("建议交易金额", format="$%.2f"),
                "调整股数": st.column_config.NumberColumn("建议交易股数", format="%.2f 股")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("暂无有效持仓数据进行再平衡计算。")


def render_dividend_dashboard(div_metrics):
    """渲染股息现金流预估看板与月度现金流柱状图"""
    st.markdown('<div class="section-title">💵 投资组合被动现金流与股息预估 (Dividend Flow)</div>', unsafe_allow_html=True)
    
    # 顶部 3 大现金流核心指标
    col1, col2, col3 = st.columns(3)
    col1.metric("组合穿透加权股息率", f"{div_metrics['portfolio_div_yield']:.2f}%")
    col2.metric("预计年化被动现金流", f"${div_metrics['total_annual_cashflow']:,.2f}")
    col3.metric("预计平均月度现金流", f"${div_metrics['total_annual_cashflow'] / 12:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart, col_table = st.columns([1.3, 1])
    
    # 左侧：月度现金流预估柱状图
    with col_chart:
        st.markdown("##### 📅 预估未来 12 个月领息日历 ($)")
        fig_div_bar = px.bar(
            div_metrics['monthly_df'],
            x="月份",
            y="预计领息 ($)",
            text_auto=".0f", # type: ignore
            template="plotly"
        )
        fig_div_bar.update_traces(
            marker_color="#0F766E",
            textposition="outside"
        )
        fig_div_bar.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="",
            yaxis_title="",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True)
        )
        st.plotly_chart(fig_div_bar, use_container_width=True)

    # 右侧：各标的派息明细表
    with col_table:
        st.markdown("##### 📋 各标的股息贡献明细")
        st.dataframe(
            div_metrics['breakdown_df'],
            column_config={
                "代码": st.column_config.TextColumn("代码", width="small"),
                "当前持仓市值 ($)": st.column_config.NumberColumn("持仓市值", format="$%.2f"),
                "股息率 (TTM %)": st.column_config.NumberColumn("股息率", format="%.2f%%"),
                "预计年领股息 ($)": st.column_config.NumberColumn("预计年股息", format="$%.2f"),
                "历史派息月份": st.column_config.TextColumn("派息月份", width="medium")
            },
            hide_index=True,
            use_container_width=True,
            height=320
        )