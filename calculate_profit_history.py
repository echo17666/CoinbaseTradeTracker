import json
import os
import requests
from datetime import datetime, timezone
from utils import build_jwt

# ==================== API Call Functions ====================

def get_hold():
    """Get current holdings"""
    request_method = "GET"
    request_host = "api.coinbase.com"
    request_path = "/api/v3/brokerage/accounts"
    uri = f"{request_method} {request_host}{request_path}"
    jwt_token = build_jwt(uri)
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    url = f"https://{request_host}{request_path}"
    response = requests.get(url, headers=headers)
    response = response.json()
    hold_result = {}
    for account in response.get("accounts", []):
        balance = float(account.get("available_balance", {}).get("value", 0)) + float(account.get("hold", {}).get("value", 0))
        if balance > 0:
            hold_result[account.get("currency")] = {
                "ticker": account.get("currency"),
                "hold": round(balance, 8),
            }
    return hold_result

def get_price(ticker):
    """Get current price"""
    request_method = "GET"
    request_host = "api.coinbase.com"
    request_path = f"/api/v3/brokerage/products/{ticker}"
    uri = f"{request_method} {request_host}{request_path}"
    jwt_token = build_jwt(uri)
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    url = f"https://{request_host}{request_path}"
    response = requests.get(url, headers=headers)
    response = response.json()
    price = float(response.get("price", 0))
    return price

def get_historical_price_from_candles(ticker, timestamp_str):
    """Get historical price at a specific time (minute-level) using candles API
    
    Args:
        ticker: Trading pair, e.g., "BTC-USDC"
        timestamp_str: ISO format timestamp, e.g., "2025-10-22T00:34:38.959435Z"
    """
    request_method = "GET"
    request_host = "api.coinbase.com"
    
    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    start_ts = int(dt.timestamp())
    end_ts = start_ts + 60
    
    request_path = f"/api/v3/brokerage/products/{ticker}/candles"
    uri = f"{request_method} {request_host}{request_path}"
    
    jwt_token = build_jwt(uri)
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    url = f"https://{request_host}{request_path}"
    querystring = {"start": str(start_ts), "end": str(end_ts), "granularity": "ONE_MINUTE"}
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            response_json = response.json()
            if "candles" in response_json and len(response_json["candles"]) > 0:
                candle = response_json["candles"][0]
                return float(candle["open"])
    except Exception as e:
        print(f"  Failed to get historical price for {ticker} at {timestamp_str}: {e}")
    
    return None

# ==================== Data Loading and Processing Functions ====================

def load_trade_history(range="alltime"):
    """Load trade history"""
    with open(f"./trade_history/filled_{range}.json", "r") as f:
        return json.load(f)

def get_all_tickers(range="alltime", hold=None):
    """Get list of all traded coins"""
    trade_history = load_trade_history(range)
    tickers = set(trade["product_id"] for trade in trade_history)
    all_tickers = []
    for ticker in tickers:
        if ticker.endswith("-USDC") or ticker.endswith("-USD"):
            coin = ticker.split("-")[0]
            all_tickers.append(coin)
    
    if hold:
        all_tickers = list(set(all_tickers).union(hold.keys()))
    
    return all_tickers

def extract_ticker_trades(trade_history, ticker):
    """Extract trade data for a specific ticker from trade history
    
    Returns:
        dict: Dictionary containing buys, sells, buy_sizes, sell_sizes, buy_times
    """
    buys = []
    sells = []
    buy_sizes = []
    sell_sizes = []
    buy_times = []
    
    for trade in trade_history:
        if trade["product_id"] == ticker:
            price = float(trade["price"])
            size = float(trade["size"])
            commission = float(trade["commission"])
            
            if trade["side"] == "BUY":
                buys.append(price * size + commission)
                buy_sizes.append(size)
                buy_times.append(trade["trade_time"])
            elif trade["side"] == "SELL":
                sells.append(price * size - commission)
                sell_sizes.append(size)
    
    return {
        "buys": buys,
        "sells": sells,
        "buy_sizes": buy_sizes,
        "sell_sizes": sell_sizes,
        "buy_times": buy_times,
        "total_buys": sum(buys),
        "total_sells": sum(sells),
        "total_buy_size": sum(buy_sizes),
        "total_sell_size": sum(sell_sizes),
    }

