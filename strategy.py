import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def calculate_rsi(prices, period=14):
    """计算 RSI 指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty and not np.isnan(rsi.iloc[-1]) else 50.0


def analyze_trading_signal(hist, latest_price, week_52_high, week_52_low, div_yield, ticker_symbol=""):
    """
    机构级多因子量化交易信号模型 (Multi-Factor Score)
    综合考量：MA200乖离率、MA20/50均线趋势、RSI超买超卖、52周位置及布林带%B
    """
    if hist.empty or len(hist) < 20:
        return {
            "type": "HOLD",
            "title": "🔵 数据不足 / 保持观察",
            "desc": "暂无足够历史数据计算量化信号。",
            "ma200": latest_price, "position_52w": 50.0, "ma_bias": 0.0, "rsi": 50.0,
            "badge_color": "#1E40AF", "badge_bg": "#DBEAFE", "score": 0
        }

    close_series = hist['Close']

    # 1. 计算核心量化指标
    ma20 = close_series.tail(20).mean()
    ma50 = close_series.tail(50).mean() if len(close_series) >= 50 else ma20
    ma200 = close_series.tail(200).mean() if len(close_series) >= 200 else close_series.mean()
    
    # 乖离率 (%)
    ma200_bias = ((latest_price - ma200) / ma200) * 100
    ma50_bias = ((latest_price - ma50) / ma50) * 100
    
    # 52周相对分位数
    range_52 = week_52_high - week_52_low
    position_52w = ((latest_price - week_52_low) / range_52 * 100) if range_52 > 0 else 50.0

    # RSI(14)
    rsi = calculate_rsi(close_series, 14)

    # 布林带 (20, 2) 与 %B 指标
    std20 = close_series.tail(20).std()
    upper_band = ma20 + (2 * std20)
    lower_band = ma20 - (2 * std20)
    pct_b = ((latest_price - lower_band) / (upper_band - lower_band)) if (upper_band - lower_band) > 0 else 0.5

    # 2. 多因子打分逻辑 (Score range: -100 ~ +100)
    # 正分偏买入 (低估/支撑)，负分偏卖出/止盈 (过热/压力)
    score = 0

    # 因子 A: MA200 乖离率 (-30 ~ +30 分)
    if ma200_bias < -10:
        score += 30  # 深度回调，强超买机会
    elif ma200_bias < -3:
        score += 15  # 均线下方，具备性价比
    elif ma200_bias > 20:
        score -= 30  # 严重偏离均线，极度过热
    elif ma200_bias > 12:
        score -= 15  # 乖离率偏高

    # 因子 B: RSI 超买超卖 (-25 ~ +25 分)
    if rsi < 30:
        score += 25  # RSI 严重超卖
    elif rsi < 42:
        score += 12  # RSI 弱势区
    elif rsi > 75:
        score -= 25  # RSI 严重超买
    elif rsi > 65:
        score -= 12  # RSI 进入强势高位

    # 因子 C: 布林带 %B 位置 (-20 ~ +20 分)
    if pct_b < 0.05:
        score += 20  # 触及/跌破布林下轨
    elif pct_b > 0.95:
        score -= 20  # 突破布林上轨

    # 因子 D: 均线排列趋势确认 (-15 ~ +15 分)
    if ma20 > ma50 and ma50 > ma200:
        # 多头排列：强趋势中提高对超买的容忍度 (+10 动量加分)
        score += 10
    elif ma20 < ma50 and ma50 < ma200:
        # 空头排列：顺势看空 (-10 分)
        score -= 10

    # 3. 结果决策映射
    if score >= 35:
        signal_type = "BUY_STRONG"
        signal_title = f"🟢 强买入 / 黄金加仓期 (综合评分: +{score})"
        signal_desc = f"价格跌破或贴近关键支撑区（MA200 乖离率 {ma200_bias:+.1f}%，RSI 为 {rsi:.1f}），布林带逼近下轨。历史概率显示当前具备极高风险收益比，建议分批加仓或分批建仓。"
        badge_color = "#166534"
        badge_bg = "#DCFCE7"

    elif score >= 10:
        signal_type = "BUY_WEAK"
        signal_title = f"🟢 分批定投 / 逢低适度关注 (综合评分: +{score})"
        signal_desc = f"指标整体处于合理或偏低估区间（RSI {rsi:.1f}），估值并未过热。适合常态化定投或分批小额买入。"
        badge_color = "#15803D"
        badge_bg = "#F0FDF4"

    elif score <= -35:
        signal_type = "SELL_STRONG"
        signal_title = f"🔴 强减仓 / 分批止盈提示 (综合评分: {score})"
        signal_desc = f"价格显著偏离 200 日均线（乖离率 {ma200_bias:+.1f}%），且 RSI ({rsi:.1f}) 处于极端超买区，触及布林上轨。短期回调风险剧增，建议分批锁定利润或通过资产再平衡降低仓位。"
        badge_color = "#991B1B"
        badge_bg = "#FEE2E2"

    elif score <= -10:
        signal_type = "SELL_WEAK"
        signal_title = f"🟡 阶段高位 / 暂停追高 (综合评分: {score})"
        signal_desc = f"价格接近 52 周高点（分位数 {position_52w:.1f}%），乖离率放宽。不建议此时大额追高，偏好稳健的投资者可暂停加仓或小幅再平衡。"
        badge_color = "#9A3412"
        badge_bg = "#FFEDD5"

    else:
        signal_type = "HOLD"
        signal_title = f"🔵 趋势健康 / 正常持有 (综合评分: {score:+} )"
        signal_desc = f"价格在 200 日均线 (${ma200:.2f}) 上方平稳运行（乖离率 {ma200_bias:+.1f}%），各项指标处于均衡区间。建议保持既定投资策略，正常持有。"
        badge_color = "#1E40AF"
        badge_bg = "#DBEAFE"

    return {
        "type": signal_type,
        "title": signal_title,
        "desc": signal_desc,
        "score": score,
        "ma200": ma200,
        "position_52w": position_52w,
        "ma_bias": ma200_bias,
        "rsi": rsi,
        "pct_b": pct_b * 100,
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


# 常见宽基 ETF 与 行业/高股息 ETF 识别分类库
BROAD_MARKET_ETFS = {"VOO", "VT", "SPY", "IVV", "QQQ", "VTI", "SCHB", "SPLG"}
SECTOR_THEME_ETFS = {"VGT", "SCHD", "XLE", "XLF", "XLK", "XLV", "ARKK", "SMH", "SOXX", "JEPI", "JEPQ", "IWM"}

def analyze_portfolio_health(portfolio_df, market_data, sector_p_df):
    """
    方案 B: 风格区分版诊断算法
    根据 宽基 ETF / 行业及主题 ETF / 单股票 采用不同的集中度阈值
    """
    suggestions = []
    total_val = 0.0
    pos_weights = {}

    for _, row in portfolio_df.iterrows():
        t = row['ticker'].strip().upper()
        shares = row['shares']
        price = market_data.get(t, {}).get('latest_price', row['cost_price'])
        v = shares * price
        total_val += v
        pos_weights[t] = v

    if total_val == 0:
        return suggestions

    pos_pcts = {t: (v / total_val * 100) for t, v in pos_weights.items()}

    # 1. 区分资产风格判定集中度
    for t, pct in pos_pcts.items():
        m_info = market_data.get(t, {})
        quote_type = m_info.get('quote_type', 'EQUITY').upper()
        
        # 判断资产分类
        is_broad_etf = t in BROAD_MARKET_ETFS
        is_sector_etf = t in SECTOR_THEME_ETFS or (quote_type in ['ETF', 'MUTUALFUND'] and not is_broad_etf)
        is_single_stock = not is_broad_etf and not is_sector_etf

        if is_broad_etf:
            # 🌐 宽基 ETF 阈值：> 65% 高危, > 50% 预警
            if pct > 65.0:
                suggestions.append({
                    "level": "DANGER",
                    "title": f"🔴 宽基 ETF 占比极高: {t} 达 {pct:.1f}%",
                    "desc": f"{t} 为全市场宽基 ETF，虽然分散度极佳，但超过 65% 使得组合缺乏其他风格资产（如高股息/增长型）的补充调节。"
                })
            elif pct > 50.0:
                suggestions.append({
                    "level": "INFO",
                    "title": f"🔵 核心压舱石持仓: {t} 占比 {pct:.1f}%",
                    "desc": f"{t} 作为核心压舱石配置正常（>50%）。建议后续新入金可适度分配至卫星资产（如行业 ETF 或优质个股）。"
                })

        elif is_sector_etf:
            # 🧱 行业/主题/高股息 ETF 阈值：> 45% 高危, > 35% 预警
            if pct > 45.0:
                suggestions.append({
                    "level": "DANGER",
                    "title": f"🔴 行业/主题 ETF 严重集中: {t} 占比 {pct:.1f}%",
                    "desc": f"{t} 为行业/风格主题 ETF，占比超过 45% 容易让组合遭受单一行业（如科技挤估值或高股息跑输大盘）的周期性冲击。"
                })
            elif pct > 35.0:
                suggestions.append({
                    "level": "WARNING",
                    "title": f"🟡 行业/主题 ETF 占比偏高: {t} 占比 {pct:.1f}%",
                    "desc": f"{t} 占比已超过 35%。建议暂停增持该主题，将新资金分配给宽基指数或低相关性资产。"
                })

        elif is_single_stock:
            # 🏢 个股/单股票 阈值：> 30% 高危, > 15% 预警
            if pct > 30.0:
                suggestions.append({
                    "level": "DANGER",
                    "title": f"🔴 单股票黑天鹅风险高危: {t} 占比高达 {pct:.1f}%",
                    "desc": f"个股 {t} 占比已突破 30%！个股面临公司财报、管理层与行业竞争等特有风险，强烈建议锁定部分利润或止盈减仓。"
                })
            elif pct > 15.0:
                suggestions.append({
                    "level": "WARNING",
                    "title": f"🟡 单个股集中度预警: {t} 占比 {pct:.1f}%",
                    "desc": f"单个股票 {t} 权重超过 15%。建议将个股持仓控制在合理范围内，避免个股波动剧烈拉低整体组合表现。"
                })

    # 2. 穿透行业集中度诊断 (行业权重 > 45% 预警)
    if not sector_p_df.empty:
        top_sector = sector_p_df.iloc[0]
        sec_name = top_sector['Sector']
        sec_weight = top_sector['Weight']
        
        if sec_weight > 50.0:
            suggestions.append({
                "level": "DANGER",
                "title": f"🔴 穿透行业严重暴露: {sec_name} 占比达 {sec_weight:.1f}%",
                "desc": f"组合穿透后在 **{sec_name}** 行业的总体配置已过半（包含直接持股与 ETF 间接持股），行业集中风险较大。"
            })
        elif sec_weight > 38.0:
            suggestions.append({
                "level": "WARNING",
                "title": f"🟡 穿透行业偏好集中: {sec_name} 占比 {sec_weight:.1f}%",
                "desc": f"组合在 **{sec_name}** 行业配置较为集中（>38%），注意科技或相关行业的估值波动风险。"
            })

    if not suggestions:
        suggestions.append({
            "level": "SUCCESS",
            "title": "🟢 资产风格分类配置健康",
            "desc": "当前宽基 ETF、行业 ETF 与个股的配置比例符合风险控制标准，未发现异常集中度风险。"
        })

    return suggestions


def calculate_portfolio_rebalance(portfolio_df, market_data, new_cash=0.0):
    """
    根据用户设定的目标权重 (target_pct) 与新增入金 (new_cash)，
    精确计算存量再平衡与新增资金分配的买卖指令
    """
    total_current_val = 0.0
    rows_data = []

    # 1. 汇总各标的当前市值与目标权重
    for _, row in portfolio_df.iterrows():
        t = row['ticker'].strip().upper()
        shares = row['shares']
        cost_price = row['cost_price']
        target_pct = row.get('target_pct', 0.0)
        
        latest_price = market_data.get(t, {}).get('latest_price', cost_price)
        current_val = shares * latest_price
        total_current_val += current_val
        
        rows_data.append({
            "ticker": t,
            "shares": shares,
            "price": latest_price,
            "current_val": current_val,
            "target_pct": target_pct
        })

    if total_current_val == 0 and new_cash == 0:
        return pd.DataFrame(), 0.0, 0.0

    target_total_val = total_current_val + new_cash
    orders = []

    # 2. 计算各标的的目标市值与买卖指令
    for item in rows_data:
        t = item['ticker']
        price = item['price']
        curr_val = item['current_val']
        curr_pct = (curr_val / total_current_val * 100) if total_current_val > 0 else 0.0
        target_pct = item['target_pct']
        
        # 目标期望市值
        target_val = target_total_val * (target_pct / 100.0)
        diff_val = target_val - curr_val
        diff_shares = (diff_val / price) if price > 0 else 0.0
        
        # 判定交易动作
        if diff_val > 10:  # 买入阈值 $10
            action = "🟢 买入 (BUY)"
        elif diff_val < -10:  # 卖出阈值 -$10
            action = "🔴 卖出 (SELL)"
        else:
            action = "⚪ 保持 (HOLD)"
            
        orders.append({
            "代码": t,
            "当前股价 ($)": price,
            "当前市值 ($)": curr_val,
            "当前实际权重 (%)": curr_pct,
            "目标权重 (%)": target_pct,
            "权重偏差 (%)": curr_pct - target_pct,
            "再平衡建议动作": action,
            "调整金额 ($)": abs(diff_val),
            "调整股数": abs(diff_shares)
        })

    return pd.DataFrame(orders), total_current_val, target_total_val


def calculate_portfolio_dividends(portfolio_df, market_data, raw_dividends_dict):
    """
    穿透计算投资组合的加权股息率、预计年化现金流，
    并根据各标的历史派息月份预估未来 12 个月的月度被动收入分布。
    """
    total_portfolio_value = 0.0
    total_annual_cashflow = 0.0
    monthly_cashflow = {m: 0.0 for m in range(1, 13)}
    breakdown_rows = []

    # 1. 遍历持仓标的计算股息与派息月份
    for _, row in portfolio_df.iterrows():
        t = row['ticker'].strip().upper()
        shares = row['shares']
        cost_price = row['cost_price']
        
        m_info = market_data.get(t, {})
        latest_price = m_info.get('latest_price', cost_price)
        pos_val = shares * latest_price
        total_portfolio_value += pos_val
        
        div_yield = m_info.get('div_yield', 0.0) # TTM 股息率 (%)
        divs = raw_dividends_dict.get(t, pd.Series(dtype=float))
        
        # 计算该标的预估年化派息总额
        annual_div_per_share = (div_yield / 100.0) * latest_price
        pos_annual_cashflow = shares * annual_div_per_share
        total_annual_cashflow += pos_annual_cashflow
        
        # 识别该标的近一年的派息月份 (美股通常按季派息，如 3, 6, 9, 12 月)
        pay_months = []
        if not divs.empty:
            one_year_ago = datetime.now() - timedelta(days=365)
            recent_divs = divs[divs.index >= one_year_ago]
            if not recent_divs.empty:
                pay_months = sorted(list(set(recent_divs.index.month)))
        
        # 若无历史数据，默认美股标准季度派息 (3, 6, 9, 12 月)
        if not pay_months:
            pay_months = [3, 6, 9, 12]
            
        # 将派息按月份平均归集
        div_per_payout = pos_annual_cashflow / len(pay_months) if pay_months else 0.0
        for m in pay_months:
            monthly_cashflow[m] += div_per_payout
            
        breakdown_rows.append({
            "代码": t,
            "当前持仓市值 ($)": pos_val,
            "股息率 (TTM %)": div_yield,
            "每股年派息 ($)": annual_div_per_share,
            "预计年领股息 ($)": pos_annual_cashflow,
            "历史派息月份": ", ".join([f"{m}月" for m in pay_months])
        })

    # 计算组合综合加权股息率
    portfolio_div_yield = (total_annual_cashflow / total_portfolio_value * 100.0) if total_portfolio_value > 0 else 0.0

    # 构建月度现金流 DataFrame
    monthly_df = pd.DataFrame([
        {"月份": f"{m}月", "Month_Num": m, "预计领息 ($)": monthly_cashflow[m]}
        for m in range(1, 13)
    ])

    return {
        "portfolio_div_yield": portfolio_div_yield,
        "total_annual_cashflow": total_annual_cashflow,
        "monthly_df": monthly_df,
        "breakdown_df": pd.DataFrame(breakdown_rows)
    }