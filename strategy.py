import pandas as pd

def analyze_trading_signal(hist, latest_price, week_52_high, week_52_low, div_yield):
    """
    根据 MA200 均线、52 周相对高低位、RSI 指标及偏离度计算综合买卖/再平衡建议
    """
    # 1. 计算 200 日均线 (MA200)
    ma200 = hist['Close'].tail(200).mean() if len(hist) >= 200 else hist['Close'].mean()
    
    # 2. 计算 52 周分位数 (0% ~ 100%)
    range_52 = week_52_high - week_52_low
    position_52w = ((latest_price - week_52_low) / range_52 * 100) if range_52 > 0 else 50
    
    # 3. 计算 MA200 乖离率 (%)
    ma_bias = ((latest_price - ma200) / ma200) * 100
    
    # 4. 计算简易 RSI (14日)
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).tail(14).mean()
    loss = (-delta.where(delta < 0, 0)).tail(14).mean()
    rsi = 100 - (100 / (1 + gain / loss)) if loss != 0 else 50

    # 5. 综合决策逻辑（包含卖出/止盈/买入/持有信号）
    if ma_bias > 18 or (position_52w > 95 and rsi > 75):
        # 🚨 强卖出 / 减仓 / 止盈信号
        signal_type = "SELL_STRONG"
        signal_title = "🔴 短期严重过热 / 建议分批止盈或再平衡 (Sell/Reduce)"
        signal_desc = f"当前价格偏离 200 日均线高达 {ma_bias:+.1f}%，且 RSI({rsi:.1f}) 进入超买区。短期回调风险极高，建议对盈利较丰厚的部分仓位**分批止盈**，或通过资产再平衡（Rebalance）将资金转移至低估标的。"
        badge_color = "#991B1B" # 警示红
        badge_bg = "#FEE2E2"

    elif ma_bias > 12 or position_52w > 88:
        # ⚠️ 减仓提示 / 暂停加仓
        signal_type = "SELL_WEAK"
        signal_title = "🟡 处于相对高位 / 建议暂停追高或适度减仓 (Hold/Trim)"
        signal_desc = f"价格接近 52 周高点（分位数 {position_52w:.1f}%），上方获利盘回吐压力增大。不建议此时大额追高，偏好稳健的投资者可考虑**小幅减仓锁定部分收益**。"
        badge_color = "#9A3412" # 橙黄
        badge_bg = "#FFEDD5"

    elif latest_price < ma200:
        # 🟢 买入信号
        signal_type = "BUY"
        signal_title = "🟢 具备较高性价比 / 黄金加仓期 (Buy)"
        signal_desc = f"当前价格已低于 200 日均线 (${ma200:.2f})，处于中长期价值区间。对于长期投资者而言，具备较好的**分批建仓/大额加仓**性价比。"
        badge_color = "#166534" # 绿
        badge_bg = "#DCFCE7"

    else:
        # 🔵 常规持有 / 定投
        signal_type = "HOLD"
        signal_title = "🔵 趋势健康 / 适合常态化持有与定投 (Hold/DCA)"
        signal_desc = f"价格保持在 200 日均线 (${ma200:.2f}) 之上运行（乖离率 {ma_bias:+.1f}%），整体上升趋势健全。适合按既定计划**继续持有或正常定投**。"
        badge_color = "#1E40AF" # 蓝
        badge_bg = "#DBEAFE"
        
    return {
        "type": signal_type,
        "title": signal_title,
        "desc": signal_desc,
        "ma200": ma200,
        "position_52w": position_52w,
        "ma_bias": ma_bias,
        "rsi": rsi,
        "badge_color": badge_color,
        "badge_bg": badge_bg
    }


