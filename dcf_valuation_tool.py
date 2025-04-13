
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_financial_data(file_path):
    df = pd.read_excel(file_path, sheet_name="Sheet1")
    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
    return df

def extract_value(df, label):
    row = df[df.iloc[:, 0].str.strip() == label].iloc[0]
    values = pd.to_numeric(row[1:], errors='coerce')
    return values.dropna().iloc[0] if not values.dropna().empty else None

def extract_base_fcf(df):
    row = df[df.iloc[:, 0].str.contains("Free Cash Flow", case=False, na=False)].iloc[0]
    values = pd.to_numeric(row[1:], errors='coerce').dropna()
    return values.iloc[0]

def project_fcf(base_fcf, growth_rate, years=5):
    return [round(base_fcf * ((1 + growth_rate) ** i), 2) for i in range(1, years + 1)]

def calculate_terminal_value(last_fcf, growth_rate, wacc, terminal_growth):
    return (last_fcf * (1 + growth_rate)) / (wacc - terminal_growth)

def discount_cash_flows(fcfs, terminal_value, wacc, years=5):
    discounted = [fcf / ((1 + wacc) ** (i + 1)) for i, fcf in enumerate(fcfs)]
    terminal_pv = terminal_value / ((1 + wacc) ** years)
    return discounted + [round(terminal_pv, 2)]

def calculate_valuation(discounted_fcfs, net_debt, shares_outstanding):
    enterprise_value = sum(discounted_fcfs)
    equity_value = enterprise_value - net_debt
    share_price = equity_value / shares_outstanding
    return {
        "Enterprise Value (B)": round(enterprise_value / 1000, 2),
        "Equity Value (B)": round(equity_value / 1000, 2),
        "Share Price ($)": round(share_price, 2)
    }

def dcf_model(file_path, scenario_inputs, terminal_growth=0.025):
    df = load_financial_data(file_path)
    base_fcf = extract_base_fcf(df)
    cash = extract_value(df, "Cash \u0026 Short Term Investments")
    debt = extract_value(df, "Long Term Debt")
    shares = extract_value(df, "Shares Outstanding")
    net_debt = debt - cash

    results = {}
    fcf_tables = {}
    for scenario, inputs in scenario_inputs.items():
        growth = inputs["growth"]
        wacc = inputs["wacc"]
        fcfs = project_fcf(base_fcf, growth)
        terminal_value = calculate_terminal_value(fcfs[-1], growth, wacc, terminal_growth)
        discounted = discount_cash_flows(fcfs, terminal_value, wacc)
        valuation = calculate_valuation(discounted, net_debt, shares)
        results[scenario] = valuation
        fcf_tables[scenario] = discounted

    return {
        "summary": pd.DataFrame(results).T.reset_index(names="Scenario"),
        "dcf_table": pd.DataFrame(fcf_tables),
        "inputs": {"Base FCF": base_fcf, "Shares": shares, "Net Debt": net_debt}
    }

def dcf_sensitivity_analysis(base_fcf, shares, net_debt, growth_rate, 
                             wacc_range=np.arange(0.07, 0.11, 0.005), 
                             tg_range=np.arange(0.02, 0.035, 0.0025), years=5):
    fcf_list = [base_fcf * ((1 + growth_rate) ** i) for i in range(1, years + 1)]
    table = pd.DataFrame(index=[f"{round(g*100,2)}%" for g in tg_range],
                         columns=[f"{round(w*100,2)}%" for w in wacc_range])
    for g in tg_range:
        for r in wacc_range:
            fcf_2026 = fcf_list[-1]
            tv = (fcf_2026 * (1 + growth_rate)) / (r - g)
            tv_pv = tv / ((1 + r) ** years)
            discounted_fcfs = [fcf / ((1 + r) ** (i + 1)) for i, fcf in enumerate(fcf_list)]
            ev = sum(discounted_fcfs) + tv_pv
            equity = ev - net_debt
            price = equity / shares
            table.loc[f"{round(g*100,2)}%", f"{round(r*100,2)}%"] = round(price, 2)
    return table

def plot_heatmap(sensitivity_table, title="DCF Sensitivity Analysis"):
    plt.figure(figsize=(10, 6))
    plt.title(title)
    plt.xlabel("WACC")
    plt.ylabel("Terminal Growth Rate")
    plt.imshow(sensitivity_table.astype(float), cmap="YlGnBu", aspect="auto")
    plt.xticks(ticks=np.arange(len(sensitivity_table.columns)), labels=sensitivity_table.columns)
    plt.yticks(ticks=np.arange(len(sensitivity_table.index)), labels=sensitivity_table.index)
    plt.colorbar(label="Share Price ($)")
    plt.tight_layout()
    plt.show()
