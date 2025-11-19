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
    with open(f"./trade_history/filled_{range}.json", "r") as f:
        trade_history = json.load(f)
        for trade in trade_history:
            if trade["product_id"] == ticker:
                if trade["side"] == "BUY":
                    buys.append(float(trade["price"]) * float(trade["size"]) + float(trade["commission"]))
                elif trade["side"] == "SELL":
                    sells.append(float(trade["price"]) * float(trade["size"]) - float(trade["commission"]))
    total_buys = sum(buys)
    total_sells = sum(sells)
    total_holds= hold * get_price(ticker)
    profit = total_sells + total_holds - total_buys

    return {
        "ticker": ticker,
        "total_buys": round(float(total_buys), 8),
        "total_sells": round(float(total_sells), 8),
        "total_holds": round(float(total_holds), 8),
        "profit": round(float(profit), 8)
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
    for coin in all_tickers:
        ticker=f"{coin}-USDC"
        result=calculate_profit(range,ticker,hold.get(coin,{}).get("hold",0))
        results.append(result)
    with open(f"./profit_history/profit_{range}.json", "w") as f:
        json.dump(results, f, indent=4)

    
    
if __name__ == "__main__":
    range="20250101_20250131"
    all_time_profit()
                
        