def calculate_portfolio_metrics(portfolio_df, market_data):
    """计算投资组合的总资产、总成本、累计浮盈浮亏及当日盈亏"""
    total_cost = 0.0
    total_market_value = 0.0
    daily_gain_loss = 0.0
    
    detailed_rows = []
    
    for _, row in portfolio_df.iterrows():
        t = row['ticker']
        shares = row['shares']
        cost_price = row['cost_price']
        
        m_info = market_data.get(t, {})
        latest_price = m_info.get('latest_price', cost_price)
        prev_price = m_info.get('prev_price', latest_price)
        
        pos_cost = shares * cost_price
        pos_value = shares * latest_price
        pos_profit = pos_value - pos_cost
        pos_profit_pct = (pos_profit / pos_cost * 100) if pos_cost > 0 else 0
        
        pos_daily = shares * (latest_price - prev_price)
        
        total_cost += pos_cost
        total_market_value += pos_value
        daily_gain_loss += pos_daily
        
        detailed_rows.append({
            "代码": t,
            "名称": m_info.get('name', t),
            "持仓股数": shares,
            "持仓成本价 ($)": cost_price,
            "当前现价 ($)": latest_price,
            "当前总市值 ($)": pos_value,
            "持仓成本总额 ($)": pos_cost,
            "累计盈亏 ($)": pos_profit,
            "累计收益率 (%)": pos_profit_pct,
            "当日盈亏 ($)": pos_daily
        })

    total_profit = total_market_value - total_cost
    total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
    
    return {
        "total_cost": total_cost,
        "total_market_value": total_market_value,
        "total_profit": total_profit,
        "total_profit_pct": total_profit_pct,
        "daily_gain_loss": daily_gain_loss,
        "details_df": pd.DataFrame(detailed_rows)
    }


def analyze_portfolio_health(portfolio_df, market_data, sector_p_df):
    """
    对投资组合进行健康诊断，提供分散度警告、行业集中度风险与再平衡建议
    """
    suggestions = []
    
    # 1. 计算各持仓标的的当前市值与权重占比
    total_val = 0.0
    pos_weights = {}
    
    for _, row in portfolio_df.iterrows():
        t = row['ticker']
        shares = row['shares']
        price = market_data.get(t, {}).get('latest_price', row['cost_price'])
        v = shares * price
        total_val += v
        pos_weights[t] = v

    if total_val == 0:
        return suggestions

    # 计算百分比占比
    pos_pcts = {t: (v / total_val * 100) for t, v in pos_weights.items()}

    # 2. 诊断一：单一标的集中度风险
    for t, pct in pos_pcts.items():
        if pct > 40.0:
            suggestions.append({
                "level": "WARNING",
                "title": f"⚠️ 标的集中度风险: {t} 占比高达 {pct:.1f}%",
                "desc": f"单个标的 {t} 占总资产比例超过 40%，组合价格波动受该标的单边影响较大。建议新增资金优先分配至其他低估标的，或适度止盈以降低集中度。"
            })

    # 3. 诊断二：行业集中度暴露
    if not sector_p_df.empty:
        top_sector = sector_p_df.iloc[0]
        if top_sector['Weight'] > 50.0:
            suggestions.append({
                "level": "WARNING",
                "title": f"⚠️ 行业过度集中: {top_sector['Sector']} 行业占比达 {top_sector['Weight']:.1f}%",
                "desc": f"组合在 **{top_sector['Sector']}** 行业的穿透配置过半，若该行业面临系统性回调（如科技股大幅挤估值），组合回撤压力会显著增加。建议补充非相关性资产（如高股息 SCHD 或防守型资产）。"
            })

    # 4. 诊断三：组合分散度与再平衡状态
    if len(pos_pcts) == 1:
        suggestions.append({
            "level": "INFO",
            "title": "💡 组合单一度提示",
            "desc": "当前组合仅包含 1 只标的。若为 VOO 等宽基指数 ETF 可长期持有；若是单一个股，建议引入其他资产以降低个股特有风险。"
        })
    elif len(suggestions) == 0:
        suggestions.append({
            "level": "SUCCESS",
            "title": "🟢 组合健康度良好 / 配置均衡",
            "desc": "持仓标的与行业分布较为健康，未出现极端的单一集中度风险。建议继续保持按既定频率（如半年或一年）进行常态化再平衡。"
        })

    return suggestions