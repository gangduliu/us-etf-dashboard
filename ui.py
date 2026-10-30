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

        /* Tab List Container: Modern capsule base, adaptive background and border */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: var(--secondary-background-color);
            padding: 6px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            margin-bottom: 20px;
        }}

        /* Individual Tab Button: 0.25s smooth bezier transition */
        .stTabs [data-baseweb="tab"] {{
            height: 40px;
            border-radius: 8px !important;
            color: var(--text-color) !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            border: none !important;
            background-color: transparent !important;
            padding: 0 16px !important;
        }}

        /* Hover effect: Smooth subtle glow and text color shift */
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: rgba(15, 118, 110, 0.08) !important;
            color: var(--primary-color) !important;
        }}

        /* Selected Tab state: Primary color fill with shadow */
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: var(--primary-color) !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(15, 118, 110, 0.25);
        }}

        /* Hide default bottom highlight bar */
        .stTabs [data-baseweb="tab-highlight"] {{
            display: none !important;
        }}
        
        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 16px;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_header(ticker_symbol, info, is_etf):
    """Dynamically generate Header Banner"""
    name = info.get('longName') or info.get('shortName') or ticker_symbol
    quote_type = "ETF Fund" if is_etf else "US Listed Company"
    sector = info.get('sector') or info.get('category') or ("Broad/Sector ETF" if is_etf else "General Classification")
    summary = info.get('longBusinessSummary', 'No detailed description available.')
    if len(summary) > 120:
        summary = summary[:120] + "..."

    st.markdown(f"""
    <div class="header-banner">
        <h1>📈 {name} ({ticker_symbol.upper()})</h1>
        <p>Type: <b>{quote_type}</b> | Sector/Category: <b>{sector}</b> | {summary}</p>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_cards(latest_price, price_change, pct_change, week_52_high, week_52_low, div_yield, info, is_etf, size_val):
    """Dynamically render 5 main KPI cards (distinction between Stocks & ETFs)"""
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        label="Latest Price (USD)",
        value=f"${latest_price:.2f}",
        delta=f"{price_change:+.2f} ({pct_change:+.2f}%)"
    )
    col2.metric(
        label="52-Week High / Low",
        value=f"${week_52_high:.2f}",
        delta=f"Low: ${week_52_low:.2f}",
        delta_color="off"
    )
    col3.metric(
        label="Dividend Yield (TTM)",
        value=f"{div_yield:.2f}%",
        delta="Based on last 12M payouts",
        delta_color="off"
    )

    if is_etf:
        expense = info.get('expenseRatio', 0.03)
        if isinstance(expense, (int, float)) and expense < 0.01:
            expense = expense * 100
        col4.metric(
            label="Expense Ratio",
            value=f"{expense}%" if expense else "N/A",
            delta="Index fund fee",
            delta_color="off"
        )
        col5.metric(
            label="AUM",
            value=f"${size_val / 1e9:.1f} B" if size_val else "N/A",
            delta="Fund AUM",
            delta_color="off"
        )
    else:
        pe_ratio = info.get('trailingPE') or info.get('forwardPE')
        col4.metric(
            label="P/E Ratio (TTM)",
            value=f"{pe_ratio:.1f}" if pe_ratio else "N/A",
            delta="Trailing / Forward P/E",
            delta_color="off"
        )
        col5.metric(
            label="Market Cap",
            value=f"${size_val / 1e9:.1f} B" if size_val else "N/A",
            delta="Total valuation",
            delta_color="off"
        )
    st.write("")


def render_advice_card(advice):
    """Render multi-factor quant trading decision banner (includes suggested buy/sell price)"""
    
    buy_price = advice.get('suggested_buy_price', None)
    sell_price = advice.get('suggested_sell_price', None)
    
    buy_str = f"${buy_price:.2f}" if buy_price is not None else "N/A"
    sell_str = f"${sell_price:.2f}" if sell_price is not None else "N/A"

    st.markdown(f"""
    <div style="background-color: {advice['badge_bg']}; border-left: 5px solid {advice['badge_color']}; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
        <div style="font-size: 1.1rem; font-weight: 700; color: {advice['badge_color']}; margin-bottom: 6px;">
            {advice['title']}
        </div>
        <div style="font-size: 0.9rem; color: #334155; line-height: 1.5;">
            {advice['desc']}
        </div>
        <!-- Target Price & Score Display -->
        <div style="display: flex; gap: 16px; align-items: center; padding: 10px 0;">
            <div style="flex: 1;">
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 500;">🟢 Suggested Buy Price</div>
                <div style="font-size: 1.0rem; font-weight: 700; color: #166534; margin-top: 2px;">{buy_str}</div>
            </div>
            <div style="flex: 1;">
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 500;">🔴 Suggested Sell Price</div>
                <div style="font-size: 1.0rem; font-weight: 700; color: #991B1B; margin-top: 2px;">{sell_str}</div>
            </div>
        </div>
        <div style="font-size: 0.82rem; color: #64748B; display: flex; flex-wrap: wrap; gap: 16px;">
            <span>Quant Score: <b>{advice.get('score', 0):+} pts</b></span>
            <span>MA200: <b>${advice['ma200']:.2f}</b></span>
            <span>MA200 Bias: <b>{advice['ma_bias']:+.1f}%</b></span>
            <span>RSI(14): <b>{advice['rsi']:.1f}</b></span>
            <span>Bollinger %B: <b>{advice.get('pct_b', 50):.1f}%</b></span>
            <span>52W Percentile: <b>{advice['position_52w']:.1f}%</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_advanced_comparison_chart(df_compare, y_axis_title):
    fig = px.line(
        df_compare, 
        x=df_compare.index, 
        y=df_compare.columns,
        labels={'value': y_axis_title, 'Date': 'Trading Date', 'variable': 'Ticker'},
        template="plotly",
    )
    fig.update_traces(line_width=2.5)
    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=10, b=0),
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(200, 200, 200, 0.2)', title=y_axis_title),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)


