# 📊 美股与 ETF 投资分析与组合管理看板
# US Stock & ETF Analysis & Portfolio Management Dashboard

🔗 **在线体验地址**：[https://us-etf-dashboard-mbgpiwkqkt38tbatgqzdal.streamlit.app/](https://us-etf-dashboard-mbgpiwkqkt38tbatgqzdal.streamlit.app/)

---

### 🌟 项目简介
这是一个基于 **Python** 与 **Streamlit** 构建的专业级美股/ETF 投资分析与组合管理看板。专为长期指数投资者、定投族及量化资产配置者设计，提供包含多因子量化交易信号、风格区分健康诊断、一键再平衡计算器及被动现金流预估在内的全套资产分析工具。系统现已升级为多页面现代化投研终端。

---

### ✨ 核心功能亮点
- 📊 **个股与 ETF 策略决策 (`Stock & ETF Strategy`)**
  - 基于 MA200 乖离率、RSI(14)、52 周价格区间及布林带 %B 的**多因子打分模型**（-100 至 +100 分）。
  - 动态计算建议买入价与建议卖出价区间，提供 Top 10 重仓股及行业穿透分布。
- ⚔️ **多标的走势与风险对比 (`Comparison`)**
  - 横向对比多只股票/ETF 在不同时间跨度下的累计收益率曲线。
  - 核心风险收益指标对账单：自动计算**年化收益率 (CAGR)、夏普比率 (Sharpe Ratio)、最大回撤 (Max Drawdown)** 等。
- 💼 **投资组合实盘管理与再平衡 (`Portfolio & Rebalance`)**
  - 支持交互式在线编辑持股数、成本价与目标配置权重，支持 **JSON / CSV 无损备份与恢复**。
  - **DCA 再平衡计算器**：支持存量调仓与新资金入金（New Cash）联合计算，输出精确的买卖交易指令。
  - **被动现金流预估**：穿透计算组合加权平均股息率，生成**未来 12 个月领息日历柱状图**。
- 🛡️ **风格区分的组合健康诊断 (`Health Advisory`)**
  - 自动识别资产类型并应用差异化风控阈值：**宽基 ETF**、**行业/主题 ETF** 与**单股票/个股**，及时预警过集中风险。
- 🌙 **亮色/暗色模式与高对比度 UI (Dark Mode Friendly)**
  - 采用无渐变纯色扁平化设计，大幅提升文字与卡片在双模式下的对比度与视觉质感。

---

### 📂 项目目录结构
```text
.
├── app.py                      # 🏠 根路由调度与全局侧边栏（含赞助链接）
├── pages/                      # 📁 Streamlit 多页面模块
│   ├── 0_index.py             # 纯色现代化欢迎页与核心功能直达卡片
│   ├── 1_stock_strategy.py   # 单标的走势、量化信号与财务分析
│   ├── 2_comparison.py       # 多标的走势比拼与风险指标对账
│   └── 3_portfolio.py        # 持仓管理、健康诊断、再平衡与股息预估
├── strategy.py                 # 核心量化算法与组合风控逻辑
├── ui.py                       # UI 视觉渲染组件（CSS 样式、KPI 卡片、Banner）
├── data.py                     # 数据抓取、缓存与三层股息率强力计算 (yfinance)
├── requirements.txt            # 依赖库清单
└── README.md                   # 项目说明文档
```

### ☕ Support My Work

If you find my projects or tools helpful, feel free to buy me a coffee! Your support helps keep my open-source tools running and motivates me to build more.

[![Buy me a lime](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20lime&emoji=🍋‍🟩&slug=qingning618&button_colour=40DCA5&font_colour=ffffff&font_family=Cookie&outline_colour=000000&coffee_colour=FFDD00)](https://www.buymeacoffee.com/qingning618)