#!/usr/bin/env python3

# Forked from: https://github.com/SudheerNotes/cams2csv

"""
cams2xirr.py

Usage:
    python cams2xirr.py --pdf path/to/your.pdf --password your_password
"""


import re
import pdfplumber
import pandas as pd
from scipy.optimize import newton


def xnpv(rate, values, dates):
    """
    Calculate the Net Present Value for irregular cash flows.
    """
    if rate <= -1.0:
        return float('inf')
    d0 = dates.min()
    return sum(val / (1 + rate) ** ((date - d0).days / 365.0) for val, date in zip(values, dates))


def xirr(values, dates):
    """
    Calculate the Internal Rate of Return for irregular cash flows.
    """
    return newton(lambda r: xnpv(r, values, dates), 0.1)


def extract_text_from_pdf(file_path, password):
    """
    Extract all text from a password-protected PDF using pdfplumber.
    """
    final_text = ""
    with pdfplumber.open(file_path, password=password) as pdf:
        for page in pdf.pages:
            final_text += "\n" + page.extract_text()
    return final_text


def get_market_value(text):
    """
    Extracts the market value of all mutual funds from the provided text.
    
    Returns:
        pd.DataFrame with columns: Fund_name, Date, Market_value
    """
    fund_name = re.compile(r"^([a-z0-9]{3,}+)-(.*?FUND)", re.IGNORECASE)
    market_val = re.compile(r"Market Value on (\d{2}-[A-Za-z]{3}-\d{4}): INR ([\d,]+\.\d{2})")
    line_items = []
    fun_name = val = dt = None

    for line in text.splitlines():
        match = fund_name.search(line)
        if match:
            fun_name = match.group(0)

        match = market_val.search(line)
        if match:
            dt, val = match.group(1), match.group(2)
            line_items.append([fun_name, dt, val])

    df = pd.DataFrame(line_items, columns=["Fund_name", "Date", "Market_value"])
    df['Market_value'] = df['Market_value'].str.replace(',', '', regex=False).astype(float)
    df['Date'] = pd.to_datetime(df['Date'], format="%d-%b-%Y")
    return df


def clean_column(col):
    """
    Clean numerical columns by removing commas and handling negative values in parentheses.
    """
    col.replace(r",", "", regex=True, inplace=True)
    col.replace(r"\(", "-", regex=True, inplace=True)
    col.replace(r"\)", "", regex=True, inplace=True)
    return col


def extract_transactions(text):
    """
    Extracts transaction details from the given document text.

    Returns:
        pd.DataFrame with transaction history including Folio, ISIN, Amount, Units, etc.
    """
    folio_pat = re.compile(r"(?:^Folio No:)(\s\d+)(?:\s.*)", re.IGNORECASE)
    fund_name = re.compile(r"^([a-z0-9]{3,}+)-(.*?FUND)", re.IGNORECASE)
    isin_num = re.compile(r"(.*)(ISIN.+?)(.*?)(?:Reg|\()", re.IGNORECASE)
    trans_details = re.compile(
        r"(^\d{2}-\w{3}-\d{4})(\s.+?\s(?=[\d(]))([\d\(]+[,.]\d+[.\d\)]+)"
        r"(\s[\d\(\,\.\)]+)(\s[\d\,\.]+)(\s[\d,\.]+)"
    )

    line_items = []
    folio = fun_name = isin = None

    for line in text.splitlines():
        if fund_name.match(line):
            fun_name = fund_name.match(line).group(0)

        if folio_pat.match(line):
            folio = folio_pat.match(line).group(1)

        if isin_num.match(line):
            isin = isin_num.match(line).group(3)

        trn_txt = trans_details.search(line)
        if trn_txt:
            date, description, amount, units, price, unit_bal = [
                trn_txt.group(i).strip() for i in range(1, 7)
            ]
            line_items.append([
                folio, isin, fun_name, date, description,
                amount, units, price, unit_bal
            ])

    df = pd.DataFrame(line_items, columns=[
        "Folio", "ISIN", "Fund_name", "Date", "Description",
        "Amount", "Units", "Price", "Unit_balance"
    ])

    for col in ["Amount", "Units", "Price", "Unit_balance"]:
        clean_column(df[col])
        df[col] = df[col].astype(float)

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compute XIRR from CAMS PDF")
    parser.add_argument("--pdf", help="Path to CAMS PDF", required=True)
    parser.add_argument("--password", help="PDF password", required=True)
    args = parser.parse_args()

    # Extract text and parse
    text = extract_text_from_pdf(args.pdf, args.password)

    # Get market values
    df_market_val = get_market_value(text)
    total_market_value = df_market_val['Market_value'].sum()

    # Get transactions
    df = extract_transactions(text)
    df['Date'] = pd.to_datetime(df['Date'], format="%d-%b-%Y")
    df = df.sort_values(by='Date').reset_index(drop=True)

    # Compute total XIRR
    df_xirr = df[['Date', 'Amount']].copy()
    df_xirr['Amount'] = -df_xirr['Amount']  # Outflows = negative, inflows = positive

    today = df_market_val['Date'].iloc[0]
    final_row = pd.DataFrame({'Date': [today], 'Amount': [total_market_value]})
    df_xirr = pd.concat([df_xirr, final_row], ignore_index=True)

    total_xirr = xirr(df_xirr['Amount'], df_xirr['Date']) * 100

    print(f"\nTotal Market Value: INR {total_market_value:,.2f}")
    print(f"Total XIRR: {total_xirr:.2f}%\n")

    # Fund-wise XIRR
    fundwise_xirr = []
    for fund in df['Fund_name'].unique():
        df_fund = df[df["Fund_name"] == fund]
        df_xirr = df_fund[['Date', 'Amount']].copy()
        df_xirr['Amount'] = -df_xirr['Amount']

        mkt_val = df_market_val[df_market_val['Fund_name'] == fund]['Market_value'].iloc[0]
        dt = df_market_val[df_market_val['Fund_name'] == fund]['Date'].iloc[0]

        final_row = pd.DataFrame({'Date': [dt], 'Amount': [mkt_val]})
        df_xirr = pd.concat([df_xirr, final_row], ignore_index=True)

        fund_xirr = xirr(df_xirr['Amount'], df_xirr['Date']) * 100
        fundwise_xirr.append(fund_xirr)

    df_market_val['XIRR (%)'] = [round(x, 2) for x in fundwise_xirr]

    print("Fund-wise XIRR:\n")
    print(df_market_val[['Fund_name', 'Market_value', 'XIRR (%)']].to_string(index=False))