def render_portfolio_summary_cards(p_metrics):
    """Render top 4 summary KPI cards for portfolio"""
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        label="Total Market Value (USD)",
        value=f"${p_metrics['total_market_value']:,.2f}",
        delta=f"Total Cost: ${p_metrics['total_cost']:,.2f}",
        delta_color="off"
    )
    
    profit_color = "normal" if p_metrics['total_profit'] >= 0 else "inverse"
    col2.metric(
        label="Total Unrealized P&L",
        value=f"${p_metrics['total_profit']:+,.2f}",
        delta=f"{p_metrics['total_profit_pct']:+.2f}%",
    )
    
    daily_color = "normal" if p_metrics['daily_gain_loss'] >= 0 else "inverse"
    col3.metric(
        label="Est. Daily Gain/Loss",
        value=f"${p_metrics['daily_gain_loss']:+,.2f}",
        delta=f"{p_metrics['daily_gain_loss_pct']:+.2f}%",
    )
    
    pos_count = len(p_metrics['details_df'])
    col4.metric(
        label="Holdings Count",
        value=f"{pos_count} Assets",
        delta="Diversified Allocation",
        delta_color="off"
    )
    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)


def render_portfolio_charts(p_metrics, sector_p_df):
    """Render portfolio charts with optimized legend position"""
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown('<div class="section-title">🍰 Asset Allocation (%)</div>', unsafe_allow_html=True)
        fig_holdings_pie = px.pie(
            p_metrics['details_df'],
            values='Current Market Value ($)',
            names='Ticker',
            hole=0.45,
            template="plotly",
            color_discrete_sequence=['#0F766E', '#14B8A6', '#2DD4BF', '#0284C7', '#38BDF8', '#818CF8']
        )
        fig_holdings_pie.update_traces(
            textposition='inside', 
            textinfo='percent',
            hovertemplate="Ticker: <b>%{label}</b><br>Share: %{percent}<br>Market Value: <b>$%{value:,.2f}</b><extra></extra>"
        )
        fig_holdings_pie.update_layout(
            margin=dict(l=20, r=20, t=20, b=80), 
            height=360, 
            showlegend=True,
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
        st.markdown('<div class="section-title">🧱 Look-Through Sector Breakdown (%)</div>', unsafe_allow_html=True)
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
                hovertemplate="Sector: <b>%{label}</b><br>Weight: <b>%{value:.1f}%</b><extra></extra>"
            )
            fig_sec_pie.update_layout(
                margin=dict(l=20, r=20, t=20, b=80), 
                height=360, 
                showlegend=True,
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
            st.info("No look-through sector breakdown data available.")


def render_portfolio_advisory(suggestions):
    """Render portfolio health diagnostic & recommendation cards"""
    st.markdown('<div class="section-title">💡 Portfolio Health Diagnostic & Advisory</div>', unsafe_allow_html=True)
    
    for item in suggestions:
        if item['level'] == "DANGER":
            border_color = "#EF4444"
            bg_color = "rgba(239, 68, 68, 0.15)"
            title_color = "#F87171"
        elif item['level'] == "WARNING":
            border_color = "#F59E0B"
            bg_color = "rgba(245, 158, 11, 0.15)"
            title_color = "#FBBF24"
        elif item['level'] == "SUCCESS":
            border_color = "#10B981"
            bg_color = "rgba(16, 185, 129, 0.15)"
            title_color = "#34D399"
        else: # INFO
            border_color = "#3B82F6"
            bg_color = "rgba(59, 130, 246, 0.15)"
            title_color = "#60A5FA"

        st.markdown(f"""
        <div style="background-color: {bg_color}; border-left: 5px solid {border_color}; padding: 14px 18px; border-radius: 8px; margin-bottom: 12px; backdrop-filter: blur(4px);">
            <div style="font-size: 0.95rem; font-weight: 700; color: {title_color}; margin-bottom: 6px;">
                {item['title']}
            </div>
            <div style="font-size: 0.88rem; line-height: 1.55; color: var(--text-color); opacity: 0.95;">
                {item['desc']}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_rebalance_dashboard(rebalance_df, total_current_val, target_total_val, new_cash):
    """Render rebalance calculator dashboard & trade actions"""
    st.markdown('<div class="section-title">⚖️ Portfolio Rebalance Assistant</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Portfolio Value", f"${total_current_val:,.2f}")
    col2.metric("Planned Cash Inflow", f"${new_cash:,.2f}")
    col3.metric("Est. Total Value Post-Rebalance", f"${target_total_val:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🛒 Rebalance Trade Instructions")
    
    if not rebalance_df.empty:
        total_target_pct = rebalance_df["Target Weight (%)"].sum() if "Target Weight (%)" in rebalance_df.columns else rebalance_df.get("目标权重 (%)", pd.Series([100])).sum()
        if abs(total_target_pct - 100.0) > 0.1:
            st.warning(f"⚠️ Current target weight sum is **{total_target_pct:.1f}%**. Consider adjusting so the sum equals **100%**.")
        else:
            st.success("✅ Target weight settings are valid (Total: 100%).")

        st.dataframe(
            rebalance_df,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Current Price ($)": st.column_config.NumberColumn("Current Price", format="$%.2f"),
                "Current Value ($)": st.column_config.NumberColumn("Current Value", format="$%.2f"),
                "Actual Weight (%)": st.column_config.NumberColumn("Actual Weight", format="%.1f%%"),
                "Target Weight (%)": st.column_config.NumberColumn("Target Weight", format="%.1f%%"),
                "Deviation (%)": st.column_config.NumberColumn("Deviation (%)", format="%+.1f%%"),
                "Action": st.column_config.TextColumn("Action", width="medium"),
                "Trade Amount ($)": st.column_config.NumberColumn("Trade Amount", format="$%.2f"),
                "Trade Shares": st.column_config.NumberColumn("Trade Shares", format="%.2f shares")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No valid holdings data available for rebalance calculation.")


def render_dividend_dashboard(div_metrics):
    """Render dividend cashflow dashboard & monthly projections"""
    st.markdown('<div class="section-title">💵 Passive Income & Dividend Flow</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Weighted Portfolio Div Yield", f"{div_metrics['portfolio_div_yield']:.2f}%")
    col2.metric("Est. Annual Passive Cashflow", f"${div_metrics['total_annual_cashflow']:,.2f}")
    col3.metric("Est. Average Monthly Cashflow", f"${div_metrics['total_annual_cashflow'] / 12:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("##### 📅 Projected 12-Month Dividend Schedule ($)")
    fig_div_bar = px.bar(
        div_metrics['monthly_df'],
        x="Month" if "Month" in div_metrics['monthly_df'].columns else "月份",
        y="Est. Dividends ($)" if "Est. Dividends ($)" in div_metrics['monthly_df'].columns else "预计领息 ($)",
        text_auto=".2f", # type: ignore
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

    st.markdown("##### 📋 Dividend Breakdown by Asset")
    st.dataframe(
        div_metrics['breakdown_df'],
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Market Value ($)": st.column_config.NumberColumn("Market Value", format="$%.2f"),
            "Dividend Yield (TTM %)": st.column_config.NumberColumn("Dividend Yield", format="%.2f%%"),
            "Est. Annual Dividend ($)": st.column_config.NumberColumn("Est. Annual Div", format="$%.2f"),
            "Payout Months": st.column_config.TextColumn("Payout Months", width="medium")
        },
        hide_index=True,
        use_container_width=True,
    )