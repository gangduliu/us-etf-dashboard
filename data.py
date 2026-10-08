import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)
def load_stock_or_etf_data(ticker_symbol):
    """通用获取任意美股/ETF 的历史价格、info 字典以及分红数据"""
    ticker_symbol = ticker_symbol.strip().upper()
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. 历史价格数据
    hist = ticker.history(period="max")
    if hist.empty:
        raise ValueError(f"未能查询到代码为 '{ticker_symbol}' 的股票或 ETF 数据，请检查代码拼写是否正确。")
    hist.index = hist.index.tz_localize(None) # type: ignore
    
    # 2. 基本信息字典
    info_raw = ticker.info or {}
    info = {k: v for k, v in info_raw.items() if isinstance(v, (int, float, str, bool, list, dict))}
    
    # 3. 历史分红记录
    dividends = ticker.dividends
    if not dividends.empty:
        dividends.index = dividends.index.tz_localize(None) # type: ignore
        
    # 判断是否为 ETF
    is_etf = info.get('quoteType') == 'ETF' or info.get('fundFamily') is not None
    
    return hist, info, dividends, is_etf


@st.cache_data(ttl=86400)
def load_etf_holdings_and_sectors(ticker_symbol):
    """动态获取 ETF 行业分布与重仓股"""
    ticker_symbol = ticker_symbol.strip().upper()
    ticker = yf.Ticker(ticker_symbol)
    sector_df = pd.DataFrame()
    holdings_df = pd.DataFrame()
    
    try:
        funds_data = ticker.funds_data
        
        # 1. 行业分布
        if hasattr(funds_data, 'sector_weightings') and funds_data.sector_weightings:
            sectors = funds_data.sector_weightings
            sector_df = pd.DataFrame(list(sectors.items()), columns=['Sector', 'Weight'])
            sector_df['Weight'] = sector_df['Weight'] * 100
        
        # 2. 重仓股
        if hasattr(funds_data, 'top_holdings') and funds_data.top_holdings is not None:
            holdings_raw = funds_data.top_holdings.reset_index()
            holdings_raw.columns = ['Ticker', 'Company', 'Weight (%)']
            holdings_raw['Weight (%)'] = holdings_raw['Weight (%)'] * 100
            holdings_df = holdings_raw.head(10)
    except Exception:
        pass

    return sector_df, holdings_df


@st.cache_data(ttl=3600)
def load_all_historical_returns(tickers=["VOO", "QQQ", "AAPL", "NVDA"]):
    """获取指定代码组的原始收盘价数据 (供对比页使用)"""
    df_combined = pd.DataFrame()
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period="max")
            if not hist.empty:
                hist.index = hist.index.tz_localize(None) # type: ignore
                df_combined[t] = hist['Close']
        except Exception:
            pass
            
    return df_combined.dropna()


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


def calculate_ttm_dividend_yield(dividends, latest_price, info):
    if not dividends.empty:
        one_year_ago = datetime.now() - timedelta(days=365)
        recent_divs = dividends[dividends.index >= one_year_ago]
        ttm_dividends = recent_divs.sum()
        if latest_price > 0:
            return (ttm_dividends / latest_price) * 100
            
    raw_yield = info.get('dividendYield', 0.0) or info.get('trailingAnnualDividendYield', 0.0)
    return raw_yield * 100 if raw_yield < 0.2 else raw_yield


def get_asset_size_or_market_cap(info):
    """自动判断提取市值 (Market Cap) 或基金规模 (AUM)"""
    val = info.get('totalAssets') or info.get('marketCap') or info.get('netAssets') or 0
    return val