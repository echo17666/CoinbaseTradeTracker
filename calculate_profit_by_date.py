import json
import os
from datetime import datetime, timezone, timedelta
from calculate_profit_history import (
    get_hold,
    get_price,
    load_trade_history,
    get_all_tickers,
    extract_ticker_trades,
    calculate_profit_components,
    calculate_ticker_roi,
    calculate_ticker_vs_btc,
    calculate_btc_baseline
)

def filter_trades_by_date(trade_history, end_date_str):
    """Filter trades up to a specific date
    
    Args:
        trade_history: List of all trades
        end_date_str: End date in format "YYYY-MM-DD" or "YYYYMMDD"
    
    Returns:
        List of trades up to (and including) the end date
    """
    # Parse end date
    if len(end_date_str) == 8:  # YYYYMMDD format
        end_date = datetime.strptime(end_date_str, "%Y%m%d")
    else:  # YYYY-MM-DD format
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    end_date = end_date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    
    filtered_trades = []
    for trade in trade_history:
        trade_time = datetime.fromisoformat(trade["trade_time"].replace('Z', '+00:00'))
        if trade_time <= end_date:
            filtered_trades.append(trade)
    
    return filtered_trades

def calculate_profit_by_date(end_date_str):
    """Calculate profit from beginning to a specific date
    
    Args:
        end_date_str: End date in format "YYYY-MM-DD" or "YYYYMMDD"
    
    Returns:
        List of profit data for each coin
    """
    print(f"\n{'='*70}")
    print(f"Calculating profit from beginning to {end_date_str}")
    print(f"{'='*70}\n")
    
    # Parse end date to get the price at that time
    if len(end_date_str) == 8:  # YYYYMMDD format
        end_date = datetime.strptime(end_date_str, "%Y%m%d")
    else:  # YYYY-MM-DD format
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    # Set to end of day for price lookup
    # BUT: if it's today and we're before EOD, use current time minus 5 minutes
    now = datetime.now(timezone.utc)
    end_datetime = end_date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    
    # If requesting today's data and we haven't reached EOD yet, use recent time
    if end_date.date() == now.date() and now < end_datetime:
        end_datetime = (now - timedelta(minutes=5)).replace(microsecond=0)
        print(f"  ℹ️  Using current time (5 min ago) for today's price: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    end_date_iso = end_datetime.isoformat().replace('+00:00', 'Z')
    
    # Load all trade history
    all_trades = load_trade_history("alltime")
    
    # Filter trades by date
    filtered_trades = filter_trades_by_date(all_trades, end_date_str)
    
    if not filtered_trades:
        print(f"No trades found up to {end_date_str}")
        return []
    
    print(f"Found {len(filtered_trades)} trades up to {end_date_str}")
    
    # Get all tickers from filtered trades
    tickers = set(trade["product_id"] for trade in filtered_trades)
    all_coins = []
    for ticker in tickers:
        if ticker.endswith("-USDC") or ticker.endswith("-USD"):
            coin = ticker.split("-")[0]
            all_coins.append(coin)
    
    # Get current holdings (to know what we're still holding)
    hold = get_hold()
    
    results = []
    print(f"\n{'Coin':<10} {'Realized':<15} {'Unrealized':<15} {'Total':<15}")
    print("-" * 60)
    
    for coin in all_coins:
        ticker = f"{coin}-USDC"
        
        # Extract trades for this ticker from filtered trades
        trades_data = extract_ticker_trades(filtered_trades, ticker)
        
        # Get current hold amount
        hold_amount = hold.get(coin, {}).get("hold", 0)
        
        # Get price at the end date (historical price)
        if hold_amount > 0:
            from calculate_profit_history import get_historical_price_from_candles, get_price
            historical_price = get_historical_price_from_candles(ticker, end_date_iso)
            if not historical_price:
                # Fallback 1: try to get current real-time price
                print(f"  ⚠️  Could not get historical price for {coin} at {end_date_str}, trying real-time price...")
                current_price = get_price(ticker)
                if current_price and current_price > 0:
                    historical_price = current_price
                    print(f"  ℹ️  Using current price ${historical_price:.2f} for {coin}")
                else:
                    # Fallback 2: use the last trade price before end date
                    ticker_trades = sorted([t for t in filtered_trades if t["product_id"] == ticker], 
                                         key=lambda x: x["trade_time"], reverse=True)
                    if ticker_trades:
                        historical_price = float(ticker_trades[0]["price"])
                        print(f"  ℹ️  Using last trade price ${historical_price:.2f} for {coin}")
                    else:
                        historical_price = 0
                        print(f"  ⚠️  Could not determine any price for {coin} at {end_date_str}")
        else:
            historical_price = 0
        
        # Calculate profit components using historical price
        profit_components = calculate_profit_components(trades_data, hold_amount, historical_price)
        
        # Calculate profit components using historical price
        profit_components = calculate_profit_components(trades_data, hold_amount, historical_price)
        
        result = {
            "ticker": ticker,
            "total_buys": round(float(trades_data["total_buys"]), 8),
            "total_sells": round(float(trades_data["total_sells"]), 8),
            "hold_amount": round(float(hold_amount), 8),
            "price_at_date": round(float(historical_price), 8),  # Add historical price to output
            "realized_profit": round(float(profit_components["realized_profit"]), 8),
            "unrealized_profit": round(float(profit_components["unrealized_profit"]), 8),
            "total_profit": round(float(profit_components["total_profit"]), 8),
        }
        results.append(result)
        
        print(f"{coin:<10} ${result['realized_profit']:>13.2f} ${result['unrealized_profit']:>13.2f} ${result['total_profit']:>13.2f}")
    
    print("-" * 60)
    total_realized = sum(r["realized_profit"] for r in results)
    total_unrealized = sum(r["unrealized_profit"] for r in results)
    total_profit = sum(r["total_profit"] for r in results)
    print(f"{'TOTAL':<10} ${total_realized:>13.2f} ${total_unrealized:>13.2f} ${total_profit:>13.2f}")
    
    return results

def calculate_comparison_by_date(end_date_str, profit_results=None):
    """Calculate ROI and vs BTC comparison from beginning to a specific date
    
    Args:
        end_date_str: End date in format "YYYY-MM-DD" or "YYYYMMDD"
        profit_results: Pre-calculated profit results (optional)
    
    Returns:
        Dictionary containing roi_comparison and vs_btc_comparison
    """
    # Parse end date to get the price at that time
    if len(end_date_str) == 8:  # YYYYMMDD format
        end_date = datetime.strptime(end_date_str, "%Y%m%d")
    else:  # YYYY-MM-DD format
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    # Set to end of day for price lookup
    # BUT: if it's today and we're before EOD, use current time minus 5 minutes
    now = datetime.now(timezone.utc)
    end_datetime = end_date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    
    # If requesting today's data and we haven't reached EOD yet, use recent time
    if end_date.date() == now.date() and now < end_datetime:
        end_datetime = (now - timedelta(minutes=5)).replace(microsecond=0)
    
    end_date_iso = end_datetime.isoformat().replace('+00:00', 'Z')
    
    # Load all trade history
    all_trades = load_trade_history("alltime")
    
    # Filter trades by date
    filtered_trades = filter_trades_by_date(all_trades, end_date_str)
    
    if not filtered_trades:
        print(f"No trades found up to {end_date_str}")
        return None
    
    # Create temporary trade history file for filtered trades
    temp_file = "./trade_history/temp_filtered.json"
    with open(temp_file, "w") as f:
        json.dump(filtered_trades, f, indent=4)
    
    try:
        # Get all tickers from filtered trades
        tickers = set(trade["product_id"] for trade in filtered_trades)
        all_coins = []
        for ticker in tickers:
            if ticker.endswith("-USDC") or ticker.endswith("-USD"):
                coin = ticker.split("-")[0]
                all_coins.append(coin)
        
        # Get current holdings
        hold = get_hold()
        
        # Create profit dict from results
        if profit_results:
            profit_dict = {item["ticker"]: item for item in profit_results}
        else:
            profit_dict = {}
        
        # Calculate ROI comparison
        print(f"\n{'='*130}")
        print("ROI COMPARISON")
        print(f"{'='*130}\n")
        
        roi_results = []
        for coin in all_coins:
            if coin == "USDC":
                continue
            ticker = f"{coin}-USDC"
            profit_data = profit_dict.get(ticker)
            
            # Extract trades for this ticker from filtered trades
            trades_data = extract_ticker_trades(filtered_trades, ticker)
            hold_amount = hold.get(coin, {}).get("hold", 0)
            
            # Get price at the end date (historical price)
            if hold_amount > 0:
                from calculate_profit_history import get_historical_price_from_candles, get_price
                current_price = get_historical_price_from_candles(ticker, end_date_iso)
                if not current_price:
                    # Fallback 1: try to get current real-time price
                    real_time_price = get_price(ticker)
                    if real_time_price and real_time_price > 0:
                        current_price = real_time_price
                    else:
                        # Fallback 2: use the last trade price before end date
                        ticker_trades = sorted([t for t in filtered_trades if t["product_id"] == ticker], 
                                             key=lambda x: x["trade_time"], reverse=True)
                        if ticker_trades:
                            current_price = float(ticker_trades[0]["price"])
                        else:
                            current_price = 0
            else:
                current_price = 0
            
            # Use provided profit data or calculate it
            if profit_data:
                total_profit = profit_data["total_profit"]
                total_buys = profit_data["total_buys"]
                realized_profit = profit_data["realized_profit"]
                unrealized_profit = profit_data["unrealized_profit"]
            else:
                profit_components = calculate_profit_components(trades_data, hold_amount, current_price)
                total_profit = profit_components["total_profit"]
                realized_profit = profit_components["realized_profit"]
                unrealized_profit = profit_components["unrealized_profit"]
                total_buys = trades_data["total_buys"]
            
            # Calculate ROI metrics (similar to calculate_ticker_roi)
            avg_buy_price = trades_data["total_buys"] / trades_data["total_buy_size"] if trades_data["total_buy_size"] > 0 else 0
            if hold_amount > 0 and trades_data["total_buy_size"] > 0:
                net_investment = avg_buy_price * hold_amount
            else:
                net_investment = 0
            
            hold_ratio = (hold_amount / trades_data["total_buy_size"]) if trades_data["total_buy_size"] > 0 else 0
            
            if hold_ratio < 0.05:
                trading_roi_percent = (total_profit / total_buys * 100) if total_buys > 0 else 0
                net_investment = total_buys
            elif hold_amount > 0 and net_investment > 0:
                trading_roi_percent = (total_profit / net_investment * 100)
            else:
                trading_roi_percent = 0
            
            # Get start price
            start_time = min(trades_data["buy_times"]) if trades_data["buy_times"] else None
            if start_time:
                from calculate_profit_history import get_historical_price_from_candles, get_price
                start_price = get_historical_price_from_candles(ticker, start_time)
                if not start_price:
                    # Fallback to first trade price
                    ticker_trades = sorted([t for t in filtered_trades if t["product_id"] == ticker], key=lambda x: x["trade_time"])
                    if ticker_trades:
                        start_price = float(ticker_trades[0]["price"])
                    else:
                        start_price = current_price
            else:
                start_price = current_price
            
            # Calculate price change
            if hold_amount > 0:
                price_change_percent = ((current_price - start_price) / start_price * 100) if start_price > 0 else 0
            else:
                avg_sell_price = trades_data["total_sells"] / trades_data["total_sell_size"] if trades_data["total_sell_size"] > 0 else 0
                price_change_percent = ((avg_sell_price - start_price) / start_price * 100) if start_price > 0 else 0
                current_price = avg_sell_price
            
            performance_diff = trading_roi_percent - price_change_percent
            
            result = {
                "ticker": ticker,
                "start_time": start_time,
                "start_price": round(float(start_price), 8),
                "current_price": round(float(current_price), 8),
                "price_change_percent": round(float(price_change_percent), 2),
                "total_buys": round(float(total_buys), 8),
                "total_sells": round(float(trades_data["total_sells"]), 8),
                "net_investment": round(float(net_investment), 8),
                "hold_amount": round(float(hold_amount), 8),
                "realized_profit": round(float(realized_profit), 8),
                "unrealized_profit": round(float(unrealized_profit), 8),
                "total_profit": round(float(total_profit), 8),
                "trading_roi_percent": round(float(trading_roi_percent), 2),
                "performance_diff": round(float(performance_diff), 2),
                "beat_hodl": performance_diff >= 0
            }
            roi_results.append(result)
        
        # Calculate vs BTC comparison
        print(f"\n{'='*90}")
        print("VS BTC COMPARISON")
        print(f"{'='*90}\n")
        
        btc_results = []
        for coin in all_coins:
            if coin == "USDC":
                continue
            ticker = f"{coin}-USDC"
            profit_data = profit_dict.get(ticker)
            
            # Extract trades for this ticker
            trades_data = extract_ticker_trades(filtered_trades, ticker)
            hold_amount = hold.get(coin, {}).get("hold", 0)
            
            # Get actual profit
            if profit_data:
                actual_profit = profit_data["total_profit"]
                total_buys = profit_data["total_buys"]
                total_sells = profit_data["total_sells"]
            else:
                # Get price at the end date (historical price)
                if hold_amount > 0:
                    from calculate_profit_history import get_price
                    current_price = get_historical_price_from_candles(ticker, end_date_iso)
                    if not current_price:
                        # Fallback 1: try current real-time price
                        real_time_price = get_price(ticker)
                        if real_time_price and real_time_price > 0:
                            current_price = real_time_price
                        else:
                            # Fallback 2: use last trade price
                            ticker_trades = sorted([t for t in filtered_trades if t["product_id"] == ticker], 
                                                 key=lambda x: x["trade_time"], reverse=True)
                            if ticker_trades:
                                current_price = float(ticker_trades[0]["price"])
                            else:
                                current_price = 0
                else:
                    current_price = 0
                    
                profit_components = calculate_profit_components(trades_data, hold_amount, current_price)
                actual_profit = profit_components["total_profit"]
                total_buys = trades_data["total_buys"]
                total_sells = trades_data["total_sells"]
            
            # Calculate BTC alternative profit
            if trades_data["buy_times"] and total_buys > 0:
                start_time = min(trades_data["buy_times"])
                
                from calculate_profit_history import get_historical_price_from_candles
                btc_price_start = get_historical_price_from_candles("BTC-USDC", start_time)
                if not btc_price_start:
                    btc_trades = sorted([t for t in filtered_trades if t["product_id"] == "BTC-USDC"], key=lambda x: x["trade_time"])
                    if btc_trades:
                        btc_price_start = float(btc_trades[0]["price"])
                    else:
                        btc_price_start = get_price("BTC-USDC")
                
                # Get BTC price at the end date (historical price)
                btc_price_current = get_historical_price_from_candles("BTC-USDC", end_date_iso)
                if not btc_price_current:
                    btc_trades = sorted([t for t in filtered_trades if t["product_id"] == "BTC-USDC"], 
                                       key=lambda x: x["trade_time"], reverse=True)
                    if btc_trades:
                        btc_price_current = float(btc_trades[0]["price"])
                    else:
                        btc_price_current = get_price("BTC-USDC")
                
                net_investment = total_buys - total_sells
                btc_amount = total_buys / btc_price_start
                btc_value_from_buys = btc_amount * btc_price_current
                btc_value_after_sells = btc_value_from_buys - total_sells
                btc_alternative_profit = btc_value_after_sells - net_investment
                
                difference = actual_profit - btc_alternative_profit
            else:
                start_time = None
                btc_alternative_profit = 0
                difference = 0
            
            result = {
                "ticker": ticker,
                "start_time": start_time,
                "total_buys": round(float(total_buys), 8),
                "total_sells": round(float(total_sells), 8),
                "hold_amount": round(float(hold_amount), 8),
                "actual_profit": round(float(actual_profit), 8),
                "btc_alternative_profit": round(float(btc_alternative_profit), 8),
                "difference": round(float(difference), 8),
                "better_than_btc": difference >= 0
            }
            btc_results.append(result)
        
        return {
            "roi_comparison": roi_results,
            "vs_btc_comparison": btc_results
        }
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)

