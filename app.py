import os

# 本地代理软件的 HTTP/SOCKS 端口
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'


import streamlit as st
from ui import inject_custom_css

# 1. 页面基本配置
st.set_page_config(
    page_title="US Stock & ETF Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 注入全局样式
inject_custom_css()

# 3. 使用 st.navigation 统一管理侧边栏菜单（注意：千万不要把当前运行的 app.py 包含进去！）
pg = st.navigation({
    "系统导航": [
        st.Page("pages/1_stock_strategy.py", title="个股与 ETF 策略", icon="📊"),
        st.Page("pages/2_comparison.py", title="走势与风险对比", icon="⚔️"),
        st.Page("pages/3_portfolio.py", title="投资组合管理", icon="💼")
    ]
})

# 4. 运行选中的页面
pg.run()

# 5. 🌟 在侧边栏底部统一注入“Buy Me a Coffee”赞助按钮
with st.sidebar:
    st.markdown("### 🌐 项目源码")
    st.markdown(
        """
        <div style="margin-bottom: 12px;">
            <a href="https://github.com/gangduliu/us-etf-dashboard" target="_blank" style="text-decoration: none;">
                <div style="background-color: var(--secondary-background-color); border: 1px solid var(--border-color); border-radius: 8px; padding: 10px 14px; text-align: center; color: var(--text-color); font-weight: 600; font-size: 0.9rem; transition: all 0.2s;">
                    ⭐ GitHub 仓库源码
                </div>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### ☕ 支持作者")
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 10px;">
            <p style="font-size: 0.85rem; opacity: 0.8; margin-bottom: 10px;">如果这个看板对你有帮助，欢迎请我喝一杯咖啡！☕</p>
            <a href="https://buymeacoffee.com/qingning618" target="_blank">
                <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=qingning618&button_colour=0F766E&font_colour=ffffff&font_family=Inter&outline_colour=ffffff&coffee_colour=FFDD00" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" alt="Buy Me A Coffee">
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )