import os

# 本地代理软件的 HTTP/SOCKS 端口
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'


import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ==========================================
# 1. 页面基本配置
# ==========================================
st.set_page_config(
    page_title="VOO Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. 主题状态与切换按钮逻辑
# ==========================================
# 初始化 session_state 中的主题状态
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# with st.sidebar:
#     st.markdown("### ⚙️ 看板配置")
#     st.caption("界面与数据参数")
    
#     # 快捷主题切换 Toggle 开关
#     st.session_state.dark_mode = st.toggle("🌙 深色模式 (Dark Mode)", value=st.session_state.dark_mode)

dark_active = st.session_state.dark_mode

# ==========================================
# 3. 动态配色表 (根据开关状态自动切换)
# ==========================================
if dark_active:
    # 深色模式配色 (Slate 900 风格)
    THEME_MAIN = "#26B0A1"         # 亮青绿
    THEME_MAIN_LIGHT = "#5EEAD4"   # 薄荷绿高亮
    THEME_BG = "#0F172A"           # 深蓝灰底色
    THEME_CARD = "#1E293B"         # 卡片深灰底
    THEME_TEXT_DARK = "#F8FAFC"    # 主文字
    THEME_TEXT_MUTED = "#94A3B8"   # 次要灰字
    THEME_BORDER = "#334155"       # 深色边框
    PLOTLY_TEMPLATE = "plotly_dark"
    CALC_BG = "#132322"
    CALC_BORDER = "#14532D"
    CALC_TEXT = "#4ADE80"
else:
    # 明亮模式配色 (Slate 50 风格)
    THEME_MAIN = "#0F766E"         # 深青绿
    THEME_MAIN_LIGHT = "#14B8A6"   # 亮青绿
    THEME_BG = "#F8FAFC"           # 浅灰底色
    THEME_CARD = "#FFFFFF"         # 卡片纯白底
    THEME_TEXT_DARK = "#0F172A"    # 主文字
    THEME_TEXT_MUTED = "#64748B"   # 次要灰字
    THEME_BORDER = "#E2E8F0"       # 浅灰边框
    PLOTLY_TEMPLATE = "plotly_white"
    CALC_BG = "#F0FDF4"
    CALC_BORDER = "#BBF7D0"
    CALC_TEXT = "#15803D"

# ==========================================
# 4. CSS 注入
# ==========================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* 全局背景与外边距调整 */
    .stApp {{
        background-color: {THEME_BG};
        color: {THEME_TEXT_DARK};
    }}
    
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1280px;
    }}

    /* 侧边栏重构 */
    [data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid {THEME_BORDER};
    }}
    
    /* 顶部 Hero Header Banner 包装 */
    .header-banner {{
        background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(15, 118, 110, 0.15);
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

    /* Metric 卡片精美化与悬浮微效果 */
    [data-testid="stMetric"] {{
        background-color: {THEME_CARD};
        padding: 18px 20px;
        border-radius: 12px;
        border: 1px solid {THEME_BORDER};
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease-in-out;
        position: relative;
        overflow: hidden;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.08);
        border-color: #CBD5E1;
    }}
    /* 卡片顶部装饰线条 */
    [data-testid="stMetric"]::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, {THEME_MAIN}, {THEME_MAIN_LIGHT});
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {THEME_TEXT_MUTED} !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }}
    
    [data-testid="stMetricValue"] {{
        color: {THEME_TEXT_DARK} !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        letter-spacing: -0.02em;
    }}

    /* 现代感 Tabs 标签页导航 */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: #F1F5F9;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid {THEME_BORDER};
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        border-radius: 6px;
        color: {THEME_TEXT_MUTED};
        font-weight: 600;
        font-size: 0.9rem;
        border: none !important;
        transition: all 0.15s ease;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: #FFFFFF !important;
        color: {THEME_MAIN} !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    
    /* 容器 Card 包装 */
    .custom-card {{
        background-color: {THEME_CARD};
        padding: 24px;
        border-radius: 14px;
        border: 1px solid {THEME_BORDER};
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
    }}

    /* 自定义标题层级样式 */
    .section-title {{
        font-size: 1.1rem;
        font-weight: 700;
        color: {THEME_TEXT_DARK};
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    /* 分割线微调 */
    hr {{
        border-color: {THEME_BORDER};
        margin: 1.5rem 0;
    }}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. 数据获取与缓存
# ==========================================
@st.cache_data(ttl=3600)
def load_voo_data():
    ticker = yf.Ticker("VOO")
    hist = ticker.history(period="max")
    if hist.empty:
        raise ValueError("未能获取到历史价格数据")
    hist.index = hist.index.tz_localize(None)
    
    info_raw = ticker.info
    info = {k: v for k, v in info_raw.items() if isinstance(v, (int, float, str, bool, list, dict))}
    
    dividends = ticker.dividends
    if not dividends.empty:
        dividends.index = dividends.index.tz_localize(None)
        
    return hist, info, dividends


try:
    hist, info, dividends = load_voo_data()
except Exception as e:
    st.error(f"获取数据失败，请检查网络设置或稍后再试: {e}")
    st.stop()


# 数据获取（包含实时行业分布与重仓股）
@st.cache_data(ttl=86400)  # 持仓与行业权重变化较慢，缓存可设为 24 小时
def load_voo_holdings_and_sectors():
    ticker = yf.Ticker("VOO")
    
    sector_df = pd.DataFrame()
    holdings_df = pd.DataFrame()
    
    try:
        funds_data = ticker.funds_data
        
        # 1. 获取行业分布 (Sector Weightings)
        if hasattr(funds_data, 'sector_weightings') and funds_data.sector_weightings:
            sectors = funds_data.sector_weightings
            sector_df = pd.DataFrame(list(sectors.items()), columns=['Sector', 'Weight'])
            # 权重换算为百分比
            sector_df['Weight'] = sector_df['Weight'] * 100
        
        # 2. 获取 Top 10 重仓股 (Top Holdings)
        if hasattr(funds_data, 'top_holdings') and funds_data.top_holdings is not None:
            holdings_raw = funds_data.top_holdings.reset_index()
            holdings_raw.columns = ['Ticker', 'Company', 'Weight (%)']
            holdings_raw['Weight (%)'] = holdings_raw['Weight (%)'] * 100
            holdings_df = holdings_raw.head(10)
    except Exception as e:
        pass

    # 兜底数据（防止 yfinance API 接口返回空数据或频控时卡死）
    if sector_df.empty:
        sector_df = pd.DataFrame({
            "Sector": ["信息技术", "金融", "医疗健康", "可选消费", "通讯服务", "工业", "必需消费", "其他"],
            "Weight": [31.5, 13.2, 11.8, 10.2, 8.9, 8.3, 5.8, 10.3]
        })
        
    if holdings_df.empty:
        holdings_df = pd.DataFrame({
            "Ticker": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "BRK.B", "LLY", "AVGO", "TSLA"],
            "Company": ["Apple Inc.", "Microsoft Corp.", "NVIDIA Corp.", "Amazon.com Inc.", "Meta Platforms", "Alphabet Inc.", "Berkshire Hathaway", "Eli Lilly", "Broadcom Inc.", "Tesla Inc."],
            "Weight (%)": [6.8, 6.5, 6.1, 3.6, 2.4, 2.0, 1.7, 1.5, 1.4, 1.3]
        })

    return sector_df, holdings_df


# ==========================================
# 4. 侧边栏设置 (Sidebar)
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ 看板配置")
    st.caption("定制视角与参数配置")
    
    time_range = st.selectbox(
        "时间跨度筛选",
        options=["1Y", "3Y", "5Y", "10Y", "Max"],
        index=3
    )
    
    st.divider()
    st.markdown("#### 💡 关于 VOO")
    st.caption(
        "Vanguard S&P 500 ETF (VOO) 追踪标普 500 指数，"
        "包含美国 500 家顶尖上市公司，是全球最具代表性的宽基指数基金之一。"
    )

def filter_by_range(df, range_str):
    now = datetime.now()
    if range_str == "1Y":
        start = now - timedelta(days=365)
    elif range_str == "3Y":
        start = now - timedelta(days=365*3)
    elif range_str == "5Y":
        start = now - timedelta(days=365*5)
    elif range_str == "10Y":
        start = now - timedelta(days=365*10)
    else:
        return df
    return df[df.index >= start]

filtered_hist = filter_by_range(hist, time_range)


# ==========================================
# 5. 顶部 Header 区域
# ==========================================
st.markdown(f"""
<div class="header-banner">
    <h1>📈 Vanguard S&P 500 ETF (VOO)</h1>
    <p>实时跟踪标普 500 指数 | 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>
""", unsafe_allow_html=True)


# ==========================================
# 6. 核心 KPI 指标区
# ==========================================
latest_price = hist['Close'].iloc[-1]
prev_price = hist['Close'].iloc[-2]
price_change = latest_price - prev_price
pct_change = (price_change / prev_price) * 100

week_52_high = info.get('fiftyTwoWeekHigh', hist['Close'].tail(252).max())
week_52_low = info.get('fiftyTwoWeekLow', hist['Close'].tail(252).min())

# --- 🛠️ 动态准确计算近12个月 (TTM) 真实股息率 ---
if not dividends.empty:
    # 筛选过去 365 天内的实际分红记录
    one_year_ago = datetime.now() - timedelta(days=365)
    recent_divs = dividends[dividends.index >= one_year_ago]
    ttm_dividends = recent_divs.sum()
    
    # 真实 TTM 股息率 (%) = 近一年总分红 / 当前最新股价 * 100
    div_yield = (ttm_dividends / latest_price) * 100
else:
    # 兜底容错逻辑 (处理 yfinance API 数据缺失)
    raw_yield = info.get('dividendYield', 0.012)
    div_yield = raw_yield * 100 if raw_yield < 0.2 else raw_yield

expense_ratio = 0.03

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
    delta="按近12月派息计算",  # 占位文本
    delta_color="off"         # off 表示使用中性灰，不显示红绿箭头
)
col4.metric(
    label="管理费率",
    value=f"{expense_ratio}%",
    delta="极低费率"
)
col5.metric(
    label="资产规模 (AUM)",
    value=f"${info.get('totalAssets', 0) / 1e9:.1f} B" if info.get('totalAssets') else "N/A",
    delta="跟踪标普500指数",   # 占位文本
    delta_color="off"
)

