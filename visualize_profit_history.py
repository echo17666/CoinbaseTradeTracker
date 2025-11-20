import json
import os
import glob
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict

def load_all_profit_files():
    """Load all profit history files
    
    Returns:
        Dictionary mapping date to profit data
    """
    profit_files = glob.glob("./profit_history/profit_begin_*.json")
    
    profit_data = {}
    for file_path in profit_files:
        # Extract date from filename
        filename = os.path.basename(file_path)
        date_str = filename.replace("profit_begin_", "").replace(".json", "")
        
        # Convert YYYYMMDD to datetime
        date = datetime.strptime(date_str, "%Y%m%d")
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        profit_data[date] = data
    
    return profit_data

def load_all_comparison_files():
    """Load all comparison history files
    
    Returns:
        Dictionary mapping date to comparison data
    """
    comparison_files = glob.glob("./comparison/comparison_begin_*.json")
    
    comparison_data = {}
    for file_path in comparison_files:
        # Extract date from filename
        filename = os.path.basename(file_path)
        date_str = filename.replace("comparison_begin_", "").replace(".json", "")
        
        # Convert YYYYMMDD to datetime
        date = datetime.strptime(date_str, "%Y%m%d")
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        comparison_data[date] = data
    
    return comparison_data

def plot_daily_profit_by_coin(profit_data, coin=None):
    """Plot cumulative daily profit (realized + unrealized) for each coin or a specific coin
    
    Args:
        profit_data: Dictionary mapping date to profit data
        coin: Optional specific coin ticker (e.g., "BTC-USDC"). If None, plot all coins
    """
    if not profit_data:
        print("No profit data found")
        return
    
    # Organize data by coin
    coin_profits = defaultdict(lambda: {"dates": [], "realized": [], "unrealized": [], "total": []})
    
    sorted_dates = sorted(profit_data.keys())
    
    for date in sorted_dates:
        data = profit_data[date]
        for item in data:
            ticker = item["ticker"]
            
            # Filter by coin if specified
            if coin and ticker != coin:
                continue
            
            coin_profits[ticker]["dates"].append(date)
            coin_profits[ticker]["realized"].append(item["realized_profit"])
            coin_profits[ticker]["unrealized"].append(item["unrealized_profit"])
            coin_profits[ticker]["total"].append(item["total_profit"])
    
    # If specific coin requested and not found
    if coin and coin not in coin_profits:
        print(f"Coin {coin} not found in profit data")
        return
    
    # Determine number of subplots needed
    coins_to_plot = [coin] if coin else sorted(coin_profits.keys())
    num_coins = len(coins_to_plot)
    
    if num_coins == 0:
        print("No coins to plot")
        return
    
    # Create figure with subplots
    fig, axes = plt.subplots(num_coins, 1, figsize=(12, 4 * num_coins))
    if num_coins == 1:
        axes = [axes]
    
    fig.suptitle("Cumulative Daily Profit by Coin" if not coin else f"Cumulative Profit for {coin}", fontsize=16, y=0.995)
    
    for idx, ticker in enumerate(coins_to_plot):
        ax = axes[idx]
        data = coin_profits[ticker]
        
        dates = data["dates"]
        realized = data["realized"]
        unrealized = data["unrealized"]
        total = data["total"]
        
        # Note: The data from profit_begin_YYYYMMDD.json is already cumulative
        # because it includes all trades up to that date
        # So we can use the values directly
        
        # Convert dates to numeric for bar positioning
        x = np.arange(len(dates))
        width = 0.8
        
        # Plot stacked bars: realized (dark) + unrealized (light) on top
        realized_colors = ['darkgreen' if r >= 0 else 'darkred' for r in realized]
        unrealized_colors = ['lightgreen' if u >= 0 else 'lightcoral' for u in unrealized]
        
        ax.bar(x, realized, width, label='Realized', color=realized_colors, alpha=0.7)
        ax.bar(x, unrealized, width, bottom=realized, label='Unrealized', color=unrealized_colors, alpha=0.6)
        
        # Overlay line chart for total profit
        ax2 = ax.twinx()  # Create a second y-axis
        line_color = 'blue'
        line = ax2.plot(x, total, marker='o', linewidth=2.5, markersize=5, color=line_color, 
                       label='Total Profit', linestyle='-', zorder=10)
        
        # Add value labels on line data points
        for i, value in enumerate(total):
            if len(dates) <= 15 or i % max(1, len(dates)//8) == 0 or i == len(dates)-1:
                ax2.annotate(f'${value:.0f}', 
                           xy=(i, value), 
                           xytext=(0, 10 if value >= 0 else -15),
                           textcoords='offset points',
                           ha='center',
                           fontsize=7,
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
        
        # Synchronize y-axes
        ax2.set_ylim(ax.get_ylim())
        ax2.set_ylabel('')
        ax2.set_yticks([])
        
        # Add horizontal line at y=0
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
        
        # Formatting
        ax.set_title(f"{ticker}", fontsize=12, fontweight='bold')
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Profit ($)")
        
        # Combine legends from both axes
        bars_legend = ax.get_legend_handles_labels()
        line_legend = ax2.get_legend_handles_labels()
        ax.legend(bars_legend[0] + line_legend[0], bars_legend[1] + line_legend[1], 
                 loc='best', fontsize=8)
        
        ax.grid(True, alpha=0.3, axis='y')
        
        # Format x-axis dates
        ax.set_xticks(x[::max(1, len(x)//10)])
        ax.set_xticklabels([dates[i].strftime('%Y-%m-%d') for i in range(0, len(dates), max(1, len(dates)//10))],
                          rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save combined chart
    os.makedirs("./charts", exist_ok=True)
    filename = f"./charts/daily_profit_{coin.replace('-', '_')}.png" if coin else "./charts/daily_profit_all_coins.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Chart saved to {filename}")
    
    plt.close()

def plot_total_daily_profit(profit_data):
    """Plot total cumulative daily profit across all coins
    
    Args:
        profit_data: Dictionary mapping date to profit data
    """
    if not profit_data:
        print("No profit data found")
        return
    
    sorted_dates = sorted(profit_data.keys())
    
    total_realized = []
    total_unrealized = []
    total_profit = []
    
    for date in sorted_dates:
        data = profit_data[date]
        realized = sum(item["realized_profit"] for item in data)
        unrealized = sum(item["unrealized_profit"] for item in data)
        total = sum(item["total_profit"] for item in data)
        
        total_realized.append(realized)
        total_unrealized.append(unrealized)
        total_profit.append(total)
    
    # Note: The data is already cumulative because profit_begin_YYYYMMDD.json
    # includes all trades from the beginning up to that date
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Convert dates to numeric for bar positioning
    x = np.arange(len(sorted_dates))
    width = 0.8
    
    # Plot stacked bars: realized (dark) + unrealized (light) on top
    realized_colors = ['darkgreen' if r >= 0 else 'darkred' for r in total_realized]
    unrealized_colors = ['lightgreen' if u >= 0 else 'lightcoral' for u in total_unrealized]
    
    ax.bar(x, total_realized, width, label='Realized', color=realized_colors, alpha=0.7)
    ax.bar(x, total_unrealized, width, bottom=total_realized, label='Unrealized', color=unrealized_colors, alpha=0.6)
    
    # Overlay line chart for total profit
    ax2 = ax.twinx()  # Create a second y-axis
    line_color = 'blue'
    line = ax2.plot(x, total_profit, marker='o', linewidth=3, markersize=6, color=line_color, 
                   label='Total Profit', linestyle='-', zorder=10)
    
    # Add value labels on line data points
    for i, value in enumerate(total_profit):
        if len(sorted_dates) <= 15 or i % max(1, len(sorted_dates)//10) == 0 or i == len(sorted_dates)-1:
            ax2.annotate(f'${value:.0f}', 
                       xy=(i, value), 
                       xytext=(0, 10 if value >= 0 else -15),
                       textcoords='offset points',
                       ha='center',
                       fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
    
    # Synchronize y-axes
    ax2.set_ylim(ax.get_ylim())
    ax2.set_ylabel('')
    ax2.set_yticks([])
    
    # Add horizontal line at y=0
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1.5)
    
    # Formatting
    ax.set_title("Total Cumulative Daily Profit (All Coins)", fontsize=16, fontweight='bold')
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Cumulative Profit ($)", fontsize=12)
    
    # Combine legends from both axes
    bars_legend = ax.get_legend_handles_labels()
    line_legend = ax2.get_legend_handles_labels()
    ax.legend(bars_legend[0] + line_legend[0], bars_legend[1] + line_legend[1], 
             loc='best', fontsize=11)
    
    ax.grid(True, alpha=0.3, axis='y')
    
    # Format x-axis dates
    ax.set_xticks(x[::max(1, len(x)//15)])
    ax.set_xticklabels([sorted_dates[i].strftime('%Y-%m-%d') for i in range(0, len(sorted_dates), max(1, len(sorted_dates)//15))],
                      rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save combined chart
    os.makedirs("./charts", exist_ok=True)
    filename = "./charts/total_daily_profit.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Chart saved to {filename}")
    
    plt.close()

def plot_vs_btc_comparison(comparison_data, coin=None):
    """Plot profit comparison vs BTC for each coin
    
    Args:
        comparison_data: Dictionary mapping date to comparison data
        coin: Optional specific coin ticker (e.g., "BTC-USDC"). If None, plot all coins
    """
    if not comparison_data:
        print("No comparison data found")
        return
    
    # Organize data by coin
    coin_comparisons = defaultdict(lambda: {"dates": [], "actual": [], "btc_alternative": [], "difference": []})
    
    sorted_dates = sorted(comparison_data.keys())
    
    for date in sorted_dates:
        data = comparison_data[date]
        vs_btc = data.get("vs_btc_comparison", [])
        
        for item in vs_btc:
            ticker = item["ticker"]
            
            # Filter by coin if specified
            if coin and ticker != coin:
                continue
            
            coin_comparisons[ticker]["dates"].append(date)
            coin_comparisons[ticker]["actual"].append(item["actual_profit"])
            coin_comparisons[ticker]["btc_alternative"].append(item["btc_alternative_profit"])
            coin_comparisons[ticker]["difference"].append(item["difference"])
    
    # If specific coin requested and not found
    if coin and coin not in coin_comparisons:
        print(f"Coin {coin} not found in comparison data")
        return
    
    # Determine coins to plot
    coins_to_plot = [coin] if coin else sorted(coin_comparisons.keys())
    num_coins = len(coins_to_plot)
    
    if num_coins == 0:
        print("No coins to plot")
        return
    
    # Create figure with subplots
    fig, axes = plt.subplots(num_coins, 1, figsize=(12, 4 * num_coins))
    if num_coins == 1:
        axes = [axes]
    
    fig.suptitle("Actual Profit vs BTC Alternative" if not coin else f"Profit vs BTC for {coin}", fontsize=16)
    
    for idx, ticker in enumerate(coins_to_plot):
        ax = axes[idx]
        data = coin_comparisons[ticker]
        
        dates = data["dates"]
        actual = data["actual"]
        btc_alt = data["btc_alternative"]
        difference = data["difference"]
        
        # Plot lines
        ax.plot(dates, actual, marker='o', label='Actual Profit', linewidth=2, color='blue')
        ax.plot(dates, btc_alt, marker='s', label='BTC Alternative', linewidth=2, color='orange')
        ax.plot(dates, difference, marker='^', label='Difference (Beat BTC)', linewidth=2, color='green', linestyle='--')
        
        # Add horizontal line at y=0
        ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
        
        # Formatting
        ax.set_title(f"{ticker}", fontsize=12, fontweight='bold')
        ax.set_xlabel("Date")
        ax.set_ylabel("Profit ($)")
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs("./charts", exist_ok=True)
    filename = f"./charts/vs_btc_{coin.replace('-', '_')}.png" if coin else "./charts/vs_btc_all_coins.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Chart saved to {filename}")
    
    plt.close()

def plot_roi_comparison(comparison_data, coin=None):
    """Plot ROI comparison: price change vs trading ROI
    
    Args:
        comparison_data: Dictionary mapping date to comparison data
        coin: Optional specific coin ticker (e.g., "BTC-USDC"). If None, plot all coins
    """
    if not comparison_data:
        print("No comparison data found")
        return
    
    # Organize data by coin
    coin_roi = defaultdict(lambda: {"dates": [], "price_change": [], "trading_roi": [], "difference": []})
    
    sorted_dates = sorted(comparison_data.keys())
    
    for date in sorted_dates:
        data = comparison_data[date]
        roi_comp = data.get("roi_comparison", [])
        
        for item in roi_comp:
            ticker = item["ticker"]
            
            # Filter by coin if specified
            if coin and ticker != coin:
                continue
            
            coin_roi[ticker]["dates"].append(date)
            coin_roi[ticker]["price_change"].append(item["price_change_percent"])
            coin_roi[ticker]["trading_roi"].append(item["trading_roi_percent"])
            coin_roi[ticker]["difference"].append(item["performance_diff"])
    
    # If specific coin requested and not found
    if coin and coin not in coin_roi:
        print(f"Coin {coin} not found in ROI comparison data")
        return
    
    # Determine coins to plot
    coins_to_plot = [coin] if coin else sorted(coin_roi.keys())
    num_coins = len(coins_to_plot)
    
    if num_coins == 0:
        print("No coins to plot")
        return
    
    # Create figure with subplots
    fig, axes = plt.subplots(num_coins, 1, figsize=(12, 4 * num_coins))
    if num_coins == 1:
        axes = [axes]
    
    fig.suptitle("Price Change vs Trading ROI" if not coin else f"ROI Comparison for {coin}", fontsize=16)
    
    for idx, ticker in enumerate(coins_to_plot):
        ax = axes[idx]
        data = coin_roi[ticker]
        
        dates = data["dates"]
        price_change = data["price_change"]
        trading_roi = data["trading_roi"]
        difference = data["difference"]
        
        # Plot lines
        ax.plot(dates, price_change, marker='o', label='Price Change %', linewidth=2, color='purple')
        ax.plot(dates, trading_roi, marker='s', label='Trading ROI %', linewidth=2, color='blue')
        ax.plot(dates, difference, marker='^', label='Performance Diff %', linewidth=2, color='green', linestyle='--')
        
        # Add horizontal line at y=0
        ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
        
        # Formatting
        ax.set_title(f"{ticker}", fontsize=12, fontweight='bold')
        ax.set_xlabel("Date")
        ax.set_ylabel("Percentage (%)")
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs("./charts", exist_ok=True)
    filename = f"./charts/roi_comparison_{coin.replace('-', '_')}.png" if coin else "./charts/roi_comparison_all_coins.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Chart saved to {filename}")
    
    plt.close()

def main():
    """Main function to generate all charts"""
    print("Loading profit data...")
    profit_data = load_all_profit_files()
    print(f"Found {len(profit_data)} profit data files")
    
    print("\nLoading comparison data...")
    comparison_data = load_all_comparison_files()
    print(f"Found {len(comparison_data)} comparison data files")
    
    if not profit_data and not comparison_data:
        print("\n❌ No data files found. Please run calculate_profit_by_date.py first.")
        return
    
    print("\n" + "="*70)
    print("Generating Charts")
    print("="*70)
    
    # Generate total profit chart
    if profit_data:
        print("\n1. Generating total daily profit chart...")
        plot_total_daily_profit(profit_data)
        
        # Generate individual coin profit charts (optional - can be commented out if too many)
        print("\n2. Generating profit charts for each coin...")
        plot_daily_profit_by_coin(profit_data)
    
    # Generate comparison charts
    if comparison_data:
        print("\n3. Generating vs BTC comparison charts...")
        plot_vs_btc_comparison(comparison_data)
        
        print("\n4. Generating ROI comparison charts...")
        plot_roi_comparison(comparison_data)
    
    print("\n" + "="*70)
    print("All charts generated successfully!")
    print("Charts are saved in ./charts/ directory")
    print("="*70)

if __name__ == "__main__":
    # Generate all charts
    main()
    
    # Or generate charts for specific coins:
    # profit_data = load_all_profit_files()
    # comparison_data = load_all_comparison_files()
    
    # plot_daily_profit_by_coin(profit_data, coin="BTC-USDC")
    # plot_vs_btc_comparison(comparison_data, coin="ETH-USDC")
    # plot_roi_comparison(comparison_data, coin="SOL-USDC")