def calculate_profit_components(trades_data, hold, current_price=None):
    """Calculate realized and unrealized profits
    
    Args:
        trades_data: Data returned by extract_ticker_trades
        hold: Current holding amount
        current_price: Current price (optional, won't calculate unrealized profit if not provided)
    
    Returns:
        dict: Dictionary containing realized_profit, unrealized_profit, total_profit, etc.
    """
    total_buys = trades_data["total_buys"]
    total_sells = trades_data["total_sells"]
    total_buy_size = trades_data["total_buy_size"]
    total_sell_size = trades_data["total_sell_size"]
    
    # Calculate realized profit
    if total_sell_size > 0 and total_buy_size > 0:
        avg_buy_price = total_buys / total_buy_size
        realized_cost = avg_buy_price * total_sell_size
        realized_profit = total_sells - realized_cost
    else:
        realized_profit = 0
        avg_buy_price = total_buys / total_buy_size if total_buy_size > 0 else 0
    
    # Calculate unrealized profit
    if hold > 0 and current_price is not None and total_buy_size > 0:
        total_holds_value = hold * current_price
        unrealized_cost = avg_buy_price * hold
        unrealized_profit = total_holds_value - unrealized_cost
    else:
        unrealized_profit = 0
    
    total_profit = realized_profit + unrealized_profit
    
    return {
        "avg_buy_price": avg_buy_price,
        "realized_profit": realized_profit,
        "unrealized_profit": unrealized_profit,
        "total_profit": total_profit,
    }

# ==================== Core Calculation Functions ====================

def calculate_profit(range, ticker, hold):
    """Calculate profit for a single coin"""
    trade_history = load_trade_history(range)
    trades_data = extract_ticker_trades(trade_history, ticker)
    
    current_price = get_price(ticker) if hold > 0 else 0
    profit_components = calculate_profit_components(trades_data, hold, current_price)
    
    return {
        "ticker": ticker,
        "total_buys": round(float(trades_data["total_buys"]), 8),
        "total_sells": round(float(trades_data["total_sells"]), 8),
        "hold_amount": round(float(hold), 8),
        "realized_profit": round(float(profit_components["realized_profit"]), 8),
        "unrealized_profit": round(float(profit_components["unrealized_profit"]), 8),
        "total_profit": round(float(profit_components["total_profit"]), 8),
    }

def calculate_ticker_roi(range, ticker, hold, profit_data=None):
    """Calculate price change vs trading ROI comparison for a single coin
    
    Args:
        range: Time range for data
        ticker: Trading pair
        hold: Current holding amount
        profit_data: Pre-calculated profit data (optional, will load if not provided)
    """
    trade_history = load_trade_history(range)
    trades_data = extract_ticker_trades(trade_history, ticker)
    
    # Get current price (needed for price change calculation)
    current_price = get_price(ticker) if hold > 0 else 0
    
    # Use provided profit data or calculate it
    if profit_data:
        total_profit = profit_data["total_profit"]
        total_buys = profit_data["total_buys"]
        realized_profit = profit_data["realized_profit"]
        unrealized_profit = profit_data["unrealized_profit"]
    else:
        profit_components = calculate_profit_components(trades_data, hold, current_price)
        total_profit = profit_components["total_profit"]
        realized_profit = profit_components["realized_profit"]
        unrealized_profit = profit_components["unrealized_profit"]
        total_buys = trades_data["total_buys"]
    
    # Calculate average buy price and net investment
    avg_buy_price = trades_data["total_buys"] / trades_data["total_buy_size"] if trades_data["total_buy_size"] > 0 else 0
    if hold > 0 and trades_data["total_buy_size"] > 0:
        net_investment = avg_buy_price * hold
    else:
        net_investment = 0
    
    # Calculate trading ROI
    hold_ratio = (hold / trades_data["total_buy_size"]) if trades_data["total_buy_size"] > 0 else 0
    
    if hold_ratio < 0.05:  # Close to fully sold out
        trading_roi_percent = (total_profit / total_buys * 100) if total_buys > 0 else 0
        net_investment = total_buys
    elif hold > 0 and net_investment > 0:
        trading_roi_percent = (total_profit / net_investment * 100)
    else:
        trading_roi_percent = 0
    
    # Get start price
    start_time = min(trades_data["buy_times"]) if trades_data["buy_times"] else None
    start_price = None
    
    if start_time:
        start_price = get_historical_price_from_candles(ticker, start_time)
        if not start_price:
            ticker_trades = sorted([t for t in trade_history if t["product_id"] == ticker], key=lambda x: x["trade_time"])
            if ticker_trades:
                start_price = float(ticker_trades[0]["price"])
            else:
                start_price = current_price
    else:
        start_price = current_price
    
    # Calculate price change percentage
    if hold > 0:
        price_change_percent = ((current_price - start_price) / start_price * 100) if start_price > 0 else 0
    else:
        avg_sell_price = trades_data["total_sells"] / trades_data["total_sell_size"] if trades_data["total_sell_size"] > 0 else 0
        price_change_percent = ((avg_sell_price - start_price) / start_price * 100) if start_price > 0 else 0
        current_price = avg_sell_price
    
    performance_diff = trading_roi_percent - price_change_percent
    
    return {
        "ticker": ticker,
        "start_time": start_time,
        "start_price": round(float(start_price), 8),
        "current_price": round(float(current_price), 8),
        "price_change_percent": round(float(price_change_percent), 2),
        "total_buys": round(float(total_buys if profit_data else trades_data["total_buys"]), 8),
        "total_sells": round(float(trades_data["total_sells"]), 8),
        "net_investment": round(float(net_investment), 8),
        "hold_amount": round(float(hold), 8),
        "realized_profit": round(float(realized_profit), 8),
        "unrealized_profit": round(float(unrealized_profit), 8),
        "total_profit": round(float(total_profit), 8),
        "trading_roi_percent": round(float(trading_roi_percent), 2),
        "performance_diff": round(float(performance_diff), 2),
        "beat_hodl": performance_diff >= 0
    }

