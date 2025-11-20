#!/usr/bin/env python3
"""
Quick test to generate a single coin chart
"""

from visualize_profit_history import load_all_profit_files, plot_daily_profit_by_coin

# Load data
profit_data = load_all_profit_files()

# Generate chart for BTC
print("Generating chart for BTC-USDC...")
plot_daily_profit_by_coin(profit_data, coin="BTC-USDC")

print("\nGenerate chart for ZEC-USDC...")
plot_daily_profit_by_coin(profit_data, coin="ZEC-USDC")

print("\nDone! Check ./charts/ directory")
