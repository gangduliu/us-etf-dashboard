import streamlit as st
import pandas as pd
from data import (
    load_stock_or_etf_data, load_portfolio_market_data, 
    get_portfolio_sector_breakdown, load_portfolio_from_file, 
    export_portfolio_to_json, export_portfolio_to_csv
)
from strategy import (
    calculate_portfolio_metrics, analyze_portfolio_health, 
    calculate_portfolio_rebalance, calculate_portfolio_dividends
)
from ui import (
    inject_custom_css, render_portfolio_summary_cards, 
    render_portfolio_charts, render_portfolio_advisory, 
    render_rebalance_dashboard, render_dividend_dashboard
)

st.set_page_config(page_title="Portfolio Management", page_icon="💼", layout="wide")
inject_custom_css()

DEFAULT_PORTFOLIO = pd.DataFrame([
    {"ticker": "SPYM", "shares": 5, "cost_price": 90, "target_pct": 60},
    {"ticker": "SCHG", "shares": 10, "cost_price": 35, "target_pct": 40}
])

if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = DEFAULT_PORTFOLIO.copy()
if "uploader_key_id" not in st.session_state:
    st.session_state.uploader_key_id = 0
if "editor_key_id" not in st.session_state:
    st.session_state.editor_key_id = 0

def handle_file_upload():
    current_key = f"portfolio_file_uploader_{st.session_state.uploader_key_id}"
    uploaded_file = st.session_state.get(current_key)
    if uploaded_file is not None:
        new_df = load_portfolio_from_file(uploaded_file)
        if new_df is not None and not new_df.empty:
            st.session_state.portfolio_data = new_df
            st.toast("✅ Portfolio data imported successfully!", icon="🎉")
            st.session_state.uploader_key_id += 1

# Portfolio Editing Panel
with st.expander("✏️ Edit Portfolio Holdings & Target Allocation (Supports Backup Import & Reset)", expanded=False):
    col_up, col_dl_json, col_dl_csv, col_reset = st.columns([1.3, 0.9, 0.9, 0.9], gap="medium")
    
    with col_up:
        dynamic_uploader_key = f"portfolio_file_uploader_{st.session_state.uploader_key_id}"
        st.file_uploader(
            "📤 Restore Portfolio Backup (.csv / .json)",
            type=["json", "csv"],
            key=dynamic_uploader_key,
            on_change=handle_file_upload
        )
    with col_dl_json:
        st.write("")
        json_str = export_portfolio_to_json(st.session_state.portfolio_data)
        st.download_button("💾 Download JSON", data=json_str, file_name="portfolio_backup.json", mime="application/json", use_container_width=True)
    with col_dl_csv:
        st.write("")
        csv_str = export_portfolio_to_csv(st.session_state.portfolio_data)
        st.download_button("📊 Export CSV", data=csv_str, file_name="portfolio_backup.csv", mime="text/csv", use_container_width=True)
    with col_reset:
        st.write("")
        if st.button("🔄 Reset to Default Portfolio", use_container_width=True):
            st.session_state.portfolio_data = DEFAULT_PORTFOLIO.copy()
            st.session_state.editor_key_id += 1
            st.toast("🔄 Restored default sample portfolio!", icon="💡")

    dynamic_editor_key = f"portfolio_editor_{st.session_state.editor_key_id}"
    edited_portfolio = st.data_editor(
        st.session_state.portfolio_data,
        column_config={
            "ticker": st.column_config.TextColumn("Ticker", required=True, width="small"),
            "shares": st.column_config.NumberColumn("Shares", min_value=0, step=1, format="%d"),
            "cost_price": st.column_config.NumberColumn("Cost Basis ($)", min_value=0, step=0.001, format="$%.3f"),
            "target_pct": st.column_config.NumberColumn("Target Weight (%)", min_value=0, max_value=100, step=5, format="%d%%")
        },
        num_rows="dynamic",
        use_container_width=True,
        key=dynamic_editor_key
    )
    st.session_state.portfolio_data = edited_portfolio

valid_portfolio = st.session_state.portfolio_data.dropna()

if not valid_portfolio.empty:
    portfolio_tickers = valid_portfolio['ticker'].unique().tolist()
    market_data = load_portfolio_market_data(portfolio_tickers)
    p_metrics = calculate_portfolio_metrics(valid_portfolio, market_data)
    sector_p_df = get_portfolio_sector_breakdown(valid_portfolio, market_data)

    render_portfolio_summary_cards(p_metrics)

    suggestions = analyze_portfolio_health(valid_portfolio, market_data, sector_p_df)
    render_portfolio_advisory(suggestions)
    
    render_portfolio_charts(p_metrics, sector_p_df)

    st.markdown('<div class="section-title">📋 Portfolio Holdings Details</div>', unsafe_allow_html=True)
    st.dataframe(p_metrics['details_df'], hide_index=True, use_container_width=True)

    st.divider()

    col_rebal_title, col_cash_input = st.columns([2, 1])
    with col_rebal_title:
        st.write("")
    with col_cash_input:
        new_cash = st.number_input("💵 Additional Capital to Invest ($USD):", min_value=0.0, value=0.0, step=100.0)

    rebalance_df, total_curr_val, target_tot_val = calculate_portfolio_rebalance(valid_portfolio, market_data, new_cash)
    render_rebalance_dashboard(rebalance_df, total_curr_val, target_tot_val, new_cash)

    st.divider()

    raw_dividends_dict = {}
    for _, row in valid_portfolio.iterrows():
        t = row['ticker'].strip().upper()
        try:
            _, _, divs, _ = load_stock_or_etf_data(t)
            raw_dividends_dict[t] = divs
        except Exception:
            pass

    div_metrics = calculate_portfolio_dividends(valid_portfolio, market_data, raw_dividends_dict)
    render_dividend_dashboard(div_metrics)
else:
    st.info("💡 Please expand the editor panel above to add at least one holding.")