#!/usr/bin/env python3
"""
Batch generate profit and comparison data for multiple dates
"""

from datetime import datetime, timedelta, date
from calculate_profit_by_date import save_profit_and_comparison_by_date

def generate_daily_history(start_date_str=None, end_date_str=None):
    """Generate profit and comparison data for each day in the date range
    
    Args:
        start_date_str: Start date in format "YYYY-MM-DD". If None, uses 30 days ago
        end_date_str: End date in format "YYYY-MM-DD". If None, uses today
    """
    # Default to last 30 days if no dates provided
    if end_date_str is None:
        end_date = date.today()
        end_date_str = end_date.strftime("%Y-%m-%d")
    else:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    if start_date_str is None:
        start_date = end_date - timedelta(days=30)
        start_date_str = start_date.strftime("%Y-%m-%d")
    else:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    
    current_date = start_date
    dates_to_process = []
    
    while current_date <= end_date:
        dates_to_process.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    print(f"\n{'='*70}")
    print(f"Generating data for {len(dates_to_process)} dates")
    print(f"From {start_date_str} to {end_date_str}")
    print(f"{'='*70}\n")
    
    for idx, date_str in enumerate(dates_to_process, 1):
        print(f"\n[{idx}/{len(dates_to_process)}] Processing {date_str}...")
        try:
            save_profit_and_comparison_by_date(date_str)
        except Exception as e:
            print(f"❌ Error processing {date_str}: {e}")
            continue
    
    print(f"\n{'='*70}")
    print(f"Batch processing complete!")
    print(f"Processed {len(dates_to_process)} dates")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    # By default, generates data for the last 30 days
    # You can specify custom date range:
    # generate_daily_history("2025-10-22", "2025-11-20")
    
    generate_daily_history()
    
    # Option 2: Generate for last N days
    # from datetime import datetime, timedelta
    # end_date = datetime.now().strftime("%Y-%m-%d")
    # start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    # generate_daily_history(start_date, end_date)