def calculate_ticker_vs_btc(range, ticker, hold, start_time=None, profit_data=None):
    """Calculate actual profit of a single coin vs if invested in BTC
    
    Args:
        range: Time range for data
        ticker: Trading pair
        hold: Current holding amount
        start_time: Optional unified start time
        profit_data: Pre-calculated profit data (optional, will load if not provided)
    """
    trade_history = load_trade_history(range)
    trades_data = extract_ticker_trades(trade_history, ticker)
    
    # Use provided profit data or calculate it
    if profit_data:
        actual_profit = profit_data["total_profit"]
        total_buys = profit_data["total_buys"]
        total_sells = profit_data["total_sells"]
    else:
        current_price = get_price(ticker) if hold > 0 else 0
        profit_components = calculate_profit_components(trades_data, hold, current_price)
        actual_profit = profit_components["total_profit"]
        total_buys = trades_data["total_buys"]
        total_sells = trades_data["total_sells"]
    
    # Calculate profit if invested in BTC
    if trades_data["buy_times"] and trades_data["total_buys"] > 0:
        if start_time is None:
            start_time = min(trades_data["buy_times"])
        
        btc_price_start = get_historical_price_from_candles("BTC-USDC", start_time)
        if not btc_price_start:
            btc_trades = sorted([t for t in trade_history if t["product_id"] == "BTC-USDC"], key=lambda x: x["trade_time"])
            if btc_trades:
                btc_price_start = float(btc_trades[0]["price"])
            else:
                btc_price_start = get_price("BTC-USDC")
        
        btc_price_current = get_price("BTC-USDC")
        
        net_investment = trades_data["total_buys"] - trades_data["total_sells"]
        btc_amount = trades_data["total_buys"] / btc_price_start
        btc_value_from_buys = btc_amount * btc_price_current
        btc_value_after_sells = btc_value_from_buys - trades_data["total_sells"]
        btc_alternative_profit = btc_value_after_sells - net_investment
        
        difference = actual_profit - btc_alternative_profit
    else:
        start_time = None
        btc_alternative_profit = 0
        difference = 0
    
    return {
        "ticker": ticker,
        "start_time": start_time,
        "total_buys": round(float(total_buys if profit_data else trades_data["total_buys"]), 8),
        "total_sells": round(float(total_sells if profit_data else trades_data["total_sells"]), 8),
        "hold_amount": round(float(hold), 8),
        "actual_profit": round(float(actual_profit), 8),
        "btc_alternative_profit": round(float(btc_alternative_profit), 8),
        "difference": round(float(difference), 8),
        "better_than_btc": difference >= 0
    }

