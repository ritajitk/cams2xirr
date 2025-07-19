# CAMS pdf to XIRR Calculator

This Python script extracts mutual fund transaction data from password-protected CAMS PDF statements and calculates the XIRR (Extended Internal Rate of Return), both for the overall portfolio and individual funds.

It parses transaction history and market values directly from the PDF, handles irregular cash flows, and provides a clear summary of investment performance.

---

## Features

- Works with CAMS-consolidated mutual fund statements (PDF)
- Supports password-protected PDFs
- Extracts transaction history and current market values
- Calculates:
  - Total portfolio XIRR
  - Fund-wise XIRR
- Outputs a readable summary to the terminal

---

## Dependencies
- pdfplumber
- pandas
- scipy

---
## Usage
   First get a CAMS pdf from [Here](https://www.camsonline.com/Investors/Statements/Consolidated-Account-Statement).
	python cams_xirr_calculator.py --pdf path/to/statement.pdf --password your_password

---

## Example Output

Total Market Value: INR 987,321.00  
Total XIRR: 7.45%

Fund-wise XIRR:

           Fund_name              Market_value  XIRR (%)
		Balanced Growth Fund        102345.67      5.32
		Ultra Short Term Fund        48765.10      7.88
		Equity Opportunities Fund   123456.78      3.47
		Liquid Plus Fund             59876.32      9.12
		Short Duration Debt Fund    278934.11      6.84
		Money Market Fund           218765.50      7.30
		Index Equity Fund           255178.52      8.05

---

## Disclaimer

This script is provided for educational and personal use only.

Please verify the results independently. The script assumes a specific format used by CAMS in its PDF statements and may not work correctly if the structure of the PDF changes or differs.

Use at your own risk. The author takes no responsibility for financial decisions made based on this tool.

