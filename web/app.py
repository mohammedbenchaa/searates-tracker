"""
SeaRates Tracker — Web App
===========================
Flask web application for container tracking with interactive map.

Run:
    python app.py
    # → http://0.0.0.0:8787/tracking
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import searates_tracker
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify, Blueprint

from searates_tracker import SeaRatesClient
from searates_tracker.exceptions import (
    SeaRatesException,
    SeaRatesNotFoundError,
    SeaRatesRateLimitError,
)

# Create blueprint with /tracking prefix
tracking_bp = Blueprint("tracking", __name__, url_prefix="/tracking")

app = Flask(__name__)
client = SeaRatesClient()


@tracking_bp.route("/")
def index():
    """Main page."""
    return render_template("index.html")


@tracking_bp.route("/api/track", methods=["POST"])
def track():
    """Track a container/shipment."""
    data = request.get_json() or {}
    number = (data.get("number") or "").strip().upper()
    tracking_type = data.get("type", "sea")  # sea, air, parcel, rail, road

    if not number:
        return jsonify({"success": False, "error": "الرجاء إدخال رقم الحاوية أو التتبع"}), 400

    try:
        if tracking_type == "sea":
            # Auto-detect carrier from prefix
            carrier = client.find_carrier_by_prefix(number)
            sealine = carrier.scac_codes[0] if carrier else None

            result = client.track_sea(number=number, sealine=sealine, route=True)

            return jsonify({
                "success": result.is_success,
                "type": "sea",
                "data": {
                    "number": result.tracking_number,
                    "carrier": result.sealine_name,
                    "carrier_code": result.sealine,
                    "status": result.status,
                    "from": result.direction_from,
                    "to": result.direction_to,
                    "etd": result.etd,
                    "eta": result.eta,
                    "atd": result.atd,
                    "ata": result.ata,
                    "progress": result.progress,
                    "events": [
                        {
                            "date": e.date,
                            "event": e.event,
                            "location": e.location,
                            "vessel": e.vessel,
                            "voyage": e.voyage,
                            "type": e.transport_type or e.mode,
                            "actual": e.actual,
                        }
                        for e in result.events
                    ],
                    "routes": [
                        {
                            "from": {"name": r.from_name, "country": r.from_country, "locode": r.from_locode},
                            "to": {"name": r.to_name, "country": r.to_country, "locode": r.to_locode},
                            "path": r.path,
                            "atd": r.atd,
                            "eta": r.eta,
                        }
                        for r in result.routes
                    ],
                    "vessels": [
                        {"name": v.name, "imo": v.imo}
                        for v in result.vessels
                    ],
                    "containers": [
                        {"number": c.number, "size_type": c.size_type, "status": c.status}
                        for c in result.containers
                    ],
                    "raw": result._raw,
                }
            })

        elif tracking_type == "air":
            result = client.track_air(number=number)
            return jsonify({
                "success": result.is_success,
                "type": "air",
                "data": {
                    "number": result.tracking_number,
                    "carrier": result.airline_name,
                    "status": result.status,
                    "events": [
                        {"date": e.date, "event": e.event, "location": e.location}
                        for e in result.events
                    ],
                }
            })

        elif tracking_type == "parcel":
            result = client.track_parcel(number=number)
            return jsonify({
                "success": result.is_success,
                "type": "parcel",
                "data": {
                    "number": result.tracking_number,
                    "carrier": result.carrier_name,
                    "carrier_code": result.carrier_code,
                    "status": result.status_message,
                    "events": [
                        {
                            "date": e.date,
                            "event": e.event,
                            "location": e.location,
                            "transport": e.transport_type,
                        }
                        for e in result.events
                    ],
                }
            })

        elif tracking_type == "rail":
            result = client.track_rail(number=number)
            return jsonify({
                "success": result.is_success,
                "type": "rail",
                "data": {
                    "number": result.tracking_number,
                    "status": result.status,
                    "events": [
                        {"date": e.date, "event": e.event, "location": e.location}
                        for e in result.events
                    ],
                }
            })

        else:
            return jsonify({"success": False, "error": "نوع التتبع غير مدعوم"}), 400

    except SeaRatesNotFoundError as e:
        return jsonify({"success": False, "error": f"لم يتم العثور على الشحنة: {e.message}"}), 404
    except SeaRatesRateLimitError as e:
        return jsonify({
            "success": False,
            "error": "تم تجاوز حد الطلبات اليومي. سجل في SeaRates للحصول على API key."
        }), 429
    except SeaRatesException as e:
        return jsonify({"success": False, "error": str(e.message)}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"خطأ غير متوقع: {str(e)}"}), 500


@tracking_bp.route("/api/carriers", methods=["GET"])
def get_carriers():
    """List shipping carriers."""
    query = request.args.get("q", "").strip()
    if query:
        carriers = client.find_carrier(query)
    else:
        carriers = client.get_carriers()

    return jsonify({
        "success": True,
        "count": len(carriers),
        "data": [
            {
                "name": c.name,
                "scac": c.scac_codes,
                "prefixes": c.prefixes,
                "active": c.active,
                "supports": {
                    "containers": c.supports_containers,
                    "bl": c.supports_bl,
                    "booking": c.supports_booking,
                }
            }
            for c in carriers[:50]  # Limit for performance
        ]
    })


# Register blueprint
app.register_blueprint(tracking_bp)


# Also serve at root for convenience
@app.route("/")
@app.route("/tracking")
def root_redirect():
    """Redirect to tracking page."""
    return render_template("index.html")


if __name__ == "__main__":
    print("🚢 SeaRates Tracker Web App")
    print("=" * 40)
    print("🌐 http://0.0.0.0:5050/tracking")
    print("📋 /tracking/api/track — تتبع شحنة (POST)")
    print("📋 /tracking/api/carriers — قائمة الناقلين (GET)")
    print("=" * 40)
    
    app.run(host="0.0.0.0", port=5050, debug=False)
