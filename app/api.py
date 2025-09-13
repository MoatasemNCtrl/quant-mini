from flask import Blueprint, request, jsonify
from .services.market_data import get_latest_prices, get_prices
from .utils.factors import compute_factors
from .models.cache import get_or_update


api_bp = Blueprint("api",__name__)

@api_bp.route("/status")
def status(): 
    return {"status": "ok"}


# Example stubs you can wire up later:
@api_bp.get("/prices/<ticker>")
def prices(ticker):
    data = get_latest_prices(ticker)   # implement in services/market_data.py
    # return jsonify(data)
    return jsonify({"ticker": ticker, "data": data})

    
@api_bp.get("/factors/<symbol>")
def factors(symbol):
    timeframe = request.args.get("timeframe", "1Day")
    start = request.args.get("start")
    end = request.args.get("end")
    return_type = request.args.get("as", "series")

    kind = f"factors:{timeframe}:{start or 'None'}:{end or 'None'}:{return_type}"

    def compute_fn():
        prices = get_prices(symbol, timeframe=timeframe, start=start, end=end)
        return compute_factors(prices, return_type=return_type)

    data = get_or_update(symbol, kind, compute_fn)
    return jsonify(data)