def calculate_btc_baseline(start_time=None):
    """Calculate BTC baseline comparison if all investments were in BTC"""
    range = "alltime"
    trade_history = load_trade_history(range)
    
    trades_sorted = sorted(trade_history, key=lambda x: x["trade_time"])
    earliest_time = trades_sorted[0]["trade_time"] if trades_sorted else None
    
    if start_time is None:
        start_time = earliest_time
    
    print(f"\nGetting BTC price at {start_time}...")
    btc_price_start = get_historical_price_from_candles("BTC-USDC", start_time)
    
    if not btc_price_start:
        print(f"  ⚠️  Unable to get historical price, using first BTC trade price")
        btc_trades = [t for t in trades_sorted if t["product_id"] == "BTC-USDC"]
        if btc_trades:
            btc_price_start = float(btc_trades[0]["price"])
        else:
            btc_price_start = get_price("BTC-USDC")
    else:
        print(f"  ✅ BTC Price (@{start_time}): ${btc_price_start:,.2f}")
    
    # Calculate total net investment
    total_net_investment = 0
    for trade in trade_history:
        if trade["side"] == "BUY":
            total_net_investment += float(trade["price"]) * float(trade["size"]) + float(trade["commission"])
        elif trade["side"] == "SELL":
            total_net_investment -= float(trade["price"]) * float(trade["size"]) - float(trade["commission"])
    
    btc_price_current = get_price("BTC-USDC")
    btc_amount = total_net_investment / btc_price_start
    btc_current_value = btc_amount * btc_price_current
    btc_profit = btc_current_value - total_net_investment
    
    return {
        "start_time": start_time,
        "earliest_time": earliest_time,
        "total_net_investment": round(total_net_investment, 2),
        "btc_price_start": round(btc_price_start, 2),
        "btc_price_current": round(btc_price_current, 2),
        "btc_amount": round(btc_amount, 8),
        "btc_current_value": round(btc_current_value, 2),
        "btc_profit": round(btc_profit, 2),
        "btc_roi_percent": round((btc_profit / total_net_investment * 100) if total_net_investment > 0 else 0, 2)
    }

# ==================== Display Functions ====================

def all_time_profit():
    """Display profit information for all coins"""
    range = "alltime"
    hold = get_hold()
    all_tickers = get_all_tickers(range, hold)
    
    results = []
    total_realized = 0
    total_unrealized = 0
    total_profit = 0
    
    print(f"\n{'Coin':<10} {'Realized':<15} {'Unrealized':<15} {'Total':<15}")
    print("-" * 60)
    
    for coin in all_tickers:
        ticker = f"{coin}-USDC"
        result = calculate_profit(range, ticker, hold.get(coin, {}).get("hold", 0))
        results.append(result)
        
        print(f"{coin:<10} ${result['realized_profit']:>13.2f} ${result['unrealized_profit']:>13.2f} ${result['total_profit']:>13.2f}")
        
        total_realized += result["realized_profit"]
        total_unrealized += result["unrealized_profit"]
        total_profit += result["total_profit"]
    
    print("-" * 60)
    print(f"{'TOTAL':<10} ${total_realized:>13.2f} ${total_unrealized:>13.2f} ${total_profit:>13.2f}")
    
    with open(f"./profit_history/profit_{range}.json", "w") as f:
        json.dump(results, f, indent=4)

def print_btc_baseline_comparison():
    """Print BTC baseline comparison"""
    print("\n" + "=" * 70)
    print("BTC BASELINE COMPARISON (If All Investments Were in BTC)")
    print("=" * 70)
    
    baseline = calculate_btc_baseline()
    
    print(f"\nEarliest Trade Time: {baseline['earliest_time']}")
    print(f"Comparison Start Time: {baseline['start_time']}")
    print(f"Total Net Investment: ${baseline['total_net_investment']:,.2f}")
    print(f"\nBTC Price (@{baseline['start_time']}): ${baseline['btc_price_start']:,.2f}")
    print(f"BTC Price (Current): ${baseline['btc_price_current']:,.2f}")
    print(f"\nIf All Invested in BTC:")
    print(f"  BTC Amount: {baseline['btc_amount']:.8f} BTC")
    print(f"  Current Value: ${baseline['btc_current_value']:,.2f}")
    print(f"  Profit: ${baseline['btc_profit']:,.2f}")
    print(f"  ROI: {baseline['btc_roi_percent']:.2f}%")
    
    # Get actual total profit
    range = "alltime"
    hold = get_hold()
    all_tickers = get_all_tickers(range, hold)
    
    actual_total_profit = 0
    for coin in all_tickers:
        ticker = f"{coin}-USDC"
        result = calculate_profit(range, ticker, hold.get(coin, {}).get("hold", 0))
        actual_total_profit += result["total_profit"]
    
    print(f"\nActual Trading Strategy:")
    print(f"  Total Profit: ${actual_total_profit:,.2f}")
    print(f"  ROI: {(actual_total_profit / baseline['total_net_investment'] * 100) if baseline['total_net_investment'] > 0 else 0:.2f}%")
    
    difference = actual_total_profit - baseline['btc_profit']
    print(f"\n{'📈 Strategy Outperforms BTC' if difference > 0 else '📉 Strategy Underperforms BTC'}")
    print(f"Difference: ${difference:,.2f} ({'+' if difference > 0 else ''}{(difference / baseline['btc_profit'] * 100) if baseline['btc_profit'] != 0 else 0:.2f}%)")
    print("=" * 70)

