import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def calculate_ticker_performance_metrics(df):
    if df.empty or len(df) < 2:
        return 0.0, 0.0, 0.0
    
    start_price = df['Close'].iloc[0]
    end_price = df['Close'].iloc[-1]
    
    # 1. Total Cumulative Return
    total_return = (end_price - start_price) / start_price
    
    # 2. Compound Annual Growth Rate (CAGR)
    days = (df.index[-1] - df.index[0]).days
    years = days / 365.25
    cagr = ((end_price / start_price) ** (1 / years) - 1) if years > 0 else 0.0
    
    # 3. Maximum Drawdown
    roll_max = df['Close'].cummax()
    drawdown = (df['Close'] - roll_max) / roll_max
    max_drawdown = drawdown.min()  # Negative value
    
    return total_return, cagr, max_drawdown


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty and not np.isnan(rsi.iloc[-1]) else 50.0


def analyze_trading_signal(hist, latest_price, week_52_high, week_52_low, div_yield, ticker_symbol=""):
    """
    Institutional multi-factor quant trading signal model (Multi-Factor Score)
    Considers: MA200 bias, MA20/50 trend, RSI overbought/oversold, 52-week position, and Bollinger %B
    Includes: Suggested buy price and sell price calculations
    """
    if hist.empty or len(hist) < 20:
        return {
            "type": "HOLD",
            "title": "🔵 Insufficient Data / Keep Observing",
            "desc": "Insufficient historical data to calculate quantitative signals.",
            "ma200": latest_price, "position_52w": 50.0, "ma_bias": 0.0, "rsi": 50.0,
            "suggested_buy_price": round(latest_price * 0.95, 2),
            "suggested_sell_price": round(latest_price * 1.05, 2),
            "badge_color": "#1E40AF", "badge_bg": "#DBEAFE", "score": 0
        }

    close_series = hist['Close']

    # 1. Calculate core quant metrics
    ma20 = close_series.tail(20).mean()
    ma50 = close_series.tail(50).mean() if len(close_series) >= 50 else ma20
    ma200 = close_series.tail(200).mean() if len(close_series) >= 200 else close_series.mean()
    
    # Bias (%)
    ma200_bias = ((latest_price - ma200) / ma200) * 100
    ma50_bias = ((latest_price - ma50) / ma50) * 100
    
    # 52-week relative position
    range_52 = week_52_high - week_52_low
    position_52w = ((latest_price - week_52_low) / range_52 * 100) if range_52 > 0 else 50.0

    # RSI(14)
    rsi = calculate_rsi(close_series, 14)

    # Bollinger Bands (20, 2) & %B
    std20 = close_series.tail(20).std()
    upper_band = ma20 + (2 * std20)
    lower_band = ma20 - (2 * std20)
    pct_b = ((latest_price - lower_band) / (upper_band - lower_band)) if (upper_band - lower_band) > 0 else 0.5

    # Suggested buy price: lower of lower band, 96% of latest price, or MA20 support
    suggested_buy_price = round(max(lower_band, min(latest_price * 0.96, ma20)), 2)
    
    # Suggested sell price: upper band or target target premium
    suggested_sell_price = round(min(upper_band, max(latest_price * 1.06, ma20 * 1.05)), 2)

    # 2. Multi-factor scoring logic (Score range: -100 ~ +100)
    score = 0

    # Factor A: MA200 Bias (-30 ~ +30 pts)
    if ma200_bias < -10:
        score += 30  # Deep pullback, strong buy opportunity
    elif ma200_bias < -3:
        score += 15  # Below moving average, good value
    elif ma200_bias > 20:
        score -= 30  # Severely overextended, extreme overheat
    elif ma200_bias > 12:
        score -= 15  # High bias

    # Factor B: RSI Overbought/Oversold (-25 ~ +25 pts)
    if rsi < 30:
        score += 25  # RSI severely oversold
    elif rsi < 42:
        score += 12  # RSI weak zone
    elif rsi > 75:
        score -= 25  # RSI severely overbought
    elif rsi > 65:
        score -= 12  # RSI entering strong upper zone

    # Factor C: Bollinger %B (-20 ~ +20 pts)
    if pct_b < 0.05:
        score += 20  # Touching/below lower band
    elif pct_b > 0.95:
        score -= 20  # Breaking above upper band

    # Factor D: Moving Average Alignment (-15 ~ +15 pts)
    if ma20 > ma50 and ma50 > ma200:
        # Bullish alignment: Strong momentum
        score += 10
    elif ma20 < ma50 and ma50 < ma200:
        # Bearish alignment
        score -= 10

    # 3. Signal Decision Mapping
    if score >= 35:
        signal_type = "BUY_STRONG"
        signal_title = f"🟢 Strong Buy / Prime Accumulation Window (Score: +{score})"
        signal_desc = f"Price is near key support levels (MA200 bias {ma200_bias:+.1f}%, RSI at {rsi:.1f}), approaching lower Bollinger Band. Favorable risk-reward ratio; consider building or adding positions in tranches."
        badge_color = "#166534"
        badge_bg = "#DCFCE7"
    elif score >= 10:
        signal_type = "BUY_WEAK"
        signal_title = f"🟢 Dollar-Cost Average / Moderate Dip Buy (Score: +{score})"
        signal_desc = f"Indicators are in reasonable or undervalued range (RSI {rsi:.1f}) without overheating. Suitable for regular DCA or incremental buying."
        badge_color = "#15803D"
        badge_bg = "#F0FDF4"
    elif score <= -35:
        signal_type = "SELL_STRONG"
        signal_title = f"🔴 Strong Trim / Profit Taking Alert (Score: {score})"
        signal_desc = f"Price is significantly stretched above 200-day MA (bias {ma200_bias:+.1f}%) and RSI ({rsi:.1f}) is in extreme overbought territory near upper Bollinger Band. Elevated risk of short-term pullbacks; consider locking in profits or rebalancing."
        badge_color = "#991B1B"
        badge_bg = "#FEE2E2"
    elif score <= -10:
        signal_type = "SELL_WEAK"
        signal_title = f"🟡 Local High / Pause Chasing (Score: {score})"
        signal_desc = f"Price is near 52-week high (percentile {position_52w:.1f}%) with extended bias. Avoid buying aggressively at these levels; conservative investors may pause buying or perform light rebalancing."
        badge_color = "#9A3412"
        badge_bg = "#FFEDD5"
    else:
        signal_type = "HOLD"
        signal_title = f"🔵 Healthy Trend / Hold Position (Score: {score:+} )"
        signal_desc = f"Price is moving smoothly above 200-day MA (${ma200:.2f}) with bias of {ma200_bias:+.1f}%. Metrics remain balanced. Maintain existing portfolio strategy."
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
        "suggested_buy_price": suggested_buy_price,
        "suggested_sell_price": suggested_sell_price,
        "badge_color": badge_color,
        "badge_bg": badge_bg
    }


def calculate_performance_metrics(df_prices):
    metrics = []
    trading_days = 252
    
    for ticker in df_prices.columns:
        series = df_prices[ticker].dropna()
        if len(series) < 2:
            continue
            
        # 1. Total Cumulative Return
        total_return = (series.iloc[-1] / series.iloc[0]) - 1
        
        # 2. Compound Annual Growth Rate (CAGR)
        days = (series.index[-1] - series.index[0]).days
        years = days / 365.25
        cagr = (series.iloc[-1] / series.iloc[0]) ** (1 / years) - 1 if years > 0 else 0
        
        # 3. Annualized Volatility
        daily_returns = series.pct_change().dropna()
        annual_volatility = daily_returns.std() * np.sqrt(trading_days)
        
        # 4. Max Drawdown
        rolling_max = series.cummax()
        drawdown = (series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 5. Sharpe Ratio (assuming risk-free rate of 4.0% / 0.04)
        risk_free_rate = 0.04
        sharpe_ratio = (cagr - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
        
        metrics.append({
            "Ticker": ticker,
            "Cumulative Return": total_return * 100,
            "CAGR (Annual Return)": cagr * 100,
            "Annualized Volatility": annual_volatility * 100,
            "Max Drawdown": max_drawdown * 100,
            "Sharpe Ratio": sharpe_ratio
        })
        
    df_result = pd.DataFrame(metrics)
    if not df_result.empty:
        df_result.set_index("Ticker", inplace=True)
    return df_result


def calculate_portfolio_metrics(portfolio_df, market_data):
    """Calculate portfolio total market value, total cost basis, cumulative profit/loss, and daily gain/loss"""
    total_cost = 0.0
    total_market_value = 0.0
    total_prev_value = 0.0
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
        pos_prev = shares * prev_price
        pos_profit = pos_value - pos_cost
        pos_profit_pct = (pos_profit / pos_cost * 100) if pos_cost > 0 else 0
        
        pos_daily = shares * (latest_price - prev_price)
        pos_daily_pct = (pos_daily / pos_prev * 100) if pos_prev > 0 else 0
        
        total_cost += pos_cost
        total_market_value += pos_value
        total_prev_value += pos_prev
        daily_gain_loss += pos_daily
        
        detailed_rows.append({
            "Ticker": t,
            "Name": m_info.get('name', t),
            "Shares": shares,
            "Cost Basis ($)": cost_price,
            "Current Price ($)": latest_price,
            "Current Market Value ($)": pos_value,
            "Total Cost ($)": pos_cost,
            "Cumulative P&L ($)": pos_profit,
            "Cumulative Return (%)": pos_profit_pct,
            "Daily Gain/Loss ($)": pos_daily,
            "Daily Return (%)": pos_daily_pct
        })

    total_profit = total_market_value - total_cost
    total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
    daily_gain_loss_pct = (daily_gain_loss / total_prev_value * 100) if total_prev_value > 0 else 0

    return {
        "total_cost": total_cost,
        "total_market_value": total_market_value,
        "total_profit": total_profit,
        "total_profit_pct": total_profit_pct,
        "daily_gain_loss": daily_gain_loss,
        "daily_gain_loss_pct": daily_gain_loss_pct,
        "details_df": pd.DataFrame(detailed_rows)
    }


# Broad market ETFs and sector/dividend ETF classification sets
BROAD_MARKET_ETFS = {"VOO", "VT", "SPY", "IVV", "QQQ", "VTI", "SCHB", "SPYM"}
SECTOR_THEME_ETFS = {"VGT", "SCHD", "XLE", "XLF", "XLK", "XLV", "ARKK", "SMH", "SOXX", "JEPI", "JEPQ", "IWM"}

def analyze_portfolio_health(portfolio_df, market_data, sector_p_df):
    """
    Asset-style differentiated diagnostic algorithm
    Applies custom concentration thresholds for Broad ETFs / Sector ETFs / Single Stocks
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

    # 1. Style-differentiated concentration analysis
    for t, pct in pos_pcts.items():
        m_info = market_data.get(t, {})
        quote_type = m_info.get('quote_type', 'EQUITY').upper()
        
        is_broad_etf = t in BROAD_MARKET_ETFS
        is_sector_etf = t in SECTOR_THEME_ETFS or (quote_type in ['ETF', 'MUTUALFUND'] and not is_broad_etf)
        is_single_stock = not is_broad_etf and not is_sector_etf

        if is_broad_etf:
            # 🌐 Broad ETF Thresholds: > 65% Danger, > 50% Notice
            if pct > 65.0:
                suggestions.append({
                    "level": "DANGER",
                    "title": f"🔴 Broad ETF Concentration High: {t} at {pct:.1f}%",
                    "desc": f"{t} is a broad market ETF. While highly diversified, exceeding 65% limits exposure to complementary asset styles (such as dividend or high-growth assets)."
                })
            elif pct > 50.0:
                suggestions.append({
                    "level": "INFO",
                    "title": f"🔵 Core Anchor Position: {t} at {pct:.1f}%",
                    "desc": f"{t} serves as a solid core holding (>50%). Future cash injections could be directed toward satellite assets (e.g., sector ETFs or individual stocks)."
                })

        elif is_sector_etf:
            # 🧱 Sector/Theme ETF Thresholds: > 45% Danger, > 35% Warning
            if pct > 45.0:
                suggestions.append({
                    "level": "DANGER",
                    "title": f"🔴 High Sector/Theme ETF Concentration: {t} at {pct:.1f}%",
                    "desc": f"{t} is a sector/style ETF. Allocation above 45% exposes the portfolio to cyclical industry downturns or valuation compression."
                })
            elif pct > 35.0:
                suggestions.append({
                    "level": "WARNING",
                    "title": f"🟡 Elevated Sector/Theme ETF Weight: {t} at {pct:.1f}%",
                    "desc": f"{t} weight exceeds 35%. Consider pausing additions to this theme and allocating new capital into broad indexes or uncorrelated assets."
                })

        elif is_single_stock:
            # 🏢 Single Stock Thresholds: > 30% Danger, > 15% Warning
            if pct > 30.0:
                suggestions.append({
                    "level": "DANGER",
                    "title": f"🔴 High Single-Stock Concentration Risk: {t} at {pct:.1f}%",
                    "desc": f"Single stock {t} exceeds 30% of total portfolio value. Single stocks carry company-specific idiosyncratic risks; strongly consider trimming or locking in profits."
                })
            elif pct > 15.0:
                suggestions.append({
                    "level": "WARNING",
                    "title": f"🟡 Single-Stock Weight Alert: {t} at {pct:.1f}%",
                    "desc": f"Single stock {t} exceeds 15% weight. Keeping individual equity weights controlled helps mitigate overall portfolio volatility."
                })

    # 2. Look-through sector concentration (> 38% Warning, > 50% Danger)
    if not sector_p_df.empty:
        top_sector = sector_p_df.iloc[0]
        sec_name = top_sector['Sector']
        sec_weight = top_sector['Weight']
        
        if sec_weight > 50.0:
            suggestions.append({
                "level": "DANGER",
                "title": f"🔴 Severe Sector Exposure: {sec_name} at {sec_weight:.1f}%",
                "desc": f"Over half of total portfolio value is concentrated in the **{sec_name}** sector (combining direct stock holdings and ETF underlying holdings)."
            })
        elif sec_weight > 38.0:
            suggestions.append({
                "level": "WARNING",
                "title": f"🟡 High Sector Preference: {sec_name} at {sec_weight:.1f}%",
                "desc": f"Portfolio allocation is heavily concentrated in the **{sec_name}** sector (>38%). Be mindful of sector valuation swings."
            })

    if not suggestions:
        suggestions.append({
            "level": "SUCCESS",
            "title": "🟢 Balanced Asset Allocation & Style Mix",
            "desc": "Current allocation across broad ETFs, sector ETFs, and individual equities meets risk-control criteria with no severe concentration risks."
        })

    return suggestions


def calculate_portfolio_rebalance(portfolio_df, market_data, new_cash=0.0):
    """
    Calculates rebalance orders for existing holdings and new cash inflow
    based on target weights (target_pct).
    """
    total_current_val = 0.0
    rows_data = []

    # 1. Aggregate current values and target weights
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

    # 2. Calculate target values and buy/sell trade instructions
    for item in rows_data:
        t = item['ticker']
        price = item['price']
        curr_val = item['current_val']
        curr_pct = (curr_val / total_current_val * 100) if total_current_val > 0 else 0.0
        target_pct = item['target_pct']
        
        target_val = target_total_val * (target_pct / 100.0)
        diff_val = target_val - curr_val
        diff_shares = (diff_val / price) if price > 0 else 0.0
        
        if diff_val > 10:  # Buy threshold $10
            action = "🟢 BUY"
        elif diff_val < -10:  # Sell threshold -$10
            action = "🔴 SELL"
        else:
            action = "⚪ HOLD"
            
        orders.append({
            "Ticker": t,
            "Current Price ($)": price,
            "Current Value ($)": curr_val,
            "Actual Weight (%)": curr_pct,
            "Target Weight (%)": target_pct,
            "Deviation (%)": curr_pct - target_pct,
            "Action": action,
            "Trade Amount ($)": abs(diff_val),
            "Trade Shares": abs(diff_shares)
        })

    return pd.DataFrame(orders), total_current_val, target_total_val


def calculate_portfolio_dividends(portfolio_df, market_data, raw_dividends_dict):
    """
    Calculates weighted dividend yield, projected annual cashflow, 
    and estimated 12-month monthly passive income breakdown.
    """
    total_portfolio_value = 0.0
    total_annual_cashflow = 0.0
    monthly_cashflow = {m: 0.0 for m in range(1, 13)}
    breakdown_rows = []

    # 1. Iterate over holdings to compute dividends and payment months
    for _, row in portfolio_df.iterrows():
        t = row['ticker'].strip().upper()
        shares = row['shares']
        cost_price = row['cost_price']
        
        m_info = market_data.get(t, {})
        latest_price = m_info.get('latest_price', cost_price)
        pos_val = shares * latest_price
        total_portfolio_value += pos_val
        
        div_yield = m_info.get('div_yield', 0.0)  # TTM Dividend Yield (%)
        divs = raw_dividends_dict.get(t, pd.Series(dtype=float))
        
        annual_div_per_share = (div_yield / 100.0) * latest_price
        pos_annual_cashflow = shares * annual_div_per_share
        total_annual_cashflow += pos_annual_cashflow
        
        pay_months = []
        if not divs.empty:
            one_year_ago = datetime.now() - timedelta(days=365)
            recent_divs = divs[divs.index >= one_year_ago]
            if not recent_divs.empty:
                pay_months = sorted(list(set(recent_divs.index.month)))
        
        # Default to standard quarterly dividend schedule (March, June, September, December)
        if not pay_months:
            pay_months = [3, 6, 9, 12]
            
        div_per_payout = pos_annual_cashflow / len(pay_months) if pay_months else 0.0
        for m in pay_months:
            monthly_cashflow[m] += div_per_payout
            
        breakdown_rows.append({
            "Ticker": t,
            "Market Value ($)": pos_val,
            "Dividend Yield (TTM %)": div_yield,
            "Annual Div / Share ($)": annual_div_per_share,
            "Est. Annual Dividend ($)": pos_annual_cashflow,
            "Payout Months": ", ".join([f"{m}" for m in pay_months])
        })

    portfolio_div_yield = (total_annual_cashflow / total_portfolio_value * 100.0) if total_portfolio_value > 0 else 0.0

    monthly_df = pd.DataFrame([
        {"Month": f"M{m}", "Month_Num": m, "Est. Dividends ($)": monthly_cashflow[m]}
        for m in range(1, 13)
    ])

    return {
        "portfolio_div_yield": portfolio_div_yield,
        "total_annual_cashflow": total_annual_cashflow,
        "monthly_df": monthly_df,
        "breakdown_df": pd.DataFrame(breakdown_rows)
    }