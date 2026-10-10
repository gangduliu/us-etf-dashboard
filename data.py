import json
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

    #提取管理费率 (依次尝试多个可能存在的 key)
    raw_expense_ratio = (
        info.get('expenseRatio') or 
        info.get('netExpenseRatio') or 
        info.get('annualReportExpenseRatio') or 
        0.0
    )

    info['expenseRatio'] = raw_expense_ratio  # type: ignore
    
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


def get_asset_size_or_market_cap(info):
    """自动判断提取市值 (Market Cap) 或基金规模 (AUM)"""
    val = info.get('totalAssets') or info.get('marketCap') or info.get('netAssets') or 0
    return val


# 常见标的基准 TTM 股息率兜底表 (云端 API 彻底失效时使用)
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
    三层递进算清股息率：
    1. 优先使用近 12 个月实际派息总额 / 最新股价
    2. 其次提取 info 字典中的各种 Yield 字段
    3. 最后使用 Known 静态基准兜底
    """
    ticker_symbol = ticker_symbol.strip().upper()

    # 1. 第一层：基于近 365 天真实历史分红数据计算
    if dividends is not None and not dividends.empty and latest_price > 0:
        try:
            one_year_ago = datetime.now() - timedelta(days=365)
            # 兼容带/不带时区的时间戳
            if dividends.index.tz is not None:
                dividends.index = dividends.index.tz_localize(None)
            
            recent_divs = dividends[dividends.index >= one_year_ago]
            ttm_sum = recent_divs.sum()
            
            if ttm_sum > 0:
                calc_yield = (ttm_sum / latest_price) * 100.0
                return round(calc_yield, 2)
        except Exception:
            pass

    # 2. 第二层：从 info 字典多种可能字段中提取
    if info:
        raw_yield = (
            info.get('dividendYield') or 
            info.get('trailingAnnualDividendYield') or 
            info.get('yield') or 0.0
        )
        if isinstance(raw_yield, (int, float)) and raw_yield > 0:
            # yfinance 部分字段返回小数 (如 0.0345)，部分返回百分比 (如 3.45)
            final_yield = raw_yield * 100.0 if raw_yield < 0.25 else raw_yield
            return round(final_yield, 2)

    # 3. 第三层：已知标的静态基准兜底
    if ticker_symbol in KNOWN_DIVIDEND_YIELDS:
        return KNOWN_DIVIDEND_YIELDS[ticker_symbol]

    return 0.0


@st.cache_data(ttl=900)
def load_portfolio_market_data(tickers):
    """批量获取持仓标的最新价格、前一日收盘价及强力计算出的股息率"""
    data = {}
    for ticker_symbol in tickers:
        t = ticker_symbol.strip().upper()
        if not t:
            continue
        try:
            ticker = yf.Ticker(t)
            hist = ticker.history(period="5d")
            if not hist.empty:
                latest_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2]) if len(hist) > 1 else latest_price
                
                info = ticker.info or {}
                dividends = ticker.dividends
                
                # 👈 使用强化版的股息率计算工具
                div_yield = calculate_ttm_dividend_yield(dividends, latest_price, info, t)

                data[t] = {
                    "latest_price": latest_price,
                    "prev_price": prev_price,
                    "div_yield": div_yield, # 保证必定能拿到数值
                    "name": info.get('shortName') or info.get('longName') or t,
                    "quote_type": info.get('quoteType', 'EQUITY')
                }
        except Exception:
            # 异常时赋予静态兜底，防止崩溃
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
    """穿透计算投资组合的综合行业配置分布 (%)"""
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

        # 获取单标的行业分布
        sector_df, _ = load_etf_holdings_and_sectors(t)
        if not sector_df.empty:
            for _, s_row in sector_df.iterrows():
                sec_name = s_row['Sector']
                sec_w = (s_row['Weight'] / 100) * position_weight * 100
                sector_weights[sec_name] = sector_weights.get(sec_name, 0) + sec_w
        else:
            # 个股或其他
            sec_name = "其他 / 个股"
            sector_weights[sec_name] = sector_weights.get(sec_name, 0) + (position_weight * 100)

    res_df = pd.DataFrame(list(sector_weights.items()), columns=['Sector', 'Weight'])
    return res_df.sort_values(by='Weight', ascending=False)


def export_portfolio_to_json(df: pd.DataFrame) -> str:
    """将持仓 DataFrame 转换为 JSON 格式字符串供下载"""
    valid_df = df.dropna(subset=['ticker'])
    records = valid_df.to_dict(orient="records")
    return json.dumps(records, ensure_ascii=False, indent=2)


def export_portfolio_to_csv(df: pd.DataFrame) -> str:
    """将持仓 DataFrame 转换为 CSV 格式字符串供下载"""
    valid_df = df.dropna(subset=['ticker'])
    return valid_df.to_csv(index=False, encoding='utf-8-sig')


def load_portfolio_from_file(uploaded_file) -> pd.DataFrame:
    """从用户上传的 CSV 或 JSON 文件解析并重建持仓 DataFrame"""
    filename = uploaded_file.name.lower()
    
    try:
        if filename.endswith(".json"):
            data = json.load(uploaded_file)
            df = pd.DataFrame(data)
        elif filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            st.error("❌ 不支持的文件格式，请上传 .json 或 .csv 文件！")
            return None # type: ignore
            
        # 验证必要的列是否存在
        required_cols = {'ticker', 'shares', 'cost_price'}
        if not required_cols.issubset(set(df.columns)):
            st.error("❌ 格式不匹配：文件缺少必要字段 (ticker, shares, cost_price)")
            return None # type: ignore
            
        # 确保数据类型正确
        df['ticker'] = df['ticker'].astype(str).str.strip().str.upper()
        df['shares'] = pd.to_numeric(df['shares'], errors='coerce').fillna(1.0)
        df['cost_price'] = pd.to_numeric(df['cost_price'], errors='coerce').fillna(0.0)
        if 'target_pct' in df.columns:
            df['target_pct'] = pd.to_numeric(df['target_pct'], errors='coerce').fillna(0.0)
        else:
            df['target_pct'] = 0.0

        return df.dropna(subset=['ticker'])
    except Exception as e:
        st.error(f"❌ 读取持仓文件失败: {e}")
        return None # type: ignore