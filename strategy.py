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