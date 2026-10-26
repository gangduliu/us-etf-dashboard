import streamlit as st
from ui import inject_custom_css

st.set_page_config(page_title="首页概览", page_icon="🏠", layout="wide")
inject_custom_css()

# 首页 Hero 头部 Banner
st.markdown("""
<div style="background-color: #0F766E; padding: 40px 36px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.15); margin-bottom: 32px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);">
    <h1 style="color: #FFFFFF; font-size: 1.8rem; margin-bottom: 12px; letter-spacing: -0.02em;">📈 美股 & ETF 智能量化投研终端</h1>
    <p style="color: #FFFFFF; font-size: 1.05rem; line-height: 1.6; font-weight: 400; opacity: 0.95; margin: 0;">整合机构级多因子量化交易信号、多资产风格穿透诊断、一键动态再平衡计算器及未来 12 个月被动股息现金流预测，助力长期稳健资产配置。</p>
</div>
""", unsafe_allow_html=True)

# 核心三大功能模块交互卡片导航
st.markdown("### 🧭 核心功能模块直达")

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <div style="background-color: var(--secondary-background-color); border: 1px solid var(--border-color); border-radius: 16px; padding: 28px 24px; height: 100%;">
        <span style="display:inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; background-color: rgba(15, 118, 110, 0.12); color: #0F766E; margin-bottom: 12px;">单标的深度分析</span>
        <div style="font-size: 2.4rem; margin-bottom: 16px;">📊</div>
        <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 10px; color: var(--text-color);">个股与 ETF 策略决策</div>
        <div style="font-size: 0.9rem; color: var(--text-color); opacity: 0.8; line-height: 1.55; margin-bottom: 20px;">基于 MA200 乖离率、RSI(14)、52周相对位置等生成量化评分与买卖参考价。</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_stock_strategy.py", label="进入个股/ETF策略 →", use_container_width=True)

with col2:
    st.markdown("""
    <div style="background-color: var(--secondary-background-color); border: 1px solid var(--border-color); border-radius: 16px; padding: 28px 24px; height: 100%;">
        <span style="display:inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; background-color: rgba(15, 118, 110, 0.12); color: #0F766E; margin-bottom: 12px;">多标的收益比拼</span>
        <div style="font-size: 2.4rem; margin-bottom: 16px;">⚔️</div>
        <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 10px; color: var(--text-color);">多标的走势与风险对比</div>
        <div style="font-size: 0.9rem; color: var(--text-color); opacity: 0.8; line-height: 1.55; margin-bottom: 20px;">横向对比多只股票/ETF的累计收益率曲线，一键算清夏普比率与最大回撤。</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_comparison.py", label="进入走势对比看板 →", use_container_width=True)

with col3:
    st.markdown("""
    <div style="background-color: var(--secondary-background-color); border: 1px solid var(--border-color); border-radius: 16px; padding: 28px 24px; height: 100%;">
        <span style="display:inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; background-color: rgba(15, 118, 110, 0.12); color: #0F766E; margin-bottom: 12px;">组合风控与再平衡</span>
        <div style="font-size: 2.4rem; margin-bottom: 16px;">💼</div>
        <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 10px; color: var(--text-color);">投资组合实盘管理</div>
        <div style="font-size: 0.9rem; color: var(--text-color); opacity: 0.8; line-height: 1.55; margin-bottom: 20px;">支持持仓导入导出、风格健康诊断、DCA 再平衡调仓与 12 个月领息日历。</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_portfolio.py", label="进入投资组合管理 →", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.caption("💡 提示：使用左侧导航菜单可随时在各个功能页面间切换。数据源自 Yahoo Finance。")