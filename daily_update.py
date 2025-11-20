#!/usr/bin/env python3
"""
Daily automated update script for CoinbaseTradeTracker
Fetches trade data, calculates profit history, and generates charts
"""

import os
import sys
from datetime import datetime, timedelta
import subprocess
import logging

# Set up logging
log_dir = "./logs"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"daily_update_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_script(script_name, description):
    """Run a Python script and log the output
    
    Args:
        script_name: Name of the script to run
        description: Description of what the script does
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"{'='*70}")
    logger.info(f"Running: {description}")
    logger.info(f"Script: {script_name}")
    logger.info(f"{'='*70}")
    
    try:
        result = subprocess.run(
            ["python", script_name],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.stdout:
            logger.info(f"Output:\n{result.stdout}")
        
        if result.stderr:
            logger.warning(f"Errors:\n{result.stderr}")
        
        if result.returncode == 0:
            logger.info(f"✅ {description} completed successfully")
            return True
        else:
            logger.error(f"❌ {description} failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} timed out after 10 minutes")
        return False
    except Exception as e:
        logger.error(f"❌ {description} failed with exception: {str(e)}")
        return False

def main():
    """Main function to run the daily update process"""
    start_time = datetime.now()
    logger.info(f"\n{'='*70}")
    logger.info(f"Starting Daily Update Process")
    logger.info(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*70}\n")
    
    success_count = 0
    total_steps = 4
    
    # Step 1: Fetch filled trade history (incremental mode)
    logger.info(f"\n{'='*70}")
    logger.info(f"Fetching trade history (incremental mode)")
    logger.info(f"{'='*70}")
    
    try:
        from get_filled_history import get_filled_history
        get_filled_history("alltime", incremental=True)
        logger.info(f"✅ Trade history updated successfully")
        success_count += 1
    except Exception as e:
        logger.error(f"❌ Failed to fetch trade history: {str(e)}")
        logger.error("Stopping process.")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    # Step 2: Calculate current profit
    if run_script("calculate_profit_history.py", "Calculate Current Profit"):
        success_count += 1
    else:
        logger.warning("Failed to calculate current profit, but continuing...")
    
    # Step 3: Generate historical profit data for today
    logger.info(f"\n{'='*70}")
    logger.info(f"Generating historical profit data for today")
    logger.info(f"{'='*70}")
    
    try:
        # Import and run the function directly
        from calculate_profit_by_date import save_profit_and_comparison_by_date
        from datetime import date
        
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        save_profit_and_comparison_by_date(today_str)
        logger.info(f"✅ Historical profit data generated for {today}")
        success_count += 1
    except Exception as e:
        logger.error(f"❌ Failed to generate historical profit data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Step 4: Generate visualization charts
    if run_script("visualize_profit_history.py", "Generate Visualization Charts"):
        success_count += 1
    else:
        logger.warning("Failed to generate charts")
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Daily Update Process Completed")
    logger.info(f"{'='*70}")
    logger.info(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duration: {duration}")
    logger.info(f"Success Rate: {success_count}/{total_steps} steps completed")
    logger.info(f"{'='*70}\n")
    
    return success_count == total_steps

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
