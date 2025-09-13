import requests
from datetime import datetime
from flask import current_app
from dotenv import load_dotenv, dotenv_values



def _to_iso8601(date_str: str, *, end_of_day: bool = False, dayfirst: bool = False) -> str:
    """
    Accepts user dates like '12/03/2025' and returns ISO8601 '2025-12-03T00:00:00Z'.
    By default interprets as MM/DD/YYYY. Set dayfirst=True to allow DD/MM/YYYY.
    Also supports 'YYYY-MM-DD', 'YYYY/MM/DD', 'MM-DD-YYYY', 'DD-MM-YYYY'.
    """
    s = date_str.strip()
    # Try formats in an order that matches North American defaults, with an option for day-first.
    fmts = ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%Y/%m/%d"]
    if dayfirst:
        fmts = ["%d/%m/%Y", "%d-%m-%Y"] + fmts
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"Unrecognized date format: {date_str!r}")

    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    else:
        dt = dt.replace(hour=0, minute=0, second=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_latest_prices(symbol):
    load_dotenv()
    url = f"https://data.alpaca.markets/v2/stocks/bars/latest?symbols={symbol}"

    #obv dont leave the api key out in the open, but for now, for testing purposes, keep it here. 

    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": current_app.config["APCA_API_KEY_ID"],
        "APCA-API-SECRET-KEY": current_app.config["APCA_API_SECRET_KEY"]
    }
    response = requests.get(url, headers=headers)
    return response.json()


def get_prices(symbol, start, end, timeframe="1Day"):
    load_dotenv()
    start = _to_iso8601(start, end_of_day=False)
    end = _to_iso8601(end, end_of_day=True)
    url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbol}&timeframe={timeframe}&start={start}&end={end}&limit=1000&adjustment=raw&feed=sip&sort=asc"

    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": current_app.config["APCA_API_KEY_ID"],
        "APCA-API-SECRET-KEY": current_app.config["APCA_API_SECRET_KEY"]
    }

    response = requests.get(url, headers=headers)
    return response.json()