def print_ticker_vs_btc_comparison(start_time=None, range="alltime"):
    """Print comparison of each ticker vs BTC
    
    Args:
        start_time: Optional unified start time
        range: Time range for data (default: "alltime")
    """
    print("\n" + "=" * 90)
    if start_time:
        print(f"TICKER vs BTC COMPARISON (Unified Start Time: {start_time})")
    else:
        print("TICKER vs BTC COMPARISON (Each ticker uses its own first trade time)")
    print("=" * 90)
    
    # Load profit data
    profit_file = f"./profit_history/profit_{range}.json"
    if not os.path.exists(profit_file):
        print(f"Error: {profit_file} not found. Please run all_time_profit() first.")
        return
    
    with open(profit_file, "r") as f:
        profit_data_list = json.load(f)
    
    # Create a dict for quick lookup
    profit_dict = {item["ticker"]: item for item in profit_data_list}
    
    hold = get_hold()
    all_tickers = get_all_tickers(range, hold)
    
    print(f"\n{'Coin':<10} {'Start Time':<22} {'Actual':<15} {'If BTC':<15} {'Diff':<15} {'Better?':<10}")
    print("-" * 100)
    
    comparisons = []
    for coin in all_tickers:
        if coin == "USDC":
            continue
        ticker = f"{coin}-USDC"
        profit_data = profit_dict.get(ticker)
        result = calculate_ticker_vs_btc(range, ticker, hold.get(coin, {}).get("hold", 0), start_time, profit_data=profit_data)
        comparisons.append(result)
        
        symbol = "✅" if result["better_than_btc"] else "❌"
        start_time_display = result.get('start_time', 'N/A')[:19] if result.get('start_time') else 'N/A'
        print(f"{coin:<10} {start_time_display:<22} ${result['actual_profit']:>12.2f} ${result['btc_alternative_profit']:>12.2f} ${result['difference']:>12.2f} {symbol:<10}")
    
    print("-" * 100)
    
    better_count = sum(1 for c in comparisons if c["better_than_btc"])
    total_count = len(comparisons)
    print(f"\nCoins Outperforming BTC: {better_count}/{total_count} ({better_count/total_count*100 if total_count > 0 else 0:.1f}%)")
    print("=" * 100)
    
    return comparisons

