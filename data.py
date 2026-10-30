import json
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def check_is_etf(ticker_symbol, info):
    """
    More robust ETF detection function with multi-layer fallback logic
    """
    ticker_symbol = ticker_symbol.upper().strip()
    
    # 1. Core whitelist fallback (prevents false negatives for mainstream ETFs when cloud IP is blocked by Yahoo resulting in empty info)
    known_etfs = {
        'VOO', 'SPY', 'QQQ', 'IVV', 'VTI', 'VEA', 'VWO', 'AGG', 'BND', 
        'GLD', 'IAU', 'IWM', 'EEM', 'VNQ', 'SCHD', 'ARKK', 'XLK', 'XLF'
    }
    if ticker_symbol in known_etfs:
        return True

    # 2. Normal check via info dictionary
    if info and isinstance(info, dict) and len(info) > 1:
        quote_type = info.get('quoteType', '')
        fund_family = info.get('fundFamily')
        
        return quote_type == 'ETF' or fund_family is not None
    
    return True


@st.cache_data(ttl=3600)
def load_stock_or_etf_data(ticker_symbol):
    """Universal fetcher for historical prices, info dictionary, and dividend data for any US stock or ETF"""
    ticker_symbol = ticker_symbol.strip().upper()
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Historical price data
    hist = ticker.history(period="max")
    if hist.empty:
        raise ValueError(f"Failed to fetch stock or ETF data for '{ticker_symbol}'. Please check if the ticker symbol is correct.")
    hist.index = hist.index.tz_localize(None) # type: ignore
    
    # 2. Basic info dictionary
    info_raw = ticker.info or {}
    info = {k: v for k, v in info_raw.items() if isinstance(v, (int, float, str, bool, list, dict))}

    # Extract expense ratio (sequentially try multiple potential keys)
    raw_expense_ratio = (
        info.get('expenseRatio') or 
        info.get('netExpenseRatio') or 
        info.get('annualReportExpenseRatio') or 
        0.0
    )

    info['expenseRatio'] = raw_expense_ratio  # type: ignore
    
    # 3. Historical dividend records
    dividends = ticker.dividends
    if not dividends.empty:
        dividends.index = dividends.index.tz_localize(None) # type: ignore
        
    # Check if ETF
    is_etf = check_is_etf(ticker_symbol, info)
    
    return hist, info, dividends, is_etf


@st.cache_data(ttl=86400)
def load_etf_holdings_and_sectors(ticker_symbol):
    """Dynamically fetch ETF sector distribution and top holdings"""
    ticker_symbol = ticker_symbol.strip().upper()
    ticker = yf.Ticker(ticker_symbol)
    sector_df = pd.DataFrame()
    holdings_df = pd.DataFrame()
    
    try:
        funds_data = ticker.funds_data
        
        # 1. Sector distribution
        if hasattr(funds_data, 'sector_weightings') and funds_data.sector_weightings:
            sectors = funds_data.sector_weightings
            sector_df = pd.DataFrame(list(sectors.items()), columns=['Sector', 'Weight'])
            sector_df['Weight'] = sector_df['Weight'] * 100
        
        # 2. Top holdings
        if hasattr(funds_data, 'top_holdings') and funds_data.top_holdings is not None:
            holdings_raw = funds_data.top_holdings.reset_index()
            holdings_raw.columns = ['Ticker', 'Company', 'Weight (%)']
            holdings_raw['Weight (%)'] = holdings_raw['Weight (%)'] * 100
            holdings_df = holdings_raw.head(10)
    except Exception:
        pass

    return sector_df, holdings_df


@st.cache_data(ttl=3600)
def load_all_historical_returns(tickers):
    """Fetch pure close price history for a given group of tickers (for comparison page)"""
    df_combined = pd.DataFrame()
    for t in tickers:
        try:
            ticker_obj = yf.Ticker(t)
            hist = ticker_obj.history(period="max")
            
            if not hist.empty and 'Close' in hist.columns:
                hist.index = hist.index.tz_localize(None) # type: ignore
                df_combined[t] = hist['Close']
        except Exception as e:
            print(f"Failed to fetch historical data for {t}: {e}")
            pass
            
    return df_combined.dropna()


@st.cache_data(ttl=3600)
def fetch_ticker_fundamentals(tickers):
    """
    Fetch Latest Price, Avg Daily Trading Volume (3M), and Expense Ratio (or N/A for individual stocks) using yfinance.
    Returns DataFrame with Rows = Tickers, Columns = Metrics.
    """
    info_list = []
    for ticker in tickers:
        try:
            yt = yf.Ticker(ticker)
            info = yt.info
            
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
            avg_vol = info.get("averageVolume") or info.get("averageDailyVolume3Month") or info.get("volume")
            exp_ratio = info.get("expenseRatio") or info.get("netExpenseRatio")
            
            if exp_ratio is not None:
                exp_ratio_str = f"{exp_ratio * 100:.2f}%" if exp_ratio < 0.01 else f"{exp_ratio:.2f}%"
            else:
                exp_ratio_str = "N/A (Stock)"
                
            info_list.append({
                "Ticker": ticker,
                "Latest Price": f"${price:,.2f}" if price else "N/A",
                "Avg Vol (3M)": f"{avg_vol:,.0f}" if avg_vol else "N/A",
                "Expense Ratio": exp_ratio_str
            })
        except Exception:
            info_list.append({
                "Ticker": ticker,
                "Latest Price": "N/A",
                "Avg Vol (3M)": "N/A",
                "Expense Ratio": "N/A"
            })
    df = pd.DataFrame(info_list).set_index("Ticker")
    return df


def filter_by_range(df, range_str):
    if df is None or df.empty:
        return df
    
    now = datetime.now()
    if range_str == "1Y":
        start = now - timedelta(days=365)
    elif range_str == "3Y":
        start = now - timedelta(days=365*3)
    elif range_str == "5Y":
        start = now - timedelta(days=365*5)
    elif range_str == "10Y":
        start = now - timedelta(days=365*10)
    else:  # "Max"
        return df
        
    return df[df.index >= start]


def get_range_years_limit(range_str):
    mapping = {"1Y": 1, "3Y": 3, "5Y": 5, "10Y": 10, "Max": 30}
    return mapping.get(range_str, 10)


def get_asset_size_or_market_cap(info):
    """Automatically extract Market Cap or Assets Under Management (AUM)"""
    val = info.get('totalAssets') or info.get('marketCap') or info.get('netAssets') or 0
    return val


# Common baseline TTM dividend yield fallback table (used when cloud APIs fail completely)
KNOWN_DIVIDEND_YIELDS = {
    "SCHD": 3.45,
    "VOO": 1.35,
    "VGT": 0.65,
    "QQQ": 0.60,
    "SPY": 1.30,
    "AAPL": 0.50,
    "MSFT": 0.70,
    "NVDA": 0.08,
    "KO": 3.10,
    "PEP": 3.00,
    "JNJ": 3.20,
    "O": 5.40
}


def calculate_ttm_dividend_yield(dividends, latest_price, info, ticker_symbol=""):
    """
    Three-tier progressive dividend yield calculation:
    1. Prioritize total actual payouts over the past 12 months / latest price
    2. Extract various Yield fields from the info dictionary
    3. Fallback to known static baselines
    """
    ticker_symbol = ticker_symbol.strip().upper()

    # 1. Tier 1: Calculate based on real historical dividends over the past 365 days
    if dividends is not None and not dividends.empty and latest_price > 0:
        try:
            one_year_ago = datetime.now() - timedelta(days=365)
            # Handle timezone-aware/naive timestamps
            if dividends.index.tz is not None:
                dividends.index = dividends.index.tz_localize(None)
            
            recent_divs = dividends[dividends.index >= one_year_ago]
            ttm_sum = recent_divs.sum()
            
            if ttm_sum > 0:
                calc_yield = (ttm_sum / latest_price) * 100.0
                return round(calc_yield, 2)
        except Exception:
            pass

    # 2. Tier 2: Extract from various potential fields in the info dictionary
    if info:
        raw_yield = (
            info.get('dividendYield') or 
            info.get('trailingAnnualDividendYield') or 
            info.get('yield') or 0.0
        )
        if isinstance(raw_yield, (int, float)) and raw_yield > 0:
            # yfinance returns decimals for some fields (e.g., 0.0345) and percentages for others (e.g., 3.45)
            final_yield = raw_yield * 100.0 if raw_yield < 0.25 else raw_yield
            return round(final_yield, 2)

    # 3. Tier 3: Known static baseline fallback
    if ticker_symbol in KNOWN_DIVIDEND_YIELDS:
        return KNOWN_DIVIDEND_YIELDS[ticker_symbol]

    return 0.0


@st.cache_data(ttl=900)
def load_portfolio_market_data(tickers):
    """Batch fetch latest price, previous close price, and robustly calculated dividend yield for portfolio holdings"""
    data = {}
    for ticker_symbol in tickers:
        t = ticker_symbol.strip().upper()
        if not t:
            continue
        try:
            ticker = yf.Ticker(t)
            hist = ticker.history(period="5d")
            if not hist.empty:
                latest_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
                
                info = ticker.info or {}
                dividends = ticker.dividends
                
                # 👈 Use enhanced dividend yield calculation utility
                div_yield = calculate_ttm_dividend_yield(dividends, latest_price, info, t)

                data[t] = {
                    "latest_price": latest_price,
                    "prev_price": prev_price,
                    "div_yield": div_yield, # Ensure a numeric value is always obtained
                    "name": info.get('shortName') or info.get('longName') or t,
                    "quote_type": info.get('quoteType', 'EQUITY')
                }
        except Exception:
            # Assign static fallback on exception to prevent crashes
            fallback_yield = KNOWN_DIVIDEND_YIELDS.get(t, 0.0)
            data[t] = {
                "latest_price": 100.0,
                "prev_price": 100.0,
                "div_yield": fallback_yield,
                "name": t,
                "quote_type": 'EQUITY'
            }
    return data


@st.cache_data(ttl=86400)
def get_portfolio_sector_breakdown(portfolio_df, market_data):
    """Look-through calculation of comprehensive portfolio sector allocation distribution (%)"""
    sector_weights = {}
    total_portfolio_value = sum(
        row['shares'] * market_data.get(row['ticker'], {}).get('latest_price', row['cost_price'])
        for _, row in portfolio_df.iterrows()
    )
    
    if total_portfolio_value == 0:
        return pd.DataFrame()

    for _, row in portfolio_df.iterrows():
        t = row['ticker']
        shares = row['shares']
        price = market_data.get(t, {}).get('latest_price', row['cost_price'])
        position_value = shares * price
        position_weight = position_value / total_portfolio_value

        # Get sector breakdown for single asset
        sector_df, _ = load_etf_holdings_and_sectors(t)
        if not sector_df.empty:
            for _, s_row in sector_df.iterrows():
                sec_name = s_row['Sector']
                sec_w = (s_row['Weight'] / 100) * position_weight * 100
                sector_weights[sec_name] = sector_weights.get(sec_name, 0) + sec_w
        else:
            # Individual stock or other
            sec_name = "Other / Stock"
            sector_weights[sec_name] = sector_weights.get(sec_name, 0) + (position_weight * 100)

    res_df = pd.DataFrame(list(sector_weights.items()), columns=['Sector', 'Weight'])
    return res_df.sort_values(by='Weight', ascending=False)


def export_portfolio_to_json(df: pd.DataFrame) -> str:
    """Convert portfolio DataFrame to JSON formatted string for download"""
    valid_df = df.dropna(subset=['ticker'])
    records = valid_df.to_dict(orient="records")
    return json.dumps(records, ensure_ascii=False, indent=2)


def export_portfolio_to_csv(df: pd.DataFrame) -> str:
    """Convert portfolio DataFrame to CSV formatted string for download"""
    valid_df = df.dropna(subset=['ticker'])
    return valid_df.to_csv(index=False, encoding='utf-8-sig')


def load_portfolio_from_file(uploaded_file) -> pd.DataFrame:
    """Parse and rebuild portfolio DataFrame from user-uploaded CSV or JSON file"""
    filename = uploaded_file.name.lower()
    
    try:
        if filename.endswith(".json"):
            data = json.load(uploaded_file)
            df = pd.DataFrame(data)
        elif filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            st.error("❌ Unsupported file format. Please upload a .json or .csv file!")
            return None # type: ignore
            
        # Verify necessary columns exist
        required_cols = {'ticker', 'shares', 'cost_price'}
        if not required_cols.issubset(set(df.columns)):
            st.error("❌ Format mismatch: File is missing required fields (ticker, shares, cost_price)")
            return None # type: ignore
            
        # Ensure correct data types
        df['ticker'] = df['ticker'].astype(str).str.strip().str.upper()
        df['shares'] = pd.to_numeric(df['shares'], errors='coerce').fillna(1.0)
        df['cost_price'] = pd.to_numeric(df['cost_price'], errors='coerce').fillna(0.0)
        if 'target_pct' in df.columns:
            df['target_pct'] = pd.to_numeric(df['target_pct'], errors='coerce').fillna(0.0)
        else:
            df['target_pct'] = 0.0

        return df.dropna(subset=['ticker'])
    except Exception as e:
        st.error(f"❌ Failed to read portfolio file: {e}")
        return None # type: ignore