import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Alpha-Invest Health Checker", layout="wide")
st.title("📈 Indian Portfolio Health Checker")

# 2. Initialize Session State for the portfolio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- SIDEBAR INPUTS ---
st.sidebar.header("Add Stock to Portfolio")
ticker_input = st.sidebar.text_input("Ticker (e.g., ITC.NS, RELIANCE.NS)").upper()
qty_input = st.sidebar.number_input("Quantity", min_value=1, step=1)
avg_price_input = st.sidebar.number_input("Avg Purchase Price (₹)", min_value=0.0, step=0.1)

if st.sidebar.button("Add to Portfolio"):
    if ticker_input:
        with st.spinner(f"Analyzing {ticker_input}..."):  # Shows a loading spinner
            try:
                stock = yf.Ticker(ticker_input)
                info = stock.info

                # 1. Fetch Price
                current_price = stock.history(period="1d")['Close'].iloc[-1]

                # 2. Fetch Health Metrics (Handling missing data with .get)
                debt_equity = info.get('debtToEquity', 0)
                # Note: yfinance returns debtToEquity as a whole number (e.g., 80.0 means 0.8)
                de_ratio = debt_equity / 100 if debt_equity else 0

                roe = info.get('returnOnEquity', 0)
                beta = info.get('beta', 1.0)

                # 3. Save to session state with Health Data
                new_entry = {
                    "Ticker": ticker_input,
                    "Qty": qty_input,
                    "Buy Price": avg_price_input,
                    "Current Price": round(current_price, 2),
                    "Debt/Equity": round(de_ratio, 2),
                    "ROE (%)": round(roe * 100, 2) if roe else 0,
                    "Beta": beta
                      # Default to 1.0 if Beta isn't found
                # ... in your new_entry dictionary:

                }

                st.session_state.portfolio.append(new_entry)
                st.sidebar.success(f"Added {ticker_input}!")

            except Exception as e:
                st.sidebar.error(f"Error fetching data: {e}")

# --- MAIN DASHBOARD ---
if st.session_state.portfolio:
    st.subheader("Your Current Holdings")

    # Convert list of dicts to a Pandas DataFrame for easy viewing
    df = pd.DataFrame(st.session_state.portfolio)

    # Calculate basic metrics
    df['Invested Value'] = df['Qty'] * df['Buy Price']
    df['Current Value'] = df['Qty'] * df['Current Price']
    df['P&L'] = df['Current Value'] - df['Invested Value']

    # Display the table
    st.table(df)

    st.subheader("Financial Health Analysis")

    for item in st.session_state.portfolio:
        col_a, col_b, col_c = st.columns([1, 2, 2])
        col_a.write(f"**{item['Ticker']}**")

        # Debt Check
        if item['Debt/Equity'] < 1:
            col_b.success(f"Safe Debt: {item['Debt/Equity']}")
        else:
            col_b.warning(f"High Debt: {item['Debt/Equity']}")

        # Profitability Check (ROE)
        if item['ROE (%)'] > 15:
            col_c.success(f"Strong ROE: {item['ROE (%)']}%")
        else:
            col_c.info(f"Modest ROE: {item['ROE (%)']}%")

    # Summary Metrics
    total_invested = df['Invested Value'].sum()
    total_current = df['Current Value'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Invested", f"₹{total_invested:,.2f}")
    col2.metric("Current Value", f"₹{total_current:,.2f}")
    col3.metric("Total P&L", f"₹{total_current - total_invested:,.2f}",
                delta=f"{((total_current - total_invested) / total_invested) * 100:.2f}%")

else:
    st.info("Your portfolio is empty. Add stocks using the sidebar to begin analysis.")

st.divider()
st.header("📉 Portfolio Stress Test (Market Crash Simulator)")

# 1. User Input: How much does the Nifty 50 drop?
crash_percent = st.slider("Simulated Nifty 50 Drop (%)", 0, 50, 20)

if st.session_state.portfolio:
    df_stress = pd.DataFrame(st.session_state.portfolio)

    # 2. Calculate the "Stressed" Price
    # Formula: Current Price * (1 - (Crash% * Beta))
    df_stress['Stressed Price'] = df_stress['Current Price'] * (1 - (crash_percent / 100 * df_stress['Beta']))
    df_stress['Value Loss'] = (df_stress['Current Price'] - df_stress['Stressed Price']) * df_stress['Qty']

    # 3. Visualization
    total_loss = df_stress['Value Loss'].sum()
    st.warning(
        f"If the Nifty 50 drops by {crash_percent}%, your portfolio could lose approximately **₹{total_loss:,.2f}**")

    # Bar Chart of Loss per Ticker
    st.bar_chart(df_stress.set_index('Ticker')['Value Loss'])

    # Show the data
    st.dataframe(df_stress[['Ticker', 'Beta', 'Current Price', 'Stressed Price', 'Value Loss']])