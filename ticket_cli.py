#!/usr/bin/env python3
"""
CLI Tool for Daily Ticket Analytics (Schnell IoT / BBMP Firestore)
"""

import argparse
import json
import csv
import sys
from ticket_engine import engine
from config import Config

def print_summary_report(analytics: dict, date_info: str):
    print("\n" + "=" * 65)
    print(f"       SCHNELL IOT / BBMP DAILY TICKET ANALYTICS REPORT")
    print(f"       Filter / Period: {date_info}")
    print(f"       (Note: Automated 'Auto' tickets are excluded)")
    print("=" * 65)
    print(f"  --- TICKETS SUMMARY (RAISED FROM JULY 1ST TO DATE) ---")
    print(f"  Raised (From July 1) : {analytics.get('july1_total_tickets', 0)}")
    print(f"  Open (From July 1)   : {analytics.get('july1_open_tickets', 0)} ({analytics.get('july1_open_slc_panels', 0)} SLC Panels, {analytics.get('july1_open_lamps', 0)} Lamps)")
    print(f"  Closed (From July 1) : {analytics.get('july1_closed_tickets', 0)}")
    print(f"  Resolution Rate      : {analytics.get('july1_resolution_rate_percent', 0.0)}%")
    print("-" * 65)
    print(f"  --- PERIOD OVERVIEW ({date_info}) ---")
    print(f"  Total Raised Tickets : {analytics['total_tickets']}")
    print(f"  Open / Active        : {analytics['open_tickets']} ({analytics.get('open_slc_panels', 0)} SLC Panels, {analytics.get('open_lamps', 0)} Lamps)")
    print(f"  Closed / Resolved    : {analytics['closed_tickets']}")
    print(f"  Other Statuses       : {analytics['other_tickets']}")
    print(f"  Resolution Rate      : {analytics['resolution_rate_percent']}%")
    print("-" * 65)

    print("\n--- ZONE-WISE BREAKDOWN ---")
    print(f"{'Zone':<30} | {'Total':<7} | {'Open':<6} | {'Closed':<7}")
    print("-" * 65)
    for zone_name, stats in list(analytics["zone_breakdown"].items())[:15]:
        print(f"{zone_name[:30]:<30} | {stats['total']:<7} | {stats['open']:<6} | {stats['closed']:<7}")
    if len(analytics["zone_breakdown"]) > 15:
        print(f"... and {len(analytics['zone_breakdown']) - 15} more zones.")

    print("\n--- COMPLAINEE-WISE BREAKDOWN ---")
    print(f"{'Complainee':<30} | {'Total':<7} | {'Open':<6} | {'Closed':<7}")
    print("-" * 65)
    for comp_name, stats in list(analytics["complainee_breakdown"].items())[:15]:
        print(f"{comp_name[:30]:<30} | {stats['total']:<7} | {stats['open']:<6} | {stats['closed']:<7}")
    if len(analytics["complainee_breakdown"]) > 15:
        print(f"... and {len(analytics['complainee_breakdown']) - 15} more complainees.")

    print("\n--- TOP PROBLEM TYPES ---")
    print(f"{'Problem Type':<40} | {'Count':<7}")
    print("-" * 65)
    for prob, count in list(analytics["problem_type_breakdown"].items())[:10]:
        print(f"{prob[:40]:<40} | {count:<7}")

    print("=" * 65 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Fetch and analyze daily ticket data from Firestore.")
    parser.add_argument("-d", "--date", type=str, default=Config.DEFAULT_REPORT_PERIOD, help="Target date ('today', 'yesterday', 'YYYY-MM-DD', or 'all')")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("-z", "--zone", type=str, help="Filter by specific Zone")
    parser.add_argument("-c", "--complainee", type=str, help="Filter by specific Complainee")
    parser.add_argument("-l", "--limit", type=int, help="Limit total raw tickets fetched from database")
    parser.add_argument("--list", action="store_true", help="Print detailed ticket list in terminal")
    parser.add_argument("-e", "--export", type=str, help="Path to export report (JSON or CSV)")
    parser.add_argument("--full", action="store_true", help="Include full raw tickets list in JSON export (default is analytics summary only)")
    parser.add_argument("--refresh", action="store_true", help="Force refresh live ticket data directly from Firestore")

    args = parser.parse_args()

    tickets = engine.fetch_tickets(limit=args.limit, force_refresh=args.refresh)
    filtered = engine.filter_tickets(
        tickets,
        target_date=args.date,
        start_date=args.start_date,
        end_date=args.end_date,
        zone=args.zone,
        complainee=args.complainee
    )

    analytics = engine.analyze_tickets(filtered, full_context_tickets=tickets)
    date_str = args.date
    if args.start_date or args.end_date:
        date_str = f"{args.start_date or 'Start'} to {args.end_date or 'End'}"

    print_summary_report(analytics, date_str)

    if args.list:
        print("\n--- DETAILED BBMP TICKET RECORDS ---")
        print(f"{'Ticket ID':<12} | {'Status':<8} | {'Opened On':<19} | {'Zone':<20} | {'Complainee':<12} | {'Problem Type':<25}")
        print("-" * 105)
        for t in filtered:
            print(f"{t.get('ticket_id', ''):<12} | {t.get('status', ''):<8} | {t.get('ticket_opened_on', ''):<19} | {t.get('zone', '')[:20]:<20} | {t.get('complainee', '')[:12]:<12} | {t.get('problem_type', '')[:25]:<25}")
        print("-" * 105 + "\n")

    if args.export:
        export_path = args.export
        if export_path.endswith(".json"):
            export_payload = {"analytics": analytics}
            if hasattr(args, "full") and args.full:
                export_payload["tickets"] = filtered
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_payload, f, indent=2)
            print(f"Exported summary analytics to {export_path} ({len(json.dumps(export_payload))} bytes)")
        elif export_path.endswith(".csv"):
            if filtered:
                headers = list(filtered[0].keys())
                with open(export_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(filtered)
                print(f"Exported {len(filtered)} tickets to CSV: {export_path}")

if __name__ == "__main__":
    main()
