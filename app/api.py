from flask import Blueprint, request, jsonify

api_bp = Blueprint("api",__name__)

@api_bp.route("/status")
def status(): 
    return {"status": "ok"}