st.write("") # 增加适度空行


# ==========================================
# 7. 标签页主体 (Tabs)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 价格走势与投资计算器", "🧩 行业分布与重仓股", "💰 历史回报与分红"])

# ==========================================
# 估值与投资策略评估逻辑
# ==========================================
def analyze_buy_signal(hist, latest_price, week_52_high, week_52_low):
    # 1. 计算 200 日均线 (MA200)
    ma200 = hist['Close'].tail(200).mean() if len(hist) >= 200 else hist['Close'].mean()
    
    # 2. 计算当前价格处于 52 周范围的百分比区间 (0% = 最低, 100% = 最高)
    range_52 = week_52_high - week_52_low
    position_52w = ((latest_price - week_52_low) / range_52 * 100) if range_52 > 0 else 50
    
    # 3. 价格相对于 MA200 的偏离度
    ma_bias = ((latest_price - ma200) / ma200) * 100
    
    # 4. 综合建议逻辑判断
    if latest_price < ma200:
        signal_title = "🟢 具备较高性价比 / 黄金加仓期"
        signal_desc = f"当前价格已低于 200 日均线 (${ma200:.2f})，处于中长期价值区间。对于长期投资者而言，具备较好的分批建仓/大额加仓性价比。"
        badge_color = "#166534" # 深绿
        badge_bg = "#DCFCE7"
    elif position_52w > 85 and ma_bias > 8:
        signal_title = "🟡 处于短期高位 / 建议逢低定投"
        signal_desc = f"价格靠近 52 周高点附近（偏离 200 日均线 {ma_bias:+.1f}%），短期可能有震荡回调风险。建议避免一次性重仓追高，优先采取**分批定投策略**。"
        badge_color = "#854D0E" # 黄色
        badge_bg = "#FEF9C3"
    else:
        signal_title = "🔵 趋势健康 / 适合定期定额常态化配置"
        signal_desc = f"价格保持在 200 日均线 (${ma200:.2f}) 之上运行，整体上升趋势健全。适合按既定计划进行**常规定投**。"
        badge_color = "#1E40AF" # 蓝色
        badge_bg = "#DBEAFE"
        
    return {
        "title": signal_title,
        "desc": signal_desc,
        "ma200": ma200,
        "position_52w": position_52w,
        "ma_bias": ma_bias,
        "badge_color": badge_color,
        "badge_bg": badge_bg
    }

