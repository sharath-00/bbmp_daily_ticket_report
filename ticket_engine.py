import requests
import json
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("TicketEngine")

PROJECT_ID = "schnelliot-380113"
DATABASE_ID = "smartlights"
COLLECTION_ID = "tickets"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/{DATABASE_ID}/documents:runQuery"

def extract_field_val(fields_dict: dict, field_name: str, default: Any = "") -> Any:
    """Extract string/number/boolean values from Firestore REST response field mapping."""
    if not fields_dict or field_name not in fields_dict:
        return default
    val_obj = fields_dict[field_name]
    if "stringValue" in val_obj:
        return val_obj["stringValue"]
    elif "booleanValue" in val_obj:
        return val_obj["booleanValue"]
    elif "doubleValue" in val_obj:
        return float(val_obj["doubleValue"])
    elif "integerValue" in val_obj:
        return int(val_obj["integerValue"])
    elif "arrayValue" in val_obj:
        arr = val_obj["arrayValue"].get("values", [])
        return [str(v.get("stringValue", v)) for v in arr]
    elif "mapValue" in val_obj:
        return val_obj["mapValue"].get("fields", {})
    return default

def parse_ticket_document(doc: dict) -> dict:
    """Convert raw Firestore document to cleaned Python dict."""
    doc_name = doc.get("name", "")
    doc_id = doc_name.split("/")[-1] if doc_name else ""
    fields = doc.get("fields", {})

    ticket_id = str(extract_field_val(fields, "ticket_id", default=doc_id) or doc_id)

    region = str(extract_field_val(fields, "region", default="Unknown") or "Unknown")
    zone = str(extract_field_val(fields, "zone", default="Unknown") or "Unknown")
    ward = str(extract_field_val(fields, "ward", default="Unknown") or "Unknown")
    complainee = str(extract_field_val(fields, "complainee", default="Unknown") or "Unknown")
    entity_name = str(extract_field_val(fields, "entity_name", default="") or "")
    entity_type = str(extract_field_val(fields, "entity_type", default="") or "")
    problem_type = str(extract_field_val(fields, "problem_type", default="Unspecified") or "Unspecified")
    status = str(extract_field_val(fields, "status", default="Open") or "Open")
    priority = str(extract_field_val(fields, "priority", default="Minor") or "Minor")
    assignee = str(extract_field_val(fields, "assignee", default="Unassigned") or "Unassigned")
    customer = str(extract_field_val(fields, "customer", default="") or "")
    location = str(extract_field_val(fields, "location", default="") or "")

    ticket_opened_on = str(extract_field_val(fields, "ticket_opened_on", default="") or "")
    ticket_closed_on = str(extract_field_val(fields, "ticket_closed_on", default="") or "")

    return {
        "id": doc_id,
        "ticket_id": ticket_id.strip(),
        "region": region.strip(),
        "zone": zone.strip(),
        "ward": ward.strip(),
        "complainee": complainee.strip(),
        "entity_name": entity_name.strip(),
        "entity_type": entity_type.strip(),
        "problem_type": problem_type.strip(),
        "status": status.strip(),
        "priority": priority.strip(),
        "assignee": assignee.strip(),
        "customer": customer.strip(),
        "location": location.strip(),
        "ticket_opened_on": ticket_opened_on.strip(),
        "ticket_closed_on": ticket_closed_on.strip(),
        "raw_create_time": str(doc.get("createTime", ""))
    }

def is_bbmp_ticket(ticket: dict) -> bool:
    """
    Returns True ONLY for BBMP project tickets with region EAST or Bommanahalli,
    excluding 5B Innovations, Auto tickets, and non-BBMP projects.
    """
    customer = str(ticket.get("customer", "")).strip()
    region = str(ticket.get("region", "")).strip().lower()
    complainee = str(ticket.get("complainee", "")).strip().lower()

    # Exclude 5B Innovations
    if "5b" in customer.lower():
        return False

    # Exclude Auto tickets
    if complainee == "auto":
        return False

    # Strictly include EAST and Bommanahalli / Bommanahali regions
    valid_bbmp_regions = ["east", "bommanahali", "bommanahalli"]
    if region in valid_bbmp_regions:
        return True

    return False

