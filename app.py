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
        st.Page("pages/0_index.py", title="首页概览", icon="🏠"),
        st.Page("pages/1_stock_strategy.py", title="个股与 ETF 策略", icon="📊"),
        st.Page("pages/2_comparison.py", title="走势与风险对比", icon="⚔️"),
        st.Page("pages/3_portfolio.py", title="投资组合管理", icon="💼")
    ]
})

# 4. 运行选中的页面
pg.run()