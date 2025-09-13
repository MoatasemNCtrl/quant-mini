from flask import Blueprint, request, jsonify
from .services.market_data import get_latest_prices, get_prices
from .utils.factors import compute_factors


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

    
@api_bp.get("/factors/<ticker>")
def factors(ticker):
    data = get_prices(ticker, "8/10/2024", "8/15/2024")
    return_type = request.args.get("as", "series")  # ?as=latest or ?as=series
    result = compute_factors(data, return_type=return_type)
    return jsonify(result)