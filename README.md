# 📊 US Stock & ETF Analysis & Portfolio Management Dashboard

🔗 **Live Demo**: [https://us-etf-dashboard-mbgpiwkqkt38tbatgqzdal.streamlit.app/](https://us-etf-dashboard-mbgpiwkqkt38tbatgqzdal.streamlit.app/)

---

### 🌟 Introduction
This is a professional-grade **US Stock & ETF Analysis and Portfolio Management Dashboard** built with **Python** and **Streamlit**. Designed specifically for long-term index investors, dollar-cost averaging (DCA) practitioners, and quantitative asset allocators, it offers a comprehensive suite of analytical tools. Features include multi-factor quantitative trading signals, asset-style differentiated health checks, one-click rebalancing calculators, and passive income/dividend forecasts. The system has been upgraded to a modern multi-page research terminal.

---

### ✨ Core Features
- 📊 **Single Asset & Strategy (`Stock & ETF Strategy`)**
  - **Multi-factor quantitative scoring model** (-100 to +100 points) based on MA200 bias, RSI(14), 52-week price range, and Bollinger Bands %B.
  - Dynamically calculates suggested buy/sell target price ranges, top 10 holdings, and sector breakdown transparency.
- ⚔️ **Multi-Asset Performance & Risk Comparison (`Comparison`)**
  - Compare cumulative returns across multiple stocks/ETFs over custom time horizons.
  - Detailed risk-adjusted performance ledger: automatically calculates **CAGR, Sharpe Ratio, Max Drawdown**, and more.
- 💼 **Portfolio Management & Rebalancing (`Portfolio & Rebalance`)**
  - Interactive editing for holdings, cost bases, and target weights, featuring **lossless JSON/CSV backup & restore**.
  - **DCA Rebalancing Calculator**: Supports joint calculation for existing holdings adjustments and new capital injections, generating precise execution orders.
  - **Passive Income Forecast**: Calculates portfolio weighted dividend yield and projects a **12-month dividend calendar**.
- 🛡️ **Style-Differentiated Portfolio Health Check (`Health Advisory`)**
  - Automatically identifies asset classes and applies tailored risk management thresholds: **Broad Market ETFs**, **Sector/Theme ETFs**, and **Individual Stocks**, providing early warnings for over-concentration.
- 🌙 **Dark/Light Mode & High-Contrast UI**
  - Employs a flat, solid-color design without gradients, significantly enhancing text readability and contrast in both dark and light modes.

---

### 📂 Directory Structure
```text
.
├── app.py                      # 🏠 Root router & global sidebar (includes donation links)
├── pages/                      # 📁 Streamlit multi-page directory
│   ├── 1_stock_strategy.py   # Single asset trend, quantitative signals & financial metrics
│   ├── 2_comparison.py       # Multi-asset performance comparison & risk analytics
│   └── 3_portfolio.py        # Holdings management, health advisory, rebalancing & dividend projections
├── strategy.py                 # Core quantitative algorithms & risk management logic
├── ui.py                       # UI rendering components (CSS styles, KPI cards, banners)
├── data.py                     # Data fetcher, caching & robust 3-tier dividend yield engine (yfinance)
├── requirements.txt            # Python dependency list
└── README.md                   # Project documentation
```

---

### 🍋‍🟩 Support My Work

If you find my projects or tools helpful, feel free to buy me a coffee! Your support helps keep my open-source tools running and motivates me to build more.

[![Buy me a lime](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20lime&emoji=🍋‍🟩&slug=qingning618&button_colour=40DCA5&font_colour=ffffff&font_family=Cookie&outline_colour=000000&coffee_colour=FFDD00)](https://www.buymeacoffee.com/qingning618)