import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import uuid
import sys
import os

# Ensure src package is importable when running from project root or directly
_app_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.dirname(_app_dir)
_project_dir = os.path.dirname(_src_dir)
for _path in [_src_dir, _project_dir]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.workflow.orchestrator import FinanceOrchestrator

st.set_page_config(
    page_title="AI Finance Assistant",
    page_icon="📈",
    layout="wide"
)


@st.cache_resource
def get_orchestrator():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "config.yaml"
    )
    return FinanceOrchestrator(config_path=config_path)


def initialize_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "portfolio_holdings" not in st.session_state:
        st.session_state.portfolio_holdings = []
    if "risk_profile" not in st.session_state:
        st.session_state.risk_profile = "moderate"
    if "user_id" not in st.session_state:
        st.session_state.user_id = None


def render_chat_tab(orchestrator):
    st.header("Financial Assistant Chat")
    st.caption("Ask me anything about investing, markets, portfolio analysis, or financial planning.")

    # Display conversation history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("agent"):
                st.caption(f"Agent: {msg['agent'].replace('_', ' ').title()}")

    # Chat input
    if prompt := st.chat_input("Ask a financial question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = orchestrator.process_query(prompt, st.session_state.session_id)
                response = result["response"]
                agent = result.get("agent", "")
            st.markdown(response)
            if agent:
                st.caption(f"Agent: {agent.replace('_', ' ').title()}")

        st.session_state.messages.append({"role": "assistant", "content": response, "agent": agent})


def render_portfolio_tab(orchestrator):
    st.header("Portfolio Analysis")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Enter Holdings")

        with st.form("add_holding"):
            symbol = st.text_input("Stock Symbol", placeholder="AAPL").upper()
            shares = st.number_input("Number of Shares", min_value=0.01, value=1.0, step=0.01)
            avg_cost = st.number_input("Average Cost per Share ($)", min_value=0.01, value=100.0, step=0.01)

            if st.form_submit_button("Add Holding"):
                if symbol:
                    # Check if already exists, update if so
                    existing = next((h for h in st.session_state.portfolio_holdings if h["symbol"] == symbol), None)
                    if existing:
                        existing["shares"] = shares
                        existing["avg_cost"] = avg_cost
                        st.success(f"Updated {symbol}")
                    else:
                        st.session_state.portfolio_holdings.append({
                            "symbol": symbol, "shares": shares, "avg_cost": avg_cost
                        })
                        st.success(f"Added {symbol}")

        if st.session_state.portfolio_holdings:
            st.subheader("Current Holdings")
            for i, h in enumerate(st.session_state.portfolio_holdings):
                cols = st.columns([3, 1])
                cols[0].write(f"{h['symbol']}: {h['shares']} shares @ ${h['avg_cost']:.2f}")
                if cols[1].button("Remove", key=f"remove_{i}"):
                    st.session_state.portfolio_holdings.pop(i)
                    st.rerun()

            if st.button("Clear All"):
                st.session_state.portfolio_holdings = []
                st.rerun()

    with col2:
        if st.session_state.portfolio_holdings:
            st.subheader("Portfolio Analysis")

            # Save portfolio to session
            portfolio = {"holdings": st.session_state.portfolio_holdings}
            orchestrator.session_manager.update_portfolio(st.session_state.session_id, portfolio)

            # Get analysis
            with st.spinner("Analyzing portfolio..."):
                analysis = orchestrator.market_data.analyze_portfolio(st.session_state.portfolio_holdings)

            if analysis.get("errors"):
                for err in analysis["errors"]:
                    st.warning(err)

            # Summary metrics
            total_value = analysis.get("total_value", 0)
            total_cost = analysis.get("total_cost", 0)
            total_gain = analysis.get("total_gain_loss", 0)
            total_gain_pct = analysis.get("total_gain_loss_pct", 0)

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Value", f"${total_value:,.2f}")
            m2.metric("Total Cost", f"${total_cost:,.2f}")
            m3.metric("Total Gain/Loss", f"${total_gain:,.2f}", delta=f"{total_gain_pct:.1f}%")

            # Holdings table
            if analysis.get("holdings"):
                holdings_df = pd.DataFrame(analysis["holdings"])[
                    ["symbol", "name", "shares", "current_price", "current_value", "gain_loss", "gain_loss_pct"]
                ]
                holdings_df.columns = ["Symbol", "Name", "Shares", "Price", "Value", "Gain/Loss", "Gain/Loss %"]
                holdings_df["Price"] = holdings_df["Price"].map("${:.2f}".format)
                holdings_df["Value"] = holdings_df["Value"].map("${:,.2f}".format)
                holdings_df["Gain/Loss"] = holdings_df["Gain/Loss"].map("${:,.2f}".format)
                holdings_df["Gain/Loss %"] = holdings_df["Gain/Loss %"].map("{:+.1f}%".format)
                st.dataframe(holdings_df, use_container_width=True)

            # Sector pie chart
            if analysis.get("sector_allocation_pct"):
                fig = px.pie(
                    values=list(analysis["sector_allocation_pct"].values()),
                    names=list(analysis["sector_allocation_pct"].keys()),
                    title="Sector Allocation"
                )
                st.plotly_chart(fig, use_container_width=True)

            # AI Analysis button
            if st.button("Get AI Portfolio Analysis"):
                with st.spinner("Analyzing..."):
                    result = orchestrator.process_query(
                        "Analyze my portfolio and give me specific recommendations for improvement.",
                        st.session_state.session_id
                    )
                st.markdown(result["response"])
        else:
            st.info("Add your stock holdings on the left to see portfolio analysis.")


def render_market_tab(orchestrator):
    st.header("Market Overview")

    # Market indices
    with st.spinner("Loading market data..."):
        indices = orchestrator.market_data.get_market_indices()

    if indices:
        cols = st.columns(len(indices))
        for i, (name, data) in enumerate(indices.items()):
            if data and data.get("price"):
                change = data.get("change_pct", 0) or 0
                cols[i].metric(name, f"{data['price']:,.2f}", delta=f"{change:+.2f}%")

def render_profile_tab(orchestrator):
    st.header("Risk Profile")
    st.caption("Choose a risk profile to personalize your financial guidance.")

    options = ["conservative", "moderate", "aggressive"]
    current_index = options.index(st.session_state.risk_profile) if st.session_state.risk_profile in options else 1
    selected_profile = st.radio(
        "Select your risk profile:",
        options,
        index=current_index,
        horizontal=True,
    )

    if st.button("Save Risk Profile"):
        orchestrator.session_manager.update_profile(
            st.session_state.session_id,
            risk_tolerance=selected_profile,
        )
        st.session_state.risk_profile = selected_profile
        st.success(f"Saved risk profile: {selected_profile.title()}")

    st.markdown(
        """
        **Profile descriptions**
        - **Conservative**: preservation first, lower volatility, more defensive guidance.
        - **Moderate**: balanced growth and risk management.
        - **Aggressive**: focus on higher potential returns with higher risk.
        """
    )

    st.divider()
    st.write("Current saved profile:")
    st.info(st.session_state.risk_profile.title())

    st.markdown(
        "Risk profile is persisted for this session and is designed to carry forward to a future login/account flow."
    )
    st.divider()

    # Stock lookup
    st.subheader("Stock Lookup")
    col1, col2 = st.columns([1, 2])

    with col1:
        symbol = st.text_input("Enter Stock Symbol", placeholder="AAPL").upper()
        if symbol and st.button("Look Up"):
            with st.spinner(f"Fetching data for {symbol}..."):
                quote = orchestrator.market_data.get_quote(symbol)
                hist = orchestrator.market_data.get_historical(symbol, "3mo")

            if quote and quote.get("price"):
                change = quote.get("change_pct", 0) or 0
                st.metric(
                    f"{symbol} - {quote.get('name', symbol)}",
                    f"${quote['price']:.2f}",
                    delta=f"{change:+.2f}%"
                )

                if quote.get("pe_ratio"):
                    st.write(f"P/E Ratio: {quote['pe_ratio']:.1f}")
                if quote.get("market_cap"):
                    mc = quote["market_cap"]
                    mc_str = f"${mc/1e12:.1f}T" if mc > 1e12 else f"${mc/1e9:.1f}B"
                    st.write(f"Market Cap: {mc_str}")
                if quote.get("52w_high"):
                    st.write(f"52-Week Range: ${quote['52w_low']:.2f} - ${quote['52w_high']:.2f}")
            else:
                st.error(f"Could not find data for {symbol}")

            if hist is not None and not hist.empty:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=hist.index,
                    open=hist["Open"],
                    high=hist["High"],
                    low=hist["Low"],
                    close=hist["Close"],
                    name=symbol
                ))
                fig.update_layout(
                    title=f"{symbol} - 3 Month Price History",
                    xaxis_rangeslider_visible=False
                )
                with col2:
                    st.plotly_chart(fig, use_container_width=True)


def main():
    initialize_session()

    try:
        orchestrator = get_orchestrator()
    except Exception as e:
        st.error(f"Failed to initialize the assistant: {e}")
        st.info("Make sure ANTHROPIC_API_KEY is set in your .env file")
        return

    # Sync persisted risk profile into the current session state.
    try:
        profile = orchestrator.session_manager.get_profile(st.session_state.session_id)
        st.session_state.risk_profile = profile.risk_tolerance
    except Exception:
        pass

    st.title("📈 AI Finance Assistant")
    st.caption("Your personalized financial education companion | Educational purposes only, not financial advice")

    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 Portfolio", "📈 Market", "⚖️ Risk Profile"])

    with tab1:
        render_chat_tab(orchestrator)
    with tab2:
        render_portfolio_tab(orchestrator)
    with tab3:
        render_market_tab(orchestrator)
    with tab4:
        render_profile_tab(orchestrator)


if __name__ == "__main__":
    main()
