import pandas as pd
from datetime import datetime, timedelta
import calendar
import os
from io import StringIO
import glob
import re

def filter_receipt_file(input_file_path):
    """
    Filter a receipt file to keep only Account Activity and work-hour vehicle activities.
    Applies the same business logic as expensable analysis: weekdays 7:30AM-8PM, excluding holidays.
    Creates a new filtered file with the same name but prefixed with 'receipt_'.
    Adds a total row for the vehicle activities.
    """
    try:
        print(f"\nFiltering receipt file: {input_file_path}")
        
        # Read the entire file as text
        with open(input_file_path, 'r') as file:
            lines = file.readlines()
        
        # Find Account Activity section
        account_start = None
        vehicle_start = None
        
        for i, line in enumerate(lines):
            if line.strip() == "Account Activity":
                account_start = i
            elif line.strip() == "Vehicle Activity":
                vehicle_start = i
                break
        
        if account_start is None or vehicle_start is None:
            print("Could not find Account Activity or Vehicle Activity sections")
            return None
        
        # Extract Account Activity section (including header and data)
        account_lines = []
        for i in range(account_start, vehicle_start):
            account_lines.append(lines[i])
        
        # Extract Vehicle Activity header
        vehicle_header = lines[vehicle_start]
        vehicle_header_line = lines[vehicle_start + 1]  # The actual CSV header
        
        # Get holidays for filtering
        from datetime import datetime
        year = 2025  # Default year, will be updated from data
        holiday_names = get_us_holidays(year)
        
        # Extract and filter vehicle activities using business logic
        filtered_vehicle_lines = [vehicle_header, vehicle_header_line]
        total_amount = 0.0
        
        for i in range(vehicle_start + 2, len(lines)):
            line = lines[i].strip()
            if not line:  # Empty line
                continue
            
            # Only process lines that start with transponder number
            if not line.startswith('"3857335"'):
                continue
            
            try:
                # Parse the line to extract date, time, and amount
                parts = line.split(',')
                if len(parts) < 6:
                    continue
                
                # Extract date and time
                date_str = parts[1].strip('"')
                time_str = parts[2].strip('"')
                amount_str = parts[5].strip('"')
                
                # Parse date and time
                date_obj = pd.to_datetime(date_str, format='%d-%b-%y')
                time_obj = pd.to_datetime(time_str, format='%H:%M:%S').time()
                
                # Check if it's a workday (Monday=0, Sunday=6)
                weekday = date_obj.weekday()
                is_weekday = weekday < 5  # Monday to Friday
                
                # Check if it's during work hours (7:30 AM to 8:00 PM)
                from datetime import time
                is_work_hours = time(7, 30) <= time_obj <= time(20, 0)
                
                # Check if it's a holiday
                date_str_for_holiday = date_obj.strftime('%Y-%m-%d')
                is_holiday = date_str_for_holiday in holiday_names.index
                
                # Check if it's Christmas
                is_christmas = (date_obj.month == 12) and (date_obj.day == 25)
                
                # Include only workday, work-hour, non-holiday transactions
                if is_weekday and is_work_hours and not is_holiday and not is_christmas:
                    filtered_vehicle_lines.append(lines[i])
                    amount = float(amount_str)
                    total_amount += amount
                    
            except (ValueError, IndexError, pd.errors.ParserError):
                # If we can't parse the line, skip it
                continue
        
        # Add total row
        total_line = f'"TOTAL","","","","TOTAL WORK-HOUR VEHICLE ACTIVITIES","{total_amount:.2f}",""\n'
        filtered_vehicle_lines.append(total_line)
        
        # Create the filtered content
        filtered_content = ''.join(account_lines) + '\n' + ''.join(filtered_vehicle_lines)
        
        # Save the filtered file
        output_file = f"receipt_{os.path.basename(input_file_path)}"
        with open(output_file, 'w') as file:
            file.write(filtered_content)
        
        print(f"Filtered receipt saved to: {output_file}")
        print(f"Total work-hour vehicle activities amount: ${total_amount:.2f}")
        return output_file
        
    except Exception as e:
        print(f"Error filtering receipt file: {str(e)}")
        return None

