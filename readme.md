# E-Pass Work Expense Analyzer

A Python tool that analyzes E-Pass toll transactions and separates work-related (expensable) transactions from personal ones.

## Features

- Identifies expensable transactions based on:
  - Workdays (Monday to Friday)
  - Work hours (8:00 AM to 8:00 PM)
  - Excludes holidays and Christmas
- Creates a filtered CSV file containing only expensable transactions
- Adds a total sum row at the bottom of the expensable transactions file
- Provides detailed transaction reports including:
  - Daily summaries
  - Work week expenses
  - Non-expensable transaction details

## Requirements

- Python 3.x
- pandas
- datetime
- calendar

## Usage

1. Place your E-Pass CSV file in the same directory as the script
2. Run the script:
   ```bash
   python epass_work_expense_analyzer.py
   ```
3. Select your CSV file from the list of available files
4. The script will generate:
   - A detailed analysis in the console
   - A new CSV file (prefixed with "expensable_") containing only work-related transactions

## Output Files

The script generates a new CSV file named `expensable_[original_filename].csv` containing:
- Only work-related transactions
- A total sum row at the bottom

## Supported Holidays

The script automatically excludes the following US Federal Holidays:
- New Year's Day
- Martin Luther King Jr. Day
- Presidents Day
- Memorial Day
- Juneteenth
- Independence Day
- Labor Day
- Columbus Day
- Veterans Day
- Thanksgiving Day
- Christmas Day