def is_slc_panel_ticket(ticket: dict) -> bool:
    """
    Returns True if the ticket is for an SLC panel asset.
    All other tickets are categorized as Lamp tickets per specification.
    """
    et = str(ticket.get("entity_type", "")).strip().lower()
    en = str(ticket.get("entity_name", "")).strip().lower()
    if "slc" in et or "panel" in et or en.startswith("ssc") or "slc" in en or "panel" in en:
        return True
    return False

class TicketEngine:
    def __init__(self, cache_file: str = "tickets_cache.json"):
        self._cached_tickets: List[dict] = []
        self._last_fetch_time: Optional[datetime] = None
        self._cache_file = cache_file
        self._load_disk_cache()

    def _load_disk_cache(self):
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cached_tickets = data.get("tickets", [])
                    ts = data.get("timestamp")
                    if ts:
                        self._last_fetch_time = datetime.fromisoformat(ts)
                    logger.info(f"Loaded {len(self._cached_tickets)} ticket records from disk cache '{self._cache_file}'.")
        except Exception as e:
            logger.warning(f"Could not load disk cache: {e}")

    def _save_disk_cache(self):
        try:
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "tickets": self._cached_tickets
                }, f)
            logger.info(f"Saved {len(self._cached_tickets)} ticket records to disk cache '{self._cache_file}'.")
        except Exception as e:
            logger.warning(f"Could not save disk cache: {e}")

    def fetch_tickets(self, limit: Optional[int] = None, force_refresh: bool = False) -> List[dict]:
        """Fetch ticket documents using paginated Firestore runQuery with BBMP server-side filter."""
        if self._cached_tickets and not force_refresh:
            logger.info(f"Using cached ticket data ({len(self._cached_tickets)} records)")
            return self._cached_tickets[:limit] if limit else self._cached_tickets

        logger.info("Fetching BBMP ticket data directly from Firebase Firestore...")
        structured_query = {
            "from": [{"collectionId": COLLECTION_ID}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "region"},
                    "op": "IN",
                    "value": {
                        "arrayValue": {
                            "values": [
                                {"stringValue": "EAST"},
                                {"stringValue": "East"},
                                {"stringValue": "east"},
                                {"stringValue": "Bommanahali"},
                                {"stringValue": "Bommanahalli"},
                                {"stringValue": "bommanahali"},
                                {"stringValue": "bommanahalli"}
                            ]
                        }
                    }
                }
            },
            "orderBy": [{"field": {"fieldPath": "__name__"}, "direction": "ASCENDING"}],
            "limit": 1000
        }

        all_tickets = []
        last_doc_name = None
        page = 1

        while True:
            if limit and len(all_tickets) >= limit:
                break

            if limit:
                remaining = limit - len(all_tickets)
                structured_query["limit"] = min(1000, remaining)
                if structured_query["limit"] <= 0:
                    break

            if last_doc_name:
                structured_query["startAt"] = {
                    "values": [{"referenceValue": last_doc_name}],
                    "before": False
                }

            payload = {"structuredQuery": structured_query}
            try:
                resp = requests.post(FIRESTORE_URL, json=payload, timeout=30)
                if resp.status_code != 200:
                    logger.error(f"Firestore API HTTP error {resp.status_code}: {resp.text}")
                    break
            except Exception as e:
                logger.error(f"Error querying Firestore API: {e}")
                break

            results = resp.json()
            batch_docs = [item["document"] for item in results if "document" in item]
            if not batch_docs:
                break

            for doc in batch_docs:
                parsed = parse_ticket_document(doc)
                if is_bbmp_ticket(parsed):
                    all_tickets.append(parsed)

            if len(batch_docs) < structured_query["limit"]:
                break

            last_doc_name = batch_docs[-1]["name"]
            page += 1

        logger.info(f"Successfully fetched {len(all_tickets)} BBMP ticket records.")
        self._cached_tickets = all_tickets
        self._last_fetch_time = datetime.now()
        self._save_disk_cache()
        return self._cached_tickets[:limit] if limit else self._cached_tickets

    @staticmethod
    def parse_opened_date(opened_str: str) -> Optional[date]:
        """Extract Python date object from ticket_opened_on string."""
        if not opened_str:
            return None
        # Handle format: "YYYY-MM-DD HH:MM:SS" or ISO strings
        clean_str = opened_str.split(".")[0].strip()
        try:
            return datetime.strptime(clean_str[:10], "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                return None

    def filter_tickets(
        self,
        tickets: List[dict],
        target_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        zone: Optional[str] = None,
        complainee: Optional[str] = None,
        region: Optional[str] = None,
        status: Optional[str] = None,
        bbmp_only: bool = True,
        exclude_auto: bool = True
    ) -> List[dict]:
        """Filter list of tickets by date/range, zone, complainee, region, status, BBMP project restriction, and Auto ticket exclusion."""
        filtered = tickets

        # Exclude Auto tickets
        if exclude_auto:
            filtered = [t for t in filtered if str(t.get("complainee", "")).strip().lower() != "auto"]

        # Apply strict BBMP Project Filter
        if bbmp_only:
            filtered = [t for t in filtered if is_bbmp_ticket(t)]

        # Resolve date shortcuts
        today_date = date.today()
        resolved_start: Optional[date] = None
        resolved_end: Optional[date] = None

        if target_date:
            if target_date.lower() == "today":
                resolved_start = today_date
                resolved_end = today_date
            elif target_date.lower() == "yesterday":
                resolved_start = today_date - timedelta(days=1)
                resolved_end = today_date - timedelta(days=1)
            elif target_date.lower() != "all":
                try:
                    parsed = datetime.strptime(target_date, "%Y-%m-%d").date()
                    resolved_start = parsed
                    resolved_end = parsed
                except ValueError:
                    pass

        if start_date and not resolved_start:
            try:
                resolved_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                pass

        if end_date and not resolved_end:
            try:
                resolved_end = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                pass

        res = []
        for t in filtered:
            # Date filter
            if resolved_start or resolved_end:
                t_date = self.parse_opened_date(t.get("ticket_opened_on", ""))
                if not t_date:
                    continue
                if resolved_start and t_date < resolved_start:
                    continue
                if resolved_end and t_date > resolved_end:
                    continue

            # Zone filter
            if zone and zone.lower() != "all":
                if t.get("zone", "").lower() != zone.lower():
                    continue

            # Complainee filter
            if complainee and complainee.lower() != "all":
                if t.get("complainee", "").lower() != complainee.lower():
                    continue

            # Region filter
            if region and region.lower() != "all":
                if t.get("region", "").lower() != region.lower():
                    continue

            # Status filter
            if status and status.lower() != "all":
                if t.get("status", "").lower() != status.lower():
                    continue

            res.append(t)

        return res

    def analyze_tickets(self, tickets: List[dict], exclude_auto: bool = True, full_context_tickets: Optional[List[dict]] = None) -> dict:
        """Perform analytics calculations on tickets list (ignoring Auto tickets by default)."""
        if exclude_auto:
            tickets = [t for t in tickets if str(t.get("complainee", "")).strip().lower() != "auto"]
            if full_context_tickets:
                full_context_tickets = [t for t in full_context_tickets if str(t.get("complainee", "")).strip().lower() != "auto"]

        trend_source_tickets = full_context_tickets if full_context_tickets is not None else tickets

        total_raised = len(tickets)
        open_count = 0
        closed_count = 0
        other_count = 0

        open_slc_panels = 0
        open_lamps = 0

        today_date = date.today()
        today_tickets_count = 0
        today_open_count = 0
        today_closed_count = 0
        today_open_slc_panels = 0
        today_open_lamps = 0

        status_counts: Dict[str, int] = {}
        zone_breakdown: Dict[str, Dict[str, int]] = {}
        complainee_breakdown: Dict[str, Dict[str, int]] = {}
        problem_counts: Dict[str, int] = {}
        priority_counts: Dict[str, int] = {}
        region_counts: Dict[str, int] = {}
        daily_trend: Dict[str, int] = {}

        past_7_dates = [today_date - timedelta(days=i) for i in range(6, -1, -1)]
        past_7_set = {d.strftime("%Y-%m-%d") for d in past_7_dates}

        for t in tickets:
            st = t.get("status", "Open") or "Open"
            st_lower = st.lower()
            status_counts[st] = status_counts.get(st, 0) + 1

            if any(term in st_lower for term in ["closed", "resolved", "duplicate"]):
                closed_count += 1
                is_closed = True
                is_open = False
            elif any(term in st_lower for term in ["open", "in progress", "pending", "assigned", "waiting"]):
                open_count += 1
                is_open = True
                is_closed = False
            else:
                other_count += 1
                is_open = False
                is_closed = False

            # Check asset type for open tickets
            if is_open:
                if is_slc_panel_ticket(t):
                    open_slc_panels += 1
                else:
                    open_lamps += 1

            # Today stats by opened date
            t_date = self.parse_opened_date(t.get("ticket_opened_on", ""))
            if t_date and t_date == today_date:
                today_tickets_count += 1
                if is_open:
                    today_open_count += 1
                    if is_slc_panel_ticket(t):
                        today_open_slc_panels += 1
                    else:
                        today_open_lamps += 1
                elif is_closed:
                    today_closed_count += 1

            # Zone breakdown
            z = t.get("zone", "Unknown") or "Unknown"
            if z not in zone_breakdown:
                zone_breakdown[z] = {"total": 0, "open": 0, "closed": 0, "other": 0}
            zone_breakdown[z]["total"] += 1
            if is_open:
                zone_breakdown[z]["open"] += 1
            elif is_closed:
                zone_breakdown[z]["closed"] += 1
            else:
                zone_breakdown[z]["other"] += 1

            # Complainee breakdown
            c = t.get("complainee", "Unknown") or "Unknown"
            if c not in complainee_breakdown:
                complainee_breakdown[c] = {"total": 0, "open": 0, "closed": 0, "other": 0}
            complainee_breakdown[c]["total"] += 1
            if is_open:
                complainee_breakdown[c]["open"] += 1
            elif is_closed:
                complainee_breakdown[c]["closed"] += 1
            else:
                complainee_breakdown[c]["other"] += 1

            # Problem type
            prob = t.get("problem_type", "Unspecified") or "Unspecified"
            problem_counts[prob] = problem_counts.get(prob, 0) + 1

            # Priority
            prio = t.get("priority", "Minor") or "Minor"
            priority_counts[prio] = priority_counts.get(prio, 0) + 1

            # Region
            reg = t.get("region", "Unknown") or "Unknown"
            region_counts[reg] = region_counts.get(reg, 0) + 1

        # Calculate Past 7 Days Clustered Trend using full_context_tickets (if provided) or tickets
        past_7_dates = [today_date - timedelta(days=i) for i in range(6, -1, -1)]
        past_7_trend = {d.strftime("%Y-%m-%d"): {"open": 0, "closed": 0, "total": 0} for d in past_7_dates}

        for t in trend_source_tickets:
            t_date = self.parse_opened_date(t.get("ticket_opened_on", ""))
            if t_date:
                d_str = t_date.strftime("%Y-%m-%d")
                if d_str in past_7_set:
                    daily_trend[d_str] = daily_trend.get(d_str, 0) + 1
                if d_str in past_7_trend:
                    st_lower = (t.get("status", "Open") or "Open").lower()
                    past_7_trend[d_str]["total"] += 1
                    if any(term in st_lower for term in ["closed", "resolved", "duplicate"]):
                        past_7_trend[d_str]["closed"] += 1
                    elif any(term in st_lower for term in ["open", "in progress", "pending", "assigned", "waiting"]):
                        past_7_trend[d_str]["open"] += 1

        july1_date = date(2026, 7, 1)
        july1_tickets_count = 0
        july1_open_count = 0
        july1_closed_count = 0
        july1_open_slc_panels = 0
        july1_open_lamps = 0

        for t in trend_source_tickets:
            t_date = self.parse_opened_date(t.get("ticket_opened_on", ""))
            if t_date and t_date >= july1_date:
                st_lower = (t.get("status", "Open") or "Open").lower()
                is_closed_t = any(term in st_lower for term in ["closed", "resolved", "duplicate"])
                is_open_t = any(term in st_lower for term in ["open", "in progress", "pending", "assigned", "waiting"])

                july1_tickets_count += 1
                if is_open_t:
                    july1_open_count += 1
                    if is_slc_panel_ticket(t):
                        july1_open_slc_panels += 1
                    else:
                        july1_open_lamps += 1
                elif is_closed_t:
                    july1_closed_count += 1

        # Unresolved Aging Analysis (> 7 Days & > 30 Days)
        unresolved_over_7_list = []
        unresolved_over_30_list = []

        for t in trend_source_tickets:
            st_lower = (t.get("status", "Open") or "Open").lower()
            is_open_t = any(term in st_lower for term in ["open", "in progress", "pending", "assigned", "waiting"])
            if is_open_t:
                t_date = self.parse_opened_date(t.get("ticket_opened_on", ""))
                if t_date:
                    age_days = (today_date - t_date).days
                    t_enriched = dict(t)
                    t_enriched["days_unresolved"] = age_days
                    if age_days > 30:
                        t_enriched["aging_category"] = "> 30 Days"
                        unresolved_over_30_list.append(t_enriched)
                        unresolved_over_7_list.append(t_enriched)
                    elif age_days > 7:
                        t_enriched["aging_category"] = "7 - 30 Days"
                        unresolved_over_7_list.append(t_enriched)
                    else:
                        t_enriched["aging_category"] = "< 7 Days"

        # Sort by longest pending first
        unresolved_over_7_list.sort(key=lambda x: x.get("days_unresolved", 0), reverse=True)
        unresolved_over_30_list.sort(key=lambda x: x.get("days_unresolved", 0), reverse=True)

        resolution_rate = round((closed_count / total_raised * 100), 2) if total_raised > 0 else 0.0
        today_res_rate = round((today_closed_count / today_tickets_count * 100), 2) if today_tickets_count > 0 else 0.0
        july1_res_rate = round((july1_closed_count / july1_tickets_count * 100), 2) if july1_tickets_count > 0 else 0.0

        # Sort breakdowns by total descending
        sorted_zones = dict(sorted(zone_breakdown.items(), key=lambda item: item[1]["total"], reverse=True))
        sorted_complainees = dict(sorted(complainee_breakdown.items(), key=lambda item: item[1]["total"], reverse=True))
        sorted_problems = dict(sorted(problem_counts.items(), key=lambda item: item[1], reverse=True))

        return {
            "total_tickets": total_raised,
            "open_tickets": open_count,
            "open_slc_panels": open_slc_panels,
            "open_lamps": open_lamps,
            "closed_tickets": closed_count,
            "other_tickets": other_count,
            "resolution_rate_percent": resolution_rate,
            "today_total_tickets": today_tickets_count,
            "today_open_tickets": today_open_count,
            "today_open_slc_panels": today_open_slc_panels,
            "today_open_lamps": today_open_lamps,
            "today_closed_tickets": today_closed_count,
            "today_resolution_rate_percent": today_res_rate,
            "july1_total_tickets": july1_tickets_count,
            "july1_open_tickets": july1_open_count,
            "july1_open_slc_panels": july1_open_slc_panels,
            "july1_open_lamps": july1_open_lamps,
            "july1_closed_tickets": july1_closed_count,
            "july1_resolution_rate_percent": july1_res_rate,
            "unresolved_over_7_days_count": len(unresolved_over_7_list),
            "unresolved_over_30_days_count": len(unresolved_over_30_list),
            "unresolved_over_7_days_tickets": unresolved_over_7_list,
            "unresolved_over_30_days_tickets": unresolved_over_30_list,
            "status_breakdown": status_counts,
            "zone_breakdown": sorted_zones,
            "complainee_breakdown": sorted_complainees,
            "problem_type_breakdown": sorted_problems,
            "priority_breakdown": priority_counts,
            "region_breakdown": region_counts,
            "daily_trend": dict(sorted(daily_trend.items())),
            "past_7_days_trend": past_7_trend
        }

# Global singleton instance for easy import
engine = TicketEngine()