def save_profit_and_comparison_by_date(end_date_str):
    """Calculate and save profit and comparison data for a specific date
    
    Args:
        end_date_str: End date in format "YYYY-MM-DD" or "YYYYMMDD"
    """
    # Format date string for filename
    if len(end_date_str) == 8:  # YYYYMMDD
        date_key = end_date_str
    else:  # YYYY-MM-DD
        date_key = end_date_str.replace("-", "")
    
    # Calculate profit
    profit_results = calculate_profit_by_date(end_date_str)
    
    if not profit_results:
        print(f"\nNo data to save for {end_date_str}")
        return
    
    # Save profit data
    os.makedirs("./profit_history", exist_ok=True)
    profit_file = f"./profit_history/profit_begin_{date_key}.json"
    with open(profit_file, "w") as f:
        json.dump(profit_results, f, indent=4)
    print(f"\n✅ Profit data saved to {profit_file}")
    
    # Calculate comparison
    comparison_results = calculate_comparison_by_date(end_date_str, profit_results)
    
    if comparison_results:
        # Save comparison data
        os.makedirs("./comparison", exist_ok=True)
        comparison_file = f"./comparison/comparison_begin_{date_key}.json"
        
        combined = {
            "range": f"begin_{date_key}",
            "end_date": end_date_str,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "roi_comparison": comparison_results["roi_comparison"],
            "vs_btc_comparison": comparison_results["vs_btc_comparison"]
        }
        
        with open(comparison_file, "w") as f:
            json.dump(combined, f, indent=4)
        print(f"✅ Comparison data saved to {comparison_file}")
    
    print(f"\n{'='*70}")
    print(f"All data saved successfully for date: {end_date_str}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    # Example usage: Calculate profit and comparison up to a specific date
    # You can call this function with different dates to generate historical data
    
    # Test with November 1, 2025
    save_profit_and_comparison_by_date("2025-11-01")
