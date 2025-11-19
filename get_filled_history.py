import requests
import json


from datetime import datetime, timezone
from utils import build_jwt


def get_filled_history(start_date, end_date=None):
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
    trade_history=[]
    for item in response.get("fills", []):
        trade_history.append({
            "trade_time": item.get("trade_time"), # ISO 8601 format
            "trade_type": item.get("trade_type"), # "FILL"
            "price": item.get("price"),           # Price per unit
            "size": item.get("size"),             # Quantity traded 
            "product_id": item.get("product_id"), # e.g., "BTC-USD"
            "commission": item.get("commission"), # Commission fee
            "side": item.get("side"),             # "BUY" or "SELL"
        })
    start_date_str = start_dt.strftime("%Y%m%d")
    end_date_str = end_dt.strftime("%Y%m%d")
    if isAllTime:
        with open(f"./trade_history/filled_alltime.json", "w") as f:
            json.dump(trade_history, f, indent=4)
    else:
        with open(f"./trade_history/filled_{start_date_str}_{end_date_str}.json", "w") as f:
            json.dump(trade_history, f, indent=4)
    return response
if __name__ == "__main__":
    # Example usage
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    # get_filled_history(start_date, end_date)
    get_filled_history("alltime")
