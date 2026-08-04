import io
import csv
import json
from flask import Flask, jsonify, request, send_from_directory, Response
from ticket_engine import engine

app = Flask(__name__, static_folder=".")

@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(".", path)

@app.route("/api/filters", methods=["GET"])
def get_filter_options():
    """Return available zones, complainees, regions for UI filter dropdowns."""
    refresh = request.args.get("refresh", "false").lower() == "true"
    tickets = engine.fetch_tickets(force_refresh=refresh)

    zones = sorted(list({t["zone"] for t in tickets if t.get("zone") and t["zone"] != "Unknown"}))
    complainees = sorted(list({t["complainee"] for t in tickets if t.get("complainee") and t["complainee"] != "Unknown"}))
    regions = sorted(list({t["region"] for t in tickets if t.get("region") and t["region"] != "Unknown"}))
    dates = sorted(list({engine.parse_opened_date(t["ticket_opened_on"]).strftime("%Y-%m-%d") for t in tickets if engine.parse_opened_date(t["ticket_opened_on"])}), reverse=True)

    return jsonify({
        "zones": zones,
        "complainees": complainees,
        "regions": regions,
        "available_dates": dates
    })

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Return calculated analytics for requested filters."""
    target_date = request.args.get("date", "all")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    zone = request.args.get("zone")
    complainee = request.args.get("complainee")
    region = request.args.get("region")
    status = request.args.get("status")
    refresh = request.args.get("refresh", "false").lower() == "true"

    tickets = engine.fetch_tickets(force_refresh=refresh)
    filtered = engine.filter_tickets(
        tickets,
        target_date=target_date,
        start_date=start_date,
        end_date=end_date,
        zone=zone,
        complainee=complainee,
        region=region,
        status=status
    )

    analytics = engine.analyze_tickets(filtered)
    return jsonify({
        "success": True,
        "filter": {
            "date": target_date,
            "start_date": start_date,
            "end_date": end_date,
            "zone": zone or "All",
            "complainee": complainee or "All",
            "region": region or "All"
        },
        "analytics": analytics
    })

@app.route("/api/tickets", methods=["GET"])
def get_tickets():
    """Return list of tickets matching filters with optional pagination."""
    target_date = request.args.get("date", "all")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    zone = request.args.get("zone")
    complainee = request.args.get("complainee")
    region = request.args.get("region")
    status = request.args.get("status")
    search = request.args.get("search", "").strip().lower()

    tickets = engine.fetch_tickets()
    filtered = engine.filter_tickets(
        tickets,
        target_date=target_date,
        start_date=start_date,
        end_date=end_date,
        zone=zone,
        complainee=complainee,
        region=region,
        status=status
    )

    if search:
        filtered = [
            t for t in filtered
            if search in t.get("ticket_id", "").lower()
            or search in t.get("zone", "").lower()
            or search in t.get("complainee", "").lower()
            or search in t.get("problem_type", "").lower()
            or search in t.get("entity_name", "").lower()
            or search in t.get("location", "").lower()
        ]

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    paginated_tickets = filtered[start_idx:end_idx]

    return jsonify({
        "success": True,
        "total_count": len(filtered),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(filtered) + per_page - 1) // per_page if len(filtered) > 0 else 1,
        "tickets": paginated_tickets
    })

@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    target_date = request.args.get("date", "all")
    zone = request.args.get("zone")
    complainee = request.args.get("complainee")

    tickets = engine.fetch_tickets()
    filtered = engine.filter_tickets(tickets, target_date=target_date, zone=zone, complainee=complainee)

    output = io.StringIO()
    if filtered:
        headers = ["ticket_id", "status", "ticket_opened_on", "ticket_closed_on", "zone", "ward", "region", "complainee", "problem_type", "priority", "assignee", "entity_name", "location"]
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(filtered)

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=ticket_report_{target_date}.csv"}
    )

if __name__ == "__main__":
    print("Starting BBMP Ticket Analytics Web Server at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
