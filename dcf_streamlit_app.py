
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from dcf_valuation_tool import dcf_model, dcf_sensitivity_analysis, plot_heatmap

st.set_page_config(page_title="DCF Valuation Tool", layout="wide")
st.title("📊 DCF Valuation Web App")

# Upload Excel file
uploaded_file = st.file_uploader("Upload your financial Excel file", type=["xlsx"])

if uploaded_file:
    st.success("File uploaded successfully!")

    # Input parameters
    st.sidebar.header("Scenario Inputs")
    wacc = st.sidebar.slider("WACC (%)", 6.0, 12.0, 9.0) / 100
    terminal_growth = st.sidebar.slider("Terminal Growth (%)", 1.0, 4.0, 2.5) / 100

    # Growth rate sliders per scenario
    st.sidebar.subheader("FCF Growth Rates")
    growth_bear = st.sidebar.slider("Bear Case Growth (%)", 0.0, 10.0, 5.0) / 100
    growth_base = st.sidebar.slider("Base Case Growth (%)", 0.0, 15.0, 10.0) / 100
    growth_bull = st.sidebar.slider("Bull Case Growth (%)", 0.0, 20.0, 15.0) / 100

    # Add current stock price input
    current_price = st.sidebar.number_input("Current Stock Price ($)", min_value=0.0, value=150.0)

    scenario_inputs = {
        "Bear": {"growth": growth_bear, "wacc": wacc},
        "Base": {"growth": growth_base, "wacc": wacc},
        "Bull": {"growth": growth_bull, "wacc": wacc},
    }

    # Run DCF model
    results = dcf_model(uploaded_file, scenario_inputs, terminal_growth=terminal_growth)

    st.subheader("📈 Valuation Summary")
    st.dataframe(results["summary"], use_container_width=True)

    # Bar chart of share price scenarios
    st.subheader("📊 DCF Share Price by Scenario")
    fig, ax = plt.subplots()
    ax.bar(results["summary"]["Scenario"], results["summary"]["Share Price ($)"], color=["red", "orange", "green"])
    ax.axhline(y=current_price, color="blue", linestyle="--", label="Current Price")
    ax.set_ylabel("Estimated Share Price ($)")
    ax.set_title("DCF Valuation vs Current Price")
    ax.legend()
    st.pyplot(fig)

    # Interpretation based on base case
    base_valuation = results["summary"][results["summary"]["Scenario"] == "Base"]["Share Price ($)"].values[0]
    price_diff = current_price - base_valuation
    price_diff_pct = (price_diff / base_valuation) * 100

    st.subheader("📌 Valuation Insight")
    if price_diff_pct < -10:
        st.success(f"✅ The stock appears **undervalued** by {abs(price_diff_pct):.1f}% vs Base Case DCF (${base_valuation:.2f}).")
    elif price_diff_pct > 10:
        st.error(f"🚨 The stock appears **overvalued** by {abs(price_diff_pct):.1f}% vs Base Case DCF (${base_valuation:.2f}).")
    else:
        st.warning(f"⚖️ The stock appears **fairly valued**, within ±10% of Base Case DCF (${base_valuation:.2f}).")

    # Discounted cash flows
    st.subheader("🧮 Discounted Cash Flows")
    st.dataframe(results["dcf_table"], use_container_width=True)

    # Sensitivity analysis (Base case)
    st.subheader("🎯 Sensitivity Analysis (Base Case)")
    sensitivity_df = dcf_sensitivity_analysis(
        base_fcf=results["inputs"]["Base FCF"],
        shares=results["inputs"]["Shares"],
        net_debt=results["inputs"]["Net Debt"],
        growth_rate=scenario_inputs["Base"]["growth"]
    )

    st.dataframe(sensitivity_df, use_container_width=True)
    plot_heatmap(sensitivity_df, title="Base Case Sensitivity Heatmap")
