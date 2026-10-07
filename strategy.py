def analyze_buy_signal(hist, latest_price, week_52_high, week_52_low):
    """根据 MA200 均线与 52 周相对高低位计算量化买入建议"""
    ma200 = hist['Close'].tail(200).mean() if len(hist) >= 200 else hist['Close'].mean()
    
    range_52 = week_52_high - week_52_low
    position_52w = ((latest_price - week_52_low) / range_52 * 100) if range_52 > 0 else 50
    ma_bias = ((latest_price - ma200) / ma200) * 100
    
    if latest_price < ma200:
        signal_title = "🟢 具备较高性价比 / 黄金加仓期"
        signal_desc = f"当前价格已低于 200 日均线 (${ma200:.2f})，处于中长期价值区间。对于长期投资者而言，具备较好的分批建仓/大额加仓性价比。"
        badge_color = "#166534"
        badge_bg = "#DCFCE7"
    elif position_52w > 85 and ma_bias > 8:
        signal_title = "🟡 处于短期高位 / 建议逢低定投"
        signal_desc = f"价格靠近 52 周高点附近（偏离 200 日均线 {ma_bias:+.1f}%），短期可能有震荡回调风险。建议避免一次性重仓追高，优先采取分批定投策略。"
        badge_color = "#854D0E"
        badge_bg = "#FEF9C3"
    else:
        signal_title = "🔵 趋势健康 / 适合定期定额常态化配置"
        signal_desc = f"价格保持在 200 日均线 (${ma200:.2f}) 之上运行，整体上升趋势健全。适合按既定计划进行常规定投。"
        badge_color = "#1E40AF"
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