import pandas as pd
from datetime import datetime, timedelta
import calendar
import os
from io import StringIO
import glob

def get_us_holidays(year):
    """Generate US Federal Holidays for a given year with their names."""
    holidays = {
        f"{year}-01-01": "New Year's Day",
        f"{year}-01-{1 + (20 - datetime(year, 1, 1).weekday()) % 7}": "Martin Luther King Jr. Day",
        f"{year}-02-{1 + (20 - datetime(year, 2, 1).weekday()) % 7}": "Presidents Day",
        f"{year}-05-{1 + (31 - datetime(year, 5, 31).weekday())}": "Memorial Day",
        f"{year}-06-19": "Juneteenth",
        f"{year}-07-04": "Independence Day",
        f"{year}-09-{1 + (7 - datetime(year, 9, 1).weekday()) % 7}": "Labor Day",
        f"{year}-10-{1 + (13 - datetime(year, 10, 1).weekday()) % 7}": "Columbus Day",
        f"{year}-11-11": "Veterans Day",
        f"{year}-11-{22 + (3 - datetime(year, 11, 22).weekday()) % 7}": "Thanksgiving Day",
        f"{year}-12-25": "Christmas Day"
    }
    # Convert to series for easier lookup
    return pd.Series(holidays)

def analyze_tool_expenses(file_path):
    try:
        df = read_csv(file_path)
        if df is None:
            return 0
            
        # Add day names and weekday indicator
        df['weekday'] = df['Date'].dt.dayofweek  # Monday=0, Sunday=6
        df['day_name'] = df['Date'].dt.day_name()
        
        # Get the year from the data
        year = df['Date'].dt.year.iloc[0]
        
        # Get holidays for the year in the data
        holiday_names = get_us_holidays(year)
        
        # Convert dates to string format for comparison
        df['date_str'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # Debug print to verify holiday dates
        print("\nDebug - Holiday dates:")
        for date, name in holiday_names.items():
            print(f"{date}: {name}")
        
        # Identify Christmas and holidays
        is_christmas = (df['Date'].dt.month == 12) & (df['Date'].dt.day == 25)
        is_holiday = df['date_str'].isin(holiday_names.index)
        
        # Debug print to verify holiday detection
        print("\nDebug - Detected holidays in data:")
        holiday_dates = df[is_holiday]['date_str'].unique()
        for date in holiday_dates:
            print(f"Found holiday: {date} - {holiday_names.get(date, 'Unknown')}")
        
        # Separate transactions into expensable and non-expensable
        work_days = df[
            (df['weekday'].between(0, 4)) &  # Monday to Friday
            (~is_christmas) &  # not Christmas
            (~is_holiday)  # not a bank holiday
        ]
        work_hours = work_days[work_days['Time'].between('08:00:00', '20:00:00')]
        
        # Calculate expensable_days before using it
        expensable_days = len(work_hours['Date'].dt.date.unique())
        
        # Non-expensable transactions
        non_expensable = df[
            (df['weekday'].isin([5, 6]) |  # Weekend
             is_christmas |  # Christmas
             is_holiday |  # Bank holiday
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
            try:
                holiday_marker = ""
                # Convert the datetime to string in the correct format
                date_str = row['Date'].strftime('%Y-%m-%d')
                
                # Check if this exact date matches any holiday
                if date_str in holiday_names.index:
                    holiday_marker = f" [{holiday_names[date_str]}]"
                elif row['Date'].month == 12 and row['Date'].day == 25:
                    holiday_marker = " [Christmas Day]"
                    
                print(f"{row['day_name']}, {date_str}, {row['Time']}: ${row['Amount']:.2f} - {row['Location']}{holiday_marker}")
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
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

def get_csv_file():
    # Find all CSV files in the current directory
    csv_files = glob.glob('*.csv')
    
    if not csv_files:
        print("No CSV files found in the current directory.")
        return None
    
    # List all found CSV files
    print("\nFound the following CSV files:")
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")
    
    # Ask user to select a file
    while True:
        try:
            choice = input("\nEnter the number of the file you want to process (or 'q' to quit): ")
            if choice.lower() == 'q':
                return None
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(csv_files):
                selected_file = csv_files[choice_idx]
                confirm = input(f"\nYou selected: {selected_file}\nProcess this file? (y/n): ")
                if confirm.lower() == 'y':
                    return selected_file
                print("Let's try again.")
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

if __name__ == "__main__":
    file_name = get_csv_file()
    if file_name:
        analyze_tool_expenses(file_name)
    else:
        print("No file selected. Exiting.")