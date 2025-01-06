import pandas as pd
from datetime import datetime, timedelta
import calendar
import os
from io import StringIO

def analyze_tool_expenses(file_path):
    try:
        df = read_csv(file_path)
        if df is None:
            return 0
            
        # Add day names and weekday indicator
        df['weekday'] = df['Date'].dt.dayofweek  # Monday=0, Sunday=6
        df['day_name'] = df['Date'].dt.day_name()
        
        # Identify Christmas
        is_christmas = (df['Date'].dt.month == 12) & (df['Date'].dt.day == 25)
        
        # Separate transactions into expensable and non-expensable
        work_days = df[df['weekday'].between(0, 4) & ~is_christmas]  # Monday to Friday, not Christmas
        work_hours = work_days[work_days['Time'].between('08:00:00', '20:00:00')]
        
        # Get unique days with expensable transactions
        expensable_days = work_hours['Date'].nunique()
        
        # Non-expensable transactions (weekends, holidays, or outside work hours)
        non_expensable = df[
            (df['weekday'].isin([5, 6]) |  # Weekend
             is_christmas |  # Christmas
             ~df['Time'].between('08:00:00', '20:00:00'))  # Outside work hours
        ]
        
        # Get month and year from filename
        month_year = os.path.splitext(os.path.basename(file_path))[0]
        month, year = month_year.split('_')
        month_name = calendar.month_name[int(month)]
        
        # Print results
        print(f"\nToll Expense Report for {month_name} {year}")
        print("=" * 60)
        
        # List all work week transactions
        print("EXPENSABLE TRANSACTIONS (Workdays 8AM-8PM):")
        print("-" * 60)
        for _, row in work_hours.sort_values(['Date', 'Time']).iterrows():
            print(f"{row['day_name']}, {row['Date'].strftime('%Y-%m-%d')}, {row['Time']}: ${row['Amount']:.2f} - {row['Location']}")
        
        # Daily Summary for work days
        print("\nEXPENSABLE DAILY SUMMARY:")
        print("-" * 60)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        daily_totals = work_hours.groupby('day_name')['Amount'].agg(['sum', 'count']).reindex(day_order)
        
        total_work_amount = 0
        
        for day, row in daily_totals.iterrows():
            if pd.notna(row['sum']):
                total_work_amount += row['sum']
                print(f"{day}: ${row['sum']:.2f} ({row['count']} transactions)")
            else:
                print(f"{day}: $0.00 (0 transactions)")
        
        # Work week summary
        avg_cost_per_day = total_work_amount / expensable_days if expensable_days > 0 else 0
        print("\nEXPENSABLE SUMMARY:")
        print("-" * 60)
        print(f"Number of days with expensable transactions: {expensable_days}")
        print(f"Total work week expenses: ${total_work_amount:.2f}")
        print(f"Average cost per day: ${avg_cost_per_day:.2f}")
        
        # Non-expensable transactions summary
        print("\nNON-EXPENSABLE TRANSACTIONS:")
        print("=" * 60)
        print("Transactions outside work hours, weekends, and holidays:")
        for _, row in non_expensable.sort_values(['Date', 'Time']).iterrows():
            print(f"{row['day_name']}, {row['Date'].strftime('%Y-%m-%d')}, {row['Time']}: ${row['Amount']:.2f} - {row['Location']}")
        
        # Non-expensable summary
        non_exp_total = non_expensable['Amount'].sum()
        print("\nNON-EXPENSABLE SUMMARY:")
        print("-" * 60)
        print(f"Total non-expensable transactions: {len(non_expensable)}")
        print(f"Total non-expensable amount: ${non_exp_total:.2f}")
        print("=" * 60)
        
        return total_work_amount
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        print("Debug info:")
        print(f"File exists: {os.path.exists(file_path)}")
        return 0

def get_previous_month_file():
    current_date = datetime.now()
    first_day = current_date.replace(day=1)
    last_month = first_day - timedelta(days=1)
    return f"{last_month.month:02d}_{last_month.year}.csv"

def clean_date(date_str):
    if date_str == "---------":
        return None
    return date_str.strip('" ')  # Remove quotes and spaces

def read_csv(file_path):
    try:
        print("\nDebug: Starting file read")
        # Read the entire file as text first
        with open(file_path, 'r') as file:
            lines = file.readlines()
        print(f"Debug: Read {len(lines)} lines from file")
        
        # Find the exact header line
        header_line = "Transponder Number,Date,Time,Posting Date,Location,Amount,Toll Type"
        header_index = next(i for i, line in enumerate(lines) if header_line in line)
        print(f"Debug: Found header at line {header_index}")
        
        # Create a new StringIO with just the header and data
        data_section = StringIO(header_line + '\n' + ''.join(lines[header_index + 1:]))
        
        # Read the CSV file, explicitly telling pandas not to use the first column as index
        df = pd.read_csv(data_section, index_col=False)
        print(f"Debug: Initial DataFrame size: {len(df)}")
        
        print("\nDebug: Raw columns:")
        print(df.columns.tolist())
        print("\nDebug: Raw data sample:")
        print(df.head())
        
        # Clean up the data first - before any filtering
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip('" ')
        
        # Filter out rows that only contain dashes
        valid_rows = ~(
            (df['Date'].str.contains('^-+$', regex=True)) |
            (df['Time'].str.contains('^-+$', regex=True)) |
            (df['Amount'].str.contains('^-+$', regex=True))
        )
        df = df[valid_rows]
        print(f"Debug: After filtering dashes: {len(df)}")
        
        # Convert Amount to numeric
        df['Amount'] = pd.to_numeric(df['Amount'])
        print(f"Debug: After amount conversion: {len(df)}")
        
        # Convert Date to datetime
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y')
        
        # Time is already in HH:MM:SS format
        df['Time'] = df['Time'].str.strip()
        
        print(f"Debug: Final DataFrame size: {len(df)}")
        print("\nDebug: Sample of processed data:")
        print(df[['Date', 'Time', 'Amount']].head())
        
        return df
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        print("Debug info:")
        print(f"File exists: {os.path.exists(file_path)}")
        try:
            print("\nDebug: Raw data sample at error:")
            print(df.head())
        except:
            pass
        return None

if __name__ == "__main__":
    file_name = get_previous_month_file()
    analyze_tool_expenses(file_name)