# 得到分析结果
buy_advice = analyze_buy_signal(hist, latest_price, week_52_high, week_52_low)

# ------------------------------------------
# Tab 1: 价格走势与投资计算器
# ------------------------------------------
with tab1:
    # 投资建议 UI Banner
    st.markdown(f"""
    <div style="background-color: {buy_advice['badge_bg']}; border-left: 5px solid {buy_advice['badge_color']}; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
        <div style="font-size: 1.1rem; font-weight: 700; color: {buy_advice['badge_color']}; margin-bottom: 6px;">
            {buy_advice['title']}
        </div>
        <div style="font-size: 0.9rem; color: #334155; line-height: 1.5;">
            {buy_advice['desc']}
        </div>
        <div style="margin-top: 10px; font-size: 0.82rem; color: #64748B; display: flex; gap: 20px;">
            <span>200日均线 (MA200): <b>${buy_advice['ma200']:.2f}</b></span>
            <span>MA200 乖离率: <b>{buy_advice['ma_bias']:+.1f}%</b></span>
            <span>52周相对分位数: <b>{buy_advice['position_52w']:.1f}%</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_chart, col_calc = st.columns([2.2, 1])
    
    with col_chart:
        st.markdown('<div class="section-title">📉 历史价格走势曲线</div>', unsafe_allow_html=True)
        
        # 渐变填充与精细线条 Plotly 图表
        fig_price = px.line(
            filtered_hist, 
            x=filtered_hist.index, 
            y='Close',
            labels={'Close': '收盘价 (USD)', 'Date': '日期'},
            template='plotly_white'
        )
        fig_price.update_traces(
            line_color=THEME_MAIN, 
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
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', title="")
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

        # 计算结果亮色卡片展示
        st.markdown(f"""
        <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; padding: 16px; border-radius: 10px; margin-top: 10px;">
            <div style="font-size: 0.85rem; color: #166534; font-weight: 500;">预估期末资产 ({invest_years}年后)</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #15803D; margin: 4px 0;">${total_balance:,.0f}</div>
            <div style="font-size: 0.85rem; color: #166534;">
                累计本金: <b>${total_principal:,.0f}</b><br>
                预计纯收益: <b>${profit:,.0f}</b> (+{(profit/total_principal)*100:.1f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)


# ------------------------------------------
# Tab 2: 行业分布与重仓股
# ------------------------------------------
# 调用获取实时持仓/行业数据
sector_data, top_holdings = load_voo_holdings_and_sectors()

with tab2:
    col_sector, col_holdings = st.columns([1, 1.1])

    with col_sector:
        st.markdown('<div class="section-title">🧱 行业板块分布 (Sector Weight)</div>', unsafe_allow_html=True)
        fig_pie = px.pie(
            sector_data, 
            values='Weight', 
            names='Sector', 
            hole=0.5,
            template=PLOTLY_TEMPLATE,
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


# ------------------------------------------
# Tab 3: 历史回报与分红
# ------------------------------------------
with tab3:
    col_annual, col_div = st.columns([1, 1])
    
    with col_annual:
        st.markdown('<div class="section-title">📅 近 10 年年度收益率 (%)</div>', unsafe_allow_html=True)
        annual_hist = hist['Close'].resample('YE').last()
        annual_returns = annual_hist.pct_change().dropna() * 100
        annual_df = pd.DataFrame({
            "Year": annual_returns.index.year,
            "Return": annual_returns.values
        }).tail(10)
        
        # 正收益深青绿，负收益软珊瑚红
        annual_df['Color'] = annual_df['Return'].apply(lambda x: '#0F766E' if x >= 0 else '#F43F5E')
        
        fig_bar = px.bar(
            annual_df, 
            x='Year', 
            y='Return', 
            text_auto='.1f',
            template='plotly_white'
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
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9')
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
                template='plotly_white'
            )
            fig_div.update_traces(
                line_color=THEME_MAIN, 
                marker_color=THEME_MAIN_LIGHT, 
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
                yaxis=dict(showgrid=True, gridcolor='#F1F5F9')
            )
            st.plotly_chart(fig_div, use_container_width=True)
        else:
            st.info("暂无分红数据")

# ==========================================
# 8. 全局页脚
# ==========================================
st.divider()
st.caption("💡 声明：本看板仅供个人数据展示与学术研究，不构成任何投资建议。数据源自 Yahoo Finance。")