def print_ticker_roi_comparison(range="alltime"):
    """Print comparison of each ticker's price change vs trading performance
    
    Args:
        range: Time range for data (default: "alltime")
    """
    print("\n" + "=" * 130)
    print("TICKER PRICE vs TRADING PERFORMANCE (Price Change vs My Trading Performance)")
    print("=" * 130)
    
    # Load profit data
    profit_file = f"./profit_history/profit_{range}.json"
    if not os.path.exists(profit_file):
        print(f"Error: {profit_file} not found. Please run all_time_profit() first.")
        return
    
    with open(profit_file, "r") as f:
        profit_data_list = json.load(f)
    
    # Create a dict for quick lookup
    profit_dict = {item["ticker"]: item for item in profit_data_list}
    
    hold = get_hold()
    all_tickers = get_all_tickers(range, hold)
    
    print(f"\n{'Coin':<10} {'Start Time':<22} {'Start $':<12} {'Current $':<12} {'Price Change':<12} {'Net Investment':<15} {'My ROI':<12} {'Difference':<12} {'Status':<10}")
    print("-" * 130)
    
    roi_results = []
    for coin in all_tickers:
        if coin == "USDC":
            continue
        ticker = f"{coin}-USDC"
        profit_data = profit_dict.get(ticker)
        result = calculate_ticker_roi(range, ticker, hold.get(coin, {}).get("hold", 0), profit_data=profit_data)
        roi_results.append(result)
        
        start_time_display = result.get('start_time', 'N/A')[:19] if result.get('start_time') else 'N/A'
        
        price_symbol = "📈" if result['price_change_percent'] > 0 else "📉"
        price_str = f"{price_symbol}{result['price_change_percent']:>6.2f}%"
        
        net_inv_str = f"${result['net_investment']:>9.2f}"
        
        roi_symbol = "✅" if result['trading_roi_percent'] > 0 else "❌"
        roi_str = f"{roi_symbol}{result['trading_roi_percent']:>6.2f}%"
        
        diff_symbol = "🟢" if result['beat_hodl'] else "🔴"
        diff_str = f"{diff_symbol}{result['performance_diff']:>+6.2f}%"
        
        status = "Holding" if result['hold_amount'] > 0 else "Sold Out"
        
        print(f"{coin:<10} {start_time_display:<22} ${result['start_price']:>10.2f} ${result['current_price']:>10.2f} "
              f"{price_str:<12} {net_inv_str:<15} {roi_str:<12} {diff_str:<12} {status:<10}")
    
    print("-" * 130)
    
    # Statistics
    positive_roi_count = sum(1 for r in roi_results if r["trading_roi_percent"] > 0)
    beat_hodl_count = sum(1 for r in roi_results if r["beat_hodl"])
    total_count = len(roi_results)
    avg_price_change = sum(r["price_change_percent"] for r in roi_results) / total_count if total_count > 0 else 0
    avg_trading_roi = sum(r["trading_roi_percent"] for r in roi_results) / total_count if total_count > 0 else 0
    total_investment = sum(r["total_buys"] for r in roi_results)
    total_net_investment = sum(r["net_investment"] for r in roi_results)
    total_profit = sum(r["total_profit"] for r in roi_results)
    overall_roi = (total_profit / total_net_investment * 100) if total_net_investment > 0 else 0
    
    print(f"\n📊 Statistics:")
    print(f"  Profitable Coins: {positive_roi_count}/{total_count} ({positive_roi_count/total_count*100 if total_count > 0 else 0:.1f}%)")
    print(f"  Beat HODL: {beat_hodl_count}/{total_count} ({beat_hodl_count/total_count*100 if total_count > 0 else 0:.1f}%)")
    print(f"  Average Price Change: {avg_price_change:.2f}%")
    print(f"  Average Trading ROI: {avg_trading_roi:.2f}%")
    print(f"  Total Investment: ${total_investment:,.2f}")
    print(f"  Net Investment (In Market): ${total_net_investment:,.2f}")
    print(f"  Total Profit: ${total_profit:,.2f}")
    print(f"  Overall ROI: {overall_roi:.2f}%")
    print("=" * 130)
    
    return roi_results

def save_comparison_data(range="alltime", start_time=None):
    """Generate and save combined comparison data (ROI + vs BTC)
    
    Args:
        range: Time range for data (default: "alltime")
        start_time: Optional unified start time for BTC comparison
    """
    # Generate ROI comparison
    roi_results = print_ticker_roi_comparison(range=range)
    
    # Generate vs BTC comparison
    btc_results = print_ticker_vs_btc_comparison(start_time=start_time, range=range)
    
    if roi_results is None or btc_results is None:
        print("\nError: Failed to generate comparison data")
        return
    
    # Combine results
    combined = {
        "range": range,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "roi_comparison": roi_results,
        "vs_btc_comparison": btc_results
    }
    
    # Create comparison directory if it doesn't exist
    os.makedirs("./comparison", exist_ok=True)
    
    # Save to file
    output_file = f"./comparison/comparison_{range}.json"
    with open(output_file, "w") as f:
        json.dump(combined, f, indent=4)
    
    print(f"\n✅ Comparison data saved to {output_file}")

# ==================== Main Program ====================

if __name__ == "__main__":
    # Display basic profit information
    all_time_profit()
    
    # Display BTC baseline comparison
    print_btc_baseline_comparison()
    
    # Generate and save combined comparison data
    save_comparison_data(range="alltime")
    
    # Method 2: Use specified unified start time
    # unified_start_time = "2025-10-22T00:34:38.959435Z"
    # print_btc_baseline_comparison(start_time=unified_start_time)
    # save_comparison_data(range="alltime", start_time=unified_start_time)
