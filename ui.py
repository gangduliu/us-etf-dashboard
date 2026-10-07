import streamlit as st
import plotly.express as px
from datetime import datetime

def get_theme_config(dark_active):
    """根据主题切换状态返回色彩参数"""
    if dark_active:
        return {
            "THEME_MAIN": "#26B0A1",
            "THEME_MAIN_LIGHT": "#5EEAD4",
            "THEME_BG": "#0F172A",
            "THEME_CARD": "#1E293B",
            "THEME_TEXT_DARK": "#F8FAFC",
            "THEME_TEXT_MUTED": "#94A3B8",
            "THEME_BORDER": "#334155",
            "PLOTLY_TEMPLATE": "plotly_dark",
            "CALC_BG": "#132322",
            "CALC_BORDER": "#14532D",
            "CALC_TEXT": "#4ADE80"
        }
    else:
        return {
            "THEME_MAIN": "#0F766E",
            "THEME_MAIN_LIGHT": "#14B8A6",
            "THEME_BG": "#F8FAFC",
            "THEME_CARD": "#FFFFFF",
            "THEME_TEXT_DARK": "#0F172A",
            "THEME_TEXT_MUTED": "#64748B",
            "THEME_BORDER": "#E2E8F0",
            "PLOTLY_TEMPLATE": "plotly_white",
            "CALC_BG": "#F0FDF4",
            "CALC_BORDER": "#BBF7D0",
            "CALC_TEXT": "#15803D"
        }


def inject_custom_css(theme):
    """注入全套 CSS 渲染与卡片对齐样式"""
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .stApp {{
            background-color: {theme['THEME_BG']};
            color: {theme['THEME_TEXT_DARK']};
        }}
        
        .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1280px;
        }}

        [data-testid="stSidebar"] {{
            background-color: {theme['THEME_CARD']};
            border-right: 1px solid {theme['THEME_BORDER']};
        }}
        
        .header-banner {{
            background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%);
            padding: 24px 32px;
            border-radius: 16px;
            color: #FFFFFF;
            margin-bottom: 24px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
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
            background-color: {theme['THEME_CARD']};
            padding: 18px 20px;
            border-radius: 12px;
            border: 1px solid {theme['THEME_BORDER']};
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease-in-out;
            position: relative;
            overflow: hidden;
            min-height: 110px;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.15);
        }}
        [data-testid="stMetric"]::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, {theme['THEME_MAIN']}, {theme['THEME_MAIN_LIGHT']});
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {theme['THEME_TEXT_MUTED']} !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
        }}
        
        [data-testid="stMetricValue"] {{
            color: {theme['THEME_TEXT_DARK']} !important;
            font-weight: 700 !important;
            font-size: 1.5rem !important;
            letter-spacing: -0.02em;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: {theme['THEME_CARD']};
            padding: 6px;
            border-radius: 10px;
            border: 1px solid {theme['THEME_BORDER']};
        }}

        .stTabs [data-baseweb="tab"] {{
            height: 40px;
            border-radius: 6px;
            color: {theme['THEME_TEXT_MUTED']};
            font-weight: 600;
            font-size: 0.9rem;
            border: none !important;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {theme['THEME_MAIN']} !important;
            color: #FFFFFF !important;
        }}
        
        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            color: {theme['THEME_TEXT_DARK']};
            margin-bottom: 16px;
        }}

        hr {{
            border-color: {theme['THEME_BORDER']};
            margin: 1.5rem 0;
        }}
    </style>
    """, unsafe_allow_html=True)


def render_header(selected_ticker, meta):
    """渲染支持标的切替的 Header Banner"""
    st.markdown(f"""
    <div class="header-banner">
        <h1>📈 {meta['name']} ({selected_ticker})</h1>
        <p>定位：<b>{meta['category']}</b> | {meta['desc']} | 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_cards(latest_price, price_change, pct_change, week_52_high, week_52_low, div_yield, expense_ratio, total_assets):
    """渲染高度对齐的顶部 5 大核心 KPI 卡片"""
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        label="最新收盘价 (USD)",
        value=f"${latest_price:.2f}",
        delta=f"{price_change:+.2f} ({pct_change:+.2f}%)"
    )
    col2.metric(
        label="52 周最高 / 最低",
        value=f"${week_52_high:.1f}",
        delta=f"最低: ${week_52_low:.1f}",
        delta_color="off"
    )
    col3.metric(
        label="股息率 (TTM)",
        value=f"{div_yield:.2f}%",
        delta="按近12月派息计算",
        delta_color="off"
    )
    col4.metric(
        label="管理费率",
        value=f"{expense_ratio}%",
        delta="极低费率",
        delta_color="off"
    )
    col5.metric(
        label="资产规模 (AUM)",
        value=f"${total_assets / 1e9:.1f} B" if total_assets else "N/A",
        delta="跟踪标普500指数",
        delta_color="off"
    )
    st.write("")


def render_advice_card(advice):
    """渲染买入策略建议 Banner"""
    st.markdown(f"""
    <div style="background-color: {advice['badge_bg']}; border-left: 5px solid {advice['badge_color']}; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
        <div style="font-size: 1.1rem; font-weight: 700; color: {advice['badge_color']}; margin-bottom: 6px;">
            {advice['title']}
        </div>
        <div style="font-size: 0.9rem; color: #334155; line-height: 1.5;">
            {advice['desc']}
        </div>
        <div style="margin-top: 10px; font-size: 0.82rem; color: #64748B; display: flex; gap: 20px;">
            <span>200日均线 (MA200): <b>${advice['ma200']:.2f}</b></span>
            <span>MA200 乖离率: <b>{advice['ma_bias']:+.1f}%</b></span>
            <span>52周相对分位数: <b>{advice['position_52w']:.1f}%</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_comparison_chart(df_compare, theme):
    """渲染 VOO vs VGT vs SCHD 10年累计收益率对比图"""
    st.markdown('<div class="section-title">⚔️ VOO / VGT / SCHD 近 10 年累计收益率比拼 (%)</div>', unsafe_allow_html=True)
    
    fig = px.line(
        df_compare, 
        x=df_compare.index, 
        y=df_compare.columns,
        labels={'value': '累计收益率 (%)', 'Date': '日期', 'variable': '标的'},
        template=theme['PLOTLY_TEMPLATE']
    )
    fig.update_traces(line_width=2.5)
    fig.update_layout(
        height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=theme['THEME_BORDER'], title="累计收益率 (%)")
    )
    st.plotly_chart(fig, use_container_width=True)