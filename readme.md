# E-Pass Work Expense Analyzer

A Python tool to analyze E-Pass toll transactions and categorize them as expensable (work-related) or non-expensable based on specific criteria.

## Features

- Analyzes E-Pass toll transactions from CSV files
- Categorizes transactions as expensable or non-expensable based on:
  - Work days (Monday-Friday)
  - Work hours (8 AM - 8 PM)
  - Excludes weekends
  - Excludes US Federal Holidays
  - Excludes Christmas Day
- Provides detailed transaction summaries
- Automatically detects and marks holiday transactions
- Calculates daily and total expenses

## US Federal Holidays Handled

The tool automatically excludes the following US Federal Holidays from expensable transactions:
- New Year's Day (January 1)
- Martin Luther King Jr. Day (3rd Monday in January)
- Presidents Day (3rd Monday in February)
- Memorial Day (Last Monday in May)
- Juneteenth (June 19)
- Independence Day (July 4)
- Labor Day (1st Monday in September)
- Columbus Day (2nd Monday in October)
- Veterans Day (November 11)
- Thanksgiving Day (4th Thursday in November)
- Christmas Day (December 25)

## Usage

1. Place your E-Pass CSV file in the same directory as the script
2. Run the script:
   ```
   python epass_work_expense_analyzer.py
   ```
3. Select your CSV file from the list presented
4. Review the generated expense report

## Output Format

The tool provides:
- List of expensable transactions with dates and amounts
- Daily summary of expensable transactions
- Total expensable amount and average cost per day
- List of non-expensable transactions (including holidays)
- Total non-expensable amount

## Requirements

- Python 3.x
- pandas
- datetime

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/epass-work-expense-analyzer.git
   cd epass-work-expense-analyzer
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Note

CSV files are ignored by git to protect sensitive transaction data.