def add_total_to_receipt_file(receipt_file_path):
    """
    Add a total row to an existing receipt file.
    """
    try:
        print(f"\nAdding total to receipt file: {receipt_file_path}")
        
        # Read the entire file as text
        with open(receipt_file_path, 'r') as file:
            lines = file.readlines()
        
        # Find Vehicle Activity section
        vehicle_start = None
        for i, line in enumerate(lines):
            if line.strip() == "Vehicle Activity":
                vehicle_start = i
                break
        
        if vehicle_start is None:
            print("Could not find Vehicle Activity section")
            return None
        
        # Check if total already exists
        has_total = any('TOTAL VEHICLE ACTIVITIES' in line for line in lines)
        if has_total:
            print("Total already exists in the file")
            return receipt_file_path
        
        # Calculate total from existing vehicle activities
        total_amount = 0.0
        for i in range(vehicle_start + 2, len(lines)):
            line = lines[i].strip()
            if not line or 'TOTAL' in line:
                continue
            
            # Include ALL vehicle activities (both with and without "E" in Toll Type)
            if line.startswith('"3857335"'):
                try:
                    # Split by comma and get the amount (second to last field)
                    parts = line.split(',')
                    if len(parts) >= 6:  # Ensure we have enough parts
                        amount_str = parts[5].strip('"')
                        amount = float(amount_str)
                        total_amount += amount
                except (ValueError, IndexError):
                    # If we can't parse the amount, continue without adding to total
                    pass
        
        # Add total row at the end
        total_line = f'"TOTAL","","","","TOTAL VEHICLE ACTIVITIES","{total_amount:.2f}",""\n'
        
        # Write back to file
        with open(receipt_file_path, 'w') as file:
            file.writelines(lines)
            file.write(total_line)
        
        print(f"Total added to receipt file: ${total_amount:.2f}")
        return receipt_file_path
        
    except Exception as e:
        print(f"Error adding total to receipt file: {str(e)}")
        return None

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
        from datetime import time
        work_hours = work_days[work_days['Time'].between(time(7, 30), time(20, 0))]
        
        
        # Calculate total amount
        total_amount = work_hours['Amount'].sum()
        
        # Create a total row
        total_row = pd.DataFrame([{
            'Transponder Number': 'TOTAL',
            'Date': '',
            'Time': '',
            'Posting Date': '',
            'Location': '',
            'Amount': total_amount,
            'Toll Type': '',
            'weekday': '',
            'day_name': '',
            'date_str': ''
        }])
        
        # Concatenate the work_hours DataFrame with the total row
        work_hours_with_total = pd.concat([work_hours, total_row], ignore_index=True)
        
        # Save expensable transactions with total to a new CSV file (retaining all fields)
        expensable_file_path = f"expensable_{os.path.basename(file_path)}"
        work_hours_with_total.to_csv(expensable_file_path, index=False)
        print(f"Expensable transactions saved to {expensable_file_path}")
        
        # Automatically create filtered receipt file with Account Activity and only expendable vehicle activities
        filtered_receipt_path = filter_receipt_file(file_path)
        if filtered_receipt_path:
            print(f"Filtered receipt with Account Activity and expendable vehicle activities saved to {filtered_receipt_path}")
        
        # Calculate expensable_days before using it
        expensable_days = len(work_hours['Date'].dt.date.unique())
        
        # Non-expensable transactions
        non_expensable = df[
            df['weekday'].isin([5, 6]) |  # Weekend
            is_christmas |  # Christmas
            is_holiday |  # Bank holiday
            ~df['Time'].between(time(7, 30), time(20, 0))  # Outside work hours
        ]
        
        # Get month and year from filename
        month_year = os.path.splitext(os.path.basename(file_path))[0]
        try:
            month, year = month_year.split('_')
            month_name = calendar.month_name[int(month)]
        except (ValueError, IndexError):
            # If filename doesn't match expected pattern, use a generic name
            month_name = "Unknown"
            year = "Unknown"
        
        # Print results
        print(f"\nToll Expense Report for {month_name} {year}")
        print("=" * 60)
        
        # List all work week transactions
        print("EXPENSABLE TRANSACTIONS (Workdays 7:30AM-8PM):")
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
        
        # Filter out rows that only contain dashes (only check object columns)
        valid_rows = pd.Series([True] * len(df), index=df.index)
        
        # Check Date column for dashes only if it's still object type
        if df['Date'].dtype == 'object':
            valid_rows &= ~df['Date'].str.contains('^-+$', regex=True, na=False)
        
        # Check Time column for dashes only if it's still object type  
        if df['Time'].dtype == 'object':
            valid_rows &= ~df['Time'].str.contains('^-+$', regex=True, na=False)
        
        # Check Amount column for dashes only if it's still object type
        if df['Amount'].dtype == 'object':
            valid_rows &= ~df['Amount'].str.contains('^-+$', regex=True, na=False)
        
        df = df[valid_rows]
        print(f"Debug: After filtering dashes: {len(df)}")
        
        # Convert Amount to numeric
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        # Remove rows where Amount conversion failed
        df = df.dropna(subset=['Amount'])
        print(f"Debug: After amount conversion: {len(df)}")
        
        # Convert Date to datetime - handle both 2-digit and 4-digit years
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y', errors='coerce')
        # Remove rows where Date conversion failed
        df = df.dropna(subset=['Date'])
        
        # Time is already in HH:MM:SS format - only strip if it's still object type
        if df['Time'].dtype == 'object':
            df['Time'] = df['Time'].str.strip()
        
        # Convert Time to datetime.time for proper comparison
        df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.time
        
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

