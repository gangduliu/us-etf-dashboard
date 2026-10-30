import os

# HTTP/SOCKS ports for local proxy software
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10808'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10808'


import streamlit as st
from ui import inject_custom_css

# 1. Page basic configuration
st.set_page_config(
    page_title="US Stock & ETF Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject global styles
inject_custom_css()

# 3. Use st.navigation to manage the sidebar menu (Note: Do not include the currently running app.py here!)
pg = st.navigation({
    "System Navigation": [
        st.Page("pages/1_stock_strategy.py", title="Stock & ETF Strategy", icon="📊"),
        st.Page("pages/2_comparison.py", title="Trend & Risk Comparison", icon="⚔️"),
        st.Page("pages/3_portfolio.py", title="Portfolio Management", icon="💼")
    ]
})

# 4. Run the selected page
pg.run()

# 5. 🌟 Inject the "Buy Me a Coffee" sponsorship button at the bottom of the sidebar
with st.sidebar:
    st.markdown("### 🌐 Source Code")
    st.markdown(
        """
        <div style="margin-bottom: 12px;">
            <a href="https://github.com/gangduliu/us-etf-dashboard" target="_blank" style="text-decoration: none;">
                <div style="background-color: var(--secondary-background-color); border: 1px solid var(--border-color); border-radius: 8px; padding: 10px 14px; text-align: center; color: var(--text-color); font-weight: 600; font-size: 0.9rem; transition: all 0.2s;">
                    ⭐ GitHub Repository
                </div>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### ☕ Support the Author")
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 10px;">
            <p style="font-size: 0.85rem; opacity: 0.8; margin-bottom: 10px;">If this dashboard has been helpful to you, feel free to buy me a coffee! ☕</p>
            <a href="https://buymeacoffee.com/qingning618" target="_blank">
                <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=qingning618&button_colour=0F766E&font_colour=ffffff&font_family=Inter&outline_colour=ffffff&coffee_colour=FFDD00" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" alt="Buy Me A Coffee">
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )