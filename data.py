import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ETF 元数据映射 (名称与描述)
ETF_METADATA = {
    "VOO": {
        "name": "Vanguard S&P 500 ETF",
        "category": "标普 500 宽基",
        "desc": "追踪标普 500 指数，包含美国 500 家顶尖上市公司，是全球最具代表性的宽基 ETF 之一。"
    },
    "VGT": {
        "name": "Vanguard Information Technology ETF",
        "category": "科技行业主题",
        "desc": "专注美国信息技术行业，重仓苹果、微软、英伟达等科技巨头，具备高成长性与高波动特征。"
    },
    "SCHD": {
        "name": "Schwab U.S. Dividend Equity ETF",
        "category": "高股息成长",
        "desc": "追踪道琼斯美国 100 红利指数，筛选连续 10 年派息且基本面强劲的高股息优质企业。"
    }
}


@st.cache_data(ttl=3600)
def load_etf_data(ticker_symbol="VOO"):
    """通用获取 ETF 历史价格、info 字典以及分红数据"""
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="max")
    if hist.empty:
        raise ValueError(f"未能获取到 {ticker_symbol} 的历史价格数据")
    hist.index = hist.index.tz_localize(None) # type: ignore
    
    info_raw = ticker.info
    info = {k: v for k, v in info_raw.items() if isinstance(v, (int, float, str, bool, list, dict))}
    
    dividends = ticker.dividends
    if not dividends.empty:
        dividends.index = dividends.index.tz_localize(None) # type: ignore
        
    return hist, info, dividends


@st.cache_data(ttl=86400)
def load_etf_holdings_and_sectors(ticker_symbol="VOO"):
    """通用获取实时行业分布与 Top 10 重仓股 (含静态兜底)"""
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

    # 针对不同标的的兜底数据
    if sector_df.empty or holdings_df.empty:
        fallback_data = {
            "VOO": {
                "sectors": pd.DataFrame({"Sector": ["信息技术", "金融", "医疗健康", "可选消费", "通讯服务", "工业", "其他"], "Weight": [31.5, 13.2, 11.8, 10.2, 8.9, 8.3, 16.1]}),
                "holdings": pd.DataFrame({"Ticker": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "BRK.B", "LLY", "AVGO", "TSLA"], "Company": ["Apple Inc.", "Microsoft Corp.", "NVIDIA Corp.", "Amazon.com Inc.", "Meta Platforms", "Alphabet Inc.", "Berkshire Hathaway", "Eli Lilly", "Broadcom Inc.", "Tesla Inc."], "Weight (%)": [6.8, 6.5, 6.1, 3.6, 2.4, 2.0, 1.7, 1.5, 1.4, 1.3]})
            },
            "VGT": {
                "sectors": pd.DataFrame({"Sector": ["软件服务", "半导体", "技术硬件", "电子设备", "其他"], "Weight": [38.2, 32.5, 22.1, 5.2, 2.0]}),
                "holdings": pd.DataFrame({"Ticker": ["AAPL", "MSFT", "NVDA", "AVGO", "CRM", "AMD", "ACN", "ADBE", "ORCL", "CSCO"], "Company": ["Apple Inc.", "Microsoft Corp.", "NVIDIA Corp.", "Broadcom Inc.", "Salesforce Inc.", "AMD", "Accenture", "Adobe Inc.", "Oracle Corp.", "Cisco Systems"], "Weight (%)": [16.2, 14.5, 13.8, 4.5, 2.8, 2.2, 2.1, 2.0, 1.9, 1.8]})
            },
            "SCHD": {
                "sectors": pd.DataFrame({"Sector": ["金融", "医疗健康", "工业", "必需消费", "信息技术", "能源", "其他"], "Weight": [17.5, 16.2, 15.8, 14.1, 11.2, 9.8, 15.4]}),
                "holdings": pd.DataFrame({"Ticker": ["HD", "ABBV", "KO", "CVX", "MRK", "PEP", "AMGN", "VZ", "TXN", "LMT"], "Company": ["Home Depot", "AbbVie Inc.", "Coca-Cola Co.", "Chevron Corp.", "Merck & Co.", "PepsiCo Inc.", "Amgen Inc.", "Verizon", "Texas Instruments", "Lockheed Martin"], "Weight (%)": [4.2, 4.1, 4.0, 3.9, 3.8, 3.7, 3.6, 3.5, 3.4, 3.3]})
            }
        }
        target_fallback = fallback_data.get(ticker_symbol, fallback_data["VOO"])
        if sector_df.empty:
            sector_df = target_fallback["sectors"]
        if holdings_df.empty:
            holdings_df = target_fallback["holdings"]

    return sector_df, holdings_df


@st.cache_data(ttl=3600)
def load_all_historical_returns(tickers=["VOO", "VGT", "SCHD"]):
    """获取多标的原始收盘价数据 (不预先进行归一化)"""
    df_combined = pd.DataFrame()
    for t in tickers:
        hist = yf.Ticker(t).history(period="max")
        if not hist.empty:
            hist.index = hist.index.tz_localize(None) # type: ignore
            df_combined[t] = hist['Close']
            
    # 清理丢失数据并对齐日期
    return df_combined.dropna()


def filter_by_range(df, range_str):
    """根据时间范围筛选单标的或多标的历史数据/分红数据"""
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
    """根据时间跨度选项返回显示的最多年份数量 (供 Tab 3 年度柱状图使用)"""
    mapping = {
        "1Y": 1,
        "3Y": 3,
        "5Y": 5,
        "10Y": 10,
        "Max": 30
    }
    return mapping.get(range_str, 10)


def calculate_ttm_dividend_yield(dividends, latest_price, info):
    if not dividends.empty:
        one_year_ago = datetime.now() - timedelta(days=365)
        recent_divs = dividends[dividends.index >= one_year_ago]
        ttm_dividends = recent_divs.sum()
        if latest_price > 0:
            return (ttm_dividends / latest_price) * 100
            
    raw_yield = info.get('dividendYield', 0.015)
    return raw_yield * 100 if raw_yield < 0.2 else raw_yield


def get_etf_aum(info, ticker_symbol):
    """
    稳健提取或计算 ETF 资产规模 (AUM)
    解决 Streamlit Cloud 服务器上 yfinance info 返回 None 的问题
    """
    # 1. 尝试从多个 Yahoo Finance info 字段中获取
    aum = info.get('totalAssets') or info.get('marketCap') or info.get('netAssets')
    
    if isinstance(aum, (int, float)) and aum > 0:
        return aum
        
    # 2. 如果云端 API 未能获取到 AUM，使用官方静态估算基准数据兜底 (单位: 美元)
    known_aums = {
        "VOO": 520_000_000_000,  # ~5200 亿美金
        "VGT": 75_000_000_000,   # ~750 亿美金
        "SCHD": 58_000_000_000   # ~580 亿美金
    }
    
    return known_aums.get(ticker_symbol, 0)