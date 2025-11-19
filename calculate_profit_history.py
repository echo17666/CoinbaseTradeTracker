import json
import os
import requests
from datetime import datetime, timezone
from utils import build_jwt

def get_hold():
    request_method = "GET"
    request_host   = "api.coinbase.com"
    request_path   = "/api/v3/brokerage/accounts"
    uri = f"{request_method} {request_host}{request_path}"
    jwt_token = build_jwt(uri)
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    url=f"https://{request_host}{request_path}"
    response = requests.get(url, headers=headers)
    response=response.json()
    hold_result={}
    for account in response.get("accounts", []):
        if float(account.get("available_balance", {}).get("value",0))+float(account.get("hold", {}).get("value",0))>0:
            hold_result[account.get("currency")]={
                "ticker": account.get("currency"),
                "hold": round(float(account.get("available_balance", {}).get("value",0))+float(account.get("hold", {}).get("value",0)), 8),
            }
    return hold_result

def get_price(ticker):
    request_method = "GET"
    request_host   = "api.coinbase.com"
    request_path   = f"/api/v3/brokerage/products/{ticker}"
    uri = f"{request_method} {request_host}{request_path}"
    jwt_token = build_jwt(uri)
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    url=f"https://{request_host}{request_path}"
    response = requests.get(url, headers=headers)
    response=response.json()
    price = float(response.get("price",0))
    return price

def calculate_profit(range,ticker,hold):
    buys = []
    sells = []
    buy_sizes = []
    sell_sizes = []
    
    with open(f"./trade_history/filled_{range}.json", "r") as f:
        trade_history = json.load(f)
        for trade in trade_history:
            if trade["product_id"] == ticker:
                if trade["side"] == "BUY":
                    buys.append(float(trade["price"]) * float(trade["size"]) + float(trade["commission"]))
                    buy_sizes.append(float(trade["size"]))
                elif trade["side"] == "SELL":
                    sells.append(float(trade["price"]) * float(trade["size"]) - float(trade["commission"]))
                    sell_sizes.append(float(trade["size"]))
    
    total_buys = sum(buys)
    total_sells = sum(sells)
    total_buy_size = sum(buy_sizes)
    total_sell_size = sum(sell_sizes)
    
    if total_sell_size > 0:
        avg_buy_price = total_buys / total_buy_size if total_buy_size > 0 else 0
        realized_cost = avg_buy_price * total_sell_size
        realized_profit = total_sells - realized_cost
    else:
        realized_profit = 0
    
    current_price = get_price(ticker) if hold > 0 else 0
    total_holds_value = hold * current_price
    if hold > 0 and total_buy_size > 0:
        avg_buy_price = total_buys / total_buy_size
        unrealized_cost = avg_buy_price * hold
        unrealized_profit = total_holds_value - unrealized_cost
    else:
        unrealized_profit = 0
    
    total_profit = realized_profit + unrealized_profit

    return {
        "ticker": ticker,
        "total_buys": round(float(total_buys), 8),
        "total_sells": round(float(total_sells), 8),
        "hold_amount": round(float(hold), 8),
        "realized_profit": round(float(realized_profit), 8),
        "unrealized_profit": round(float(unrealized_profit), 8),
        "total_profit": round(float(total_profit), 8),
    }

def all_time_profit():
    range="alltime"
    all_tickers=[]
    hold=get_hold()
    with open(f"./trade_history/filled_alltime.json", "r") as f:
        trade_history = json.load(f)
        tickers = set(trade["product_id"] for trade in trade_history)
        for ticker in tickers:
            if ticker.endswith("-USDC") or ticker.endswith("-USD"):
                coin = ticker.split("-")[0]
                all_tickers.append(coin)
    all_tickers = list(set(all_tickers).union(hold.keys()))
    
    results=[]
    total_realized = 0
    total_unrealized = 0
    total_profit = 0
    
    print(f"\n{'Coin':<10} {'Realized':<15} {'Unrealized':<15} {'Total':<15}")
    print("-" * 60)
    
    for coin in all_tickers:
        ticker=f"{coin}-USDC"
        result=calculate_profit(range,ticker,hold.get(coin,{}).get("hold",0))
        results.append(result)
        
        print(f"{coin:<10} ${result['realized_profit']:>13.2f} ${result['unrealized_profit']:>13.2f} ${result['total_profit']:>13.2f}")
        
        total_realized += result["realized_profit"]
        total_unrealized += result["unrealized_profit"]
        total_profit += result["total_profit"]
    
    print("-" * 60)
    print(f"{'TOTAL':<10} ${total_realized:>13.2f} ${total_unrealized:>13.2f} ${total_profit:>13.2f}")
    
    with open(f"./profit_history/profit_{range}.json", "w") as f:
        json.dump(results, f, indent=4)

    
    
if __name__ == "__main__":
    range="20250101_20250131"
    all_time_profit()
                
        
