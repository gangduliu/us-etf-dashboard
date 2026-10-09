# 📊 美股与 ETF 投资分析与组合管理看板
# US Stock & ETF Analysis & Portfolio Management Dashboard

### 🌟 项目简介
这是一个基于 **Python** 与 **Streamlit** 构建的专业级美股/ETF 投资分析与组合管理看板。专为长期指数投资者、定投族及量化资产配置者设计，提供包含多因子量化交易信号、风格区分健康诊断、一键再平衡计算器及被动现金流预估在内的全套资产分析工具。

### ✨ 核心功能亮点
- 📊 **行情与量化交易信号 (`analyze_trading_signal`)**
  - 基于 MA200 乖离率、RSI(14)、52 周价格区间及布林带 %B 的**多因子打分模型**（-100 至 +100 分）。
  - 结合均线多/空头排列趋势，动态给出分批建仓、持仓或止盈减仓建议。
- 💼 **持仓管理与一键再平衡 (`Rebalance Assistant`)**
  - 支持交互式在线编辑持股数、成本价与目标配置权重（`Target Weight %`）。
  - 支持**“存量调仓”**与**“新资金入金 (New Cash DCA)”**两种模式，自动计算买卖股数与金额。
- 💵 **被动现金流与股息预估 (`Dividend Projection`)**
  - 穿透计算组合加权平均股息率与预估年化现金流。
  - 基于历史派息数据生成**未来 12 个月领息日历柱状图**。
- 🛡️ **风格区分的组合健康诊断 (`Style-Based Health Advisory`)**
  - 自动识别资产类型并应用差异化风控阈值：**宽基 ETF** (如 VOO/VT)、**行业/主题 ETF** (如 VGT/SCHD) 与**单股票/个股**。
  - 穿透计算综合行业暴露，及时预警过集中风险。
- 🔄 **数据导入导出与持久化 (Data Transfer & Backup)**
  - 支持 **JSON（无损备份）** 与 **CSV（Excel 批量编辑）** 一键导入导出。
  - 结合动态 Key 与回调函数设计，防止文件重复上传引发死循环。
- 🌙 **暗色模式与响应式 UI (Dark Mode Friendly)**
  - 使用 CSS 变量自适应亮色/暗色主题，保持极佳高对比度与视觉质感。

---

### 📂 项目目录结构
```text
.
├── app.py              # 主程序入口 (Streamlit 页面布局与 Tab 导航)
├── strategy.py         # 核心量化算法 (交易信号、再平衡、股息穿透、健康诊断)
├── ui.py               # UI 视觉渲染组件 (KPI 卡片、Plotly 图表、诊断 Banner)
├── data.py             # 数据抓取与三层股息率强力计算 (yfinance 封装与缓存)
├── requirements.txt    # 依赖库清单
└── README.md           # 项目说明文档
```