def add_totals_to_all_receipts():
    """Add totals to all existing receipt files."""
    # Find all receipt files
    receipt_files = glob.glob('receipt_*.csv')
    
    if not receipt_files:
        print("No receipt files found.")
        return
    
    print(f"\nFound {len(receipt_files)} receipt files to update:")
    for file in receipt_files:
        print(f"  - {file}")
    
    total_all_amount = 0.0
    for receipt_file in sorted(receipt_files):
        print(f"\n{'='*60}")
        print(f"Updating: {receipt_file}")
        print('='*60)
        
        # Add total to the receipt file
        result = add_total_to_receipt_file(receipt_file)
        if result:
            # Extract the total amount from the file for summary
            try:
                with open(receipt_file, 'r') as file:
                    lines = file.readlines()
                for line in lines:
                    if 'TOTAL VEHICLE ACTIVITIES' in line:
                        parts = line.split(',')
                        if len(parts) >= 6:
                            amount_str = parts[5].strip('"')
                            amount = float(amount_str)
                            total_all_amount += amount
                            break
            except:
                pass
    
    print(f"\n{'='*60}")
    print(f"TOTAL AMOUNT ACROSS ALL RECEIPTS: ${total_all_amount:.2f}")
    print('='*60)

def process_all_files():
    """Process all CSV files and create filtered receipts automatically."""
    # Find all CSV files that match the pattern (month_year.csv)
    csv_files = glob.glob('[0-9]*_2025.csv')
    
    if not csv_files:
        print("No CSV files found matching the pattern (month_year.csv).")
        return
    
    print(f"\nFound {len(csv_files)} CSV files to process:")
    for file in csv_files:
        print(f"  - {file}")
    
    total_amount = 0
    for file_path in sorted(csv_files):
        print(f"\n{'='*60}")
        print(f"Processing: {file_path}")
        print('='*60)
        
        # Create filtered receipt first
        filtered_receipt_path = filter_receipt_file(file_path)
        
        # Then analyze the original file for expensable transactions
        amount = analyze_tool_expenses(file_path)
        total_amount += amount
    
    print(f"\n{'='*60}")
    print(f"TOTAL EXPENSABLE AMOUNT ACROSS ALL FILES: ${total_amount:.2f}")
    print('='*60)

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
            choice = input("\nEnter the number of the file you want to process (or 'q' to quit, 'all' to process all, 'totals' to add totals to receipts): ")
            if choice.lower() == 'q':
                return None
            elif choice.lower() == 'all':
                return 'ALL'
            elif choice.lower() == 'totals':
                return 'TOTALS'
            
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
    if file_name == 'ALL':
        process_all_files()
    elif file_name == 'TOTALS':
        add_totals_to_all_receipts()
    elif file_name:
        analyze_tool_expenses(file_name)
    else:
        print("No file selected. Exiting.")