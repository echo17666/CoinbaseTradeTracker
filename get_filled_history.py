import requests
import json
import os

from datetime import datetime, timezone
from utils import build_jwt


def get_filled_history(start_date, end_date=None, incremental=False):
    """Get filled trade history from Coinbase API
    
    Args:
        start_date: Start date string or "alltime"
        end_date: End date string
        incremental: If True, merge with existing data instead of overwriting
    """
    # alltime condition
    isAllTime=False
    if start_date=="alltime":
        isAllTime=True
        start_date="2020-01-01"
        end_date="3020-01-01"
    request_method = "GET"
    request_host   = "api.coinbase.com"
    request_path   = "/api/v3/brokerage/orders/historical/fills"
    uri = f"{request_method} {request_host}{request_path}"
    jwt_token = build_jwt(uri)
    # print(jwt_token)
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    url=f"https://{request_host}{request_path}"

    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

    start_iso = start_dt.isoformat(timespec='microseconds').replace('+00:00', 'Z')
    end_iso = end_dt.isoformat(timespec='microseconds').replace('+00:00', 'Z')
    querystring = {"sort_by":"TRADE_TIME","start_sequence_timestamp":start_iso,"end_sequence_timestamp":end_iso}
    if isAllTime:
        querystring = {"limit":"2000"}
    response = requests.get(url, headers=headers,params=querystring)
    response=response.json()
    
    new_trades=[]
    for item in response.get("fills", []):
        new_trades.append({
            "trade_time": item.get("trade_time"), # ISO 8601 format
            "trade_type": item.get("trade_type"), # "FILL"
            "price": item.get("price"),           # Price per unit
            "size": item.get("size"),             # Quantity traded 
            "product_id": item.get("product_id"), # e.g., "BTC-USD"
            "commission": item.get("commission"), # Commission fee
            "side": item.get("side"),             # "BUY" or "SELL"
        })
    
    # Create directory if it doesn't exist
    os.makedirs("./trade_history", exist_ok=True)
    
    start_date_str = start_dt.strftime("%Y%m%d")
    end_date_str = end_dt.strftime("%Y%m%d")
    
    if isAllTime:
        file_path = f"./trade_history/filled_alltime.json"
        
        # If incremental mode and file exists, merge with existing data
        if incremental and os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    existing_trades = json.load(f)
                
                # Create a set of existing trade identifiers (time + product_id + side + price)
                existing_ids = {
                    (t["trade_time"], t["product_id"], t["side"], t["price"])
                    for t in existing_trades
                }
                
                # Add only new trades that don't exist
                trades_added = 0
                for trade in new_trades:
                    trade_id = (trade["trade_time"], trade["product_id"], trade["side"], trade["price"])
                    if trade_id not in existing_ids:
                        existing_trades.append(trade)
                        trades_added += 1
                
                # Sort by trade_time to maintain chronological order
                existing_trades.sort(key=lambda x: x["trade_time"])
                trade_history = existing_trades
                
                print(f"📊 Incremental update: {trades_added} new trades added, {len(existing_trades)} total trades")
                
            except Exception as e:
                print(f"⚠️  Could not load existing data, using new data only: {e}")
                trade_history = new_trades
        else:
            trade_history = new_trades
            if incremental:
                print(f"📊 First time fetch: {len(trade_history)} trades")
        
        with open(file_path, "w") as f:
            json.dump(trade_history, f, indent=4)
    else:
        with open(f"./trade_history/filled_{start_date_str}_{end_date_str}.json", "w") as f:
            json.dump(new_trades, f, indent=4)
            
    return response

if __name__ == "__main__":
    # Example usage
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    # get_filled_history(start_date, end_date)
    get_filled_history("alltime")
