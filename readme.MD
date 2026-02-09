#readme.MD
#!/usr/bin/env python3
"""
Meeting Attendance Intelligence Report
=======================================
Fetches room calendars from Microsoft Graph API, matches them to VergeSense
spaces, and produces a CSV report with actual occupancy vs. scheduled attendees.

All timestamps are output in US Central Time (CST/CDT).

Dependencies:
    pip install requests python-dateutil fuzzywuzzy python-Levenshtein python-dotenv pytz

Usage:
    1. Create a .env file with credentials
    2. Configure ROOM_FILTERS below
    3. python meeting_attendance_report.py
"""

import os
import sys
import csv
import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser
from fuzzywuzzy import fuzz
from dotenv import load_dotenv
import pytz

# ============================================================================
# LOAD ENVIRONMENT
# ============================================================================

load_dotenv()

GRAPH_TENANT_ID = os.environ.get("GRAPH_TENANT_ID", "YOUR_TENANT_ID")
GRAPH_CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID", "YOUR_CLIENT_ID")
GRAPH_CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
VS_API_KEY = os.environ.get("VS_API_KEY", "YOUR_VERGESENSE_API_KEY")
VS_BASE_URL = "https://api.vergesense.com"

# ============================================================================
# ROOM FILTERS — CONFIGURE THESE
# ============================================================================
# Set any combination. Leave a filter as None or empty to skip it.
# All filters are combined with AND logic.

ROOM_FILTERS = {
    # Match rooms whose displayName contains ANY of these substrings (case-insensitive)
    # Example: ["Board", "Huddle", "Exec"]
    "name_contains": [],

    # Match rooms whose displayName exactly matches ANY of these (case-insensitive)
    # Example: ["Board Room A", "Hudson Room", "Phone Booth 3"]
    "name_exact": [],

    # Match rooms whose building field contains ANY of these (case-insensitive)
    # Example: ["HQ", "Campus North", "Building 5"]
    "building_contains": [],

    # Match rooms whose floorLabel contains ANY of these (case-insensitive)
    # Example: ["1", "Floor 3", "Ground"]
    "floor_contains": [],

    # Match rooms whose emailAddress matches ANY of these (case-insensitive)
    # Example: ["boardroom-a@company.com", "hudsonroom@company.com"]
    "email_list": [],

    # Match rooms with capacity >= this value. Set to 0 or None to skip.
    "min_capacity": None,

    # Match rooms with capacity <= this value. Set to 0 or None to skip.
    "max_capacity": None,
}

# ============================================================================
# SETTINGS
# ============================================================================

FUZZY_MATCH_THRESHOLD = 70
SNAPSHOT_INTERVAL_MINUTES = 5
CST = pytz.timezone("America/Chicago")
REPORT_FILENAME = f"meeting_attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


# ============================================================================
# TIMEZONE HELPERS
# ============================================================================

def to_cst(dt_string):
    """Parse an ISO datetime string and convert to CST. Returns formatted string."""
    if not dt_string:
        return ""
    try:
        dt = dateparser.isoparse(dt_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_cst = dt.astimezone(CST)
        return dt_cst.strftime("%Y-%m-%d %I:%M %p %Z")
    except Exception:
        return str(dt_string)


def to_cst_iso(dt_string):
    """Parse an ISO datetime string and return CST as ISO format (for API queries)."""
    if not dt_string:
        return ""
    try:
        dt = dateparser.isoparse(dt_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(CST).isoformat()
    except Exception:
        return str(dt_string)


def safe_iso(dt_string):
    """Parse ISO string to timezone-aware datetime. Returns None on failure."""
    if not dt_string:
        return None
    try:
        dt = dateparser.isoparse(dt_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


# ============================================================================
# GRAPH API — AUTHENTICATION
# ============================================================================

def get_graph_token():
    """Authenticate via OAuth2 client credentials and return access token."""
    print("🔐 Authenticating with Microsoft Graph API...")
    url = f"https://login.microsoftonline.com/{GRAPH_TENANT_ID}/oauth2/v2.0/token"
    resp = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": GRAPH_CLIENT_ID,
        "client_secret": GRAPH_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    })
    if not resp.ok:
        print(f"   ❌ Auth failed: {resp.status_code} — {resp.text[:300]}")
        sys.exit(1)
    token = resp.json().get("access_token")
    if not token:
        print("   ❌ No access_token in response")
        sys.exit(1)
    print("   ✅ Authenticated")
    return token


# ============================================================================
# GRAPH API — PAGINATOR
# ============================================================================

def graph_paginate(url, headers):
    """Follow @odata.nextLink and collect all results."""
    results = []
    while url:
        resp = requests.get(url, headers=headers)
        if not resp.ok:
            print(f"      ⚠️  Graph {resp.status_code}: {resp.text[:200]}")
            break
        data = resp.json()
        results.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return results


# ============================================================================
# GRAPH API — FETCH & FILTER ROOMS
# ============================================================================

def apply_room_filters(rooms, filters):
    """Apply user-defined filters to the list of Graph rooms."""
    filtered = []

    for room in rooms:
        display = (room.get("displayName") or "").lower()
        email = (room.get("emailAddress") or "").lower()
        building = (room.get("building") or "").lower()
        floor_label = (room.get("floorLabel") or room.get("floor") or "").lower()
        capacity = room.get("capacity") or 0

        # --- name_contains ---
        if filters.get("name_contains"):
            if not any(n.lower() in display for n in filters["name_contains"]):
                continue

        # --- name_exact ---
        if filters.get("name_exact"):
            if not any(display == n.lower() for n in filters["name_exact"]):
                continue

        # --- building_contains ---
        if filters.get("building_contains"):
            if not any(b.lower() in building for b in filters["building_contains"]):
                continue

        # --- floor_contains ---
        if filters.get("floor_contains"):
            if not any(f.lower() in floor_label for f in filters["floor_contains"]):
                continue

        # --- email_list ---
        if filters.get("email_list"):
            if not any(email == e.lower() for e in filters["email_list"]):
                continue

        # --- min_capacity ---
        if filters.get("min_capacity") and filters["min_capacity"] > 0:
            if capacity < filters["min_capacity"]:
                continue

        # --- max_capacity ---
        if filters.get("max_capacity") and filters["max_capacity"] > 0:
            if capacity > filters["max_capacity"]:
                continue

        filtered.append(room)

    return filtered


def get_graph_rooms(token):
    """Fetch all rooms from Graph and apply user filters."""
    print("\n📋 Fetching rooms from Microsoft Graph API...")
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://graph.microsoft.com/v1.0/places/microsoft.graph.room"
    all_rooms = graph_paginate(url, headers)
    print(f"   Total rooms in tenant: {len(all_rooms)}")

    # Check if any filter is active
    any_filter_active = any(
        bool(v) if not isinstance(v, (int, float)) else (v is not None and v > 0)
        for v in ROOM_FILTERS.values()
    )

    if any_filter_active:
        print(f"   🔍 Applying filters...")
        for key, val in ROOM_FILTERS.items():
            if val and (not isinstance(val, (int, float)) or val > 0):
                print(f"      • {key}: {val}")
        rooms = apply_room_filters(all_rooms, ROOM_FILTERS)
        print(f"   ✅ {len(rooms)} rooms after filtering")
    else:
        rooms = all_rooms
        print(f"   ℹ️  No filters applied — using all {len(rooms)} rooms")

    for r in rooms:
        print(f"      • {r.get('displayName', 'N/A')} | {r.get('emailAddress', '')} "
              f"| building: {r.get('building', '?')} | capacity: {r.get('capacity', '?')}")

    return rooms


# ============================================================================
# GRAPH API — ORGANIZER DEPARTMENT LOOKUP
# ============================================================================

def get_user_department(token, user_email):
    """Look up a user's department from the Graph directory."""
    if not user_email:
        return ""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}?$select=department"
    resp = requests.get(url, headers=headers)
    if resp.ok:
        return resp.json().get("department", "")
    return ""


# Department cache so we don't re-query the same organizer
_dept_cache = {}


def get_department_cached(token, user_email):
    """Cached wrapper around get_user_department."""
    if not user_email:
        return ""
    if user_email not in _dept_cache:
        _dept_cache[user_email] = get_user_department(token, user_email)
    return _dept_cache[user_email]


# ============================================================================
# GRAPH API — FETCH MEETINGS FOR A ROOM
# ============================================================================

def get_room_meetings(token, room_email, start_utc, end_utc):
    """Fetch calendar events for a room in the given UTC window."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Prefer": 'outlook.timezone="UTC"',
    }
    select = (
        "id,subject,start,end,organizer,attendees,"
        "isAllDay,isCancelled,isOnlineMeeting"
    )
    url = (
        f"https://graph.microsoft.com/v1.0/users/{room_email}/calendarView"
        f"?startDateTime={start_utc}&endDateTime={end_utc}"
        f"&$select={select}&$top=100&$orderby=start/dateTime"
    )
    events = graph_paginate(url, headers)
    return [e for e in events if not e.get("isCancelled", False)]


# ============================================================================
# VERGESENSE — FETCH ALL SPACES
# ============================================================================

def get_vs_spaces():
    """Walk buildings → floors → spaces and return a flat list."""
    print("\n📋 Fetching spaces from VergeSense API...")
    headers = {"vs-api-key": VS_API_KEY}
    spaces = []

    resp = requests.get(f"{VS_BASE_URL}/buildings", headers=headers)
    if not resp.ok:
        print(f"   ❌ Buildings fetch failed: {resp.status_code}")
        return spaces
    buildings = resp.json()

    for bldg in buildings:
        bldg_id = bldg.get("building_id") or bldg.get("id", "")
        bldg_name = bldg.get("name", "")

        floors = bldg.get("floors", [])
        if not floors:
            r = requests.get(f"{VS_BASE_URL}/buildings/{bldg_id}/floors", headers=headers)
            floors = r.json() if r.ok else []

        for floor in floors:
            floor_id = floor.get("floor_id") or floor.get("id", "")
            floor_name = floor.get("name", "")

            r = requests.get(
                f"{VS_BASE_URL}/buildings/{bldg_id}/floors/{floor_id}/spaces",
                headers=headers,
            )
            if not r.ok:
                continue
            for sp in r.json():
                sp["_bldg_id"] = bldg_id
                sp["_bldg_name"] = bldg_name
                sp["_floor_id"] = floor_id
                sp["_floor_name"] = floor_name
                spaces.append(sp)

    print(f"   ✅ Found {len(spaces)} spaces")
    for s in spaces:
        print(f"      • {s.get('name', 'N/A')} | building: {s.get('_bldg_name')} "
              f"| floor: {s.get('_floor_name')}")
    return spaces


# ============================================================================
# VERGESENSE — OCCUPANCY DURING A TIME WINDOW
# ============================================================================

def get_vs_occupancy(space, start_iso, end_iso):
    """
    Query people_count snapshots for a space during [start, end].
    Returns max occupancy and supporting data.
    """
    headers = {"vs-api-key": VS_API_KEY}
    space_id = space.get("space_id") or space.get("id", "")
    url = (
        f"{VS_BASE_URL}/buildings/{space['_bldg_id']}"
        f"/floors/{space['_floor_id']}/spaces/{space_id}/people_count"
        f"?start_time={start_iso}&end_time={end_iso}"
        f"&interval={SNAPSHOT_INTERVAL_MINUTES}m"
    )
    resp = requests.get(url, headers=headers)
    if not resp.ok:
        return None

    payload = resp.json()
    if isinstance(payload, list):
        snapshots = payload
    elif isinstance(payload, dict):
        snapshots = payload.get("data", payload.get("results", []))
    else:
        snapshots = []

    if not snapshots:
        return {"max": 0, "avg": 0, "snapshots": 0, "occupied": False, "timeline": ""}

    counts = [s.get("people_count", s.get("count", 0)) or 0 for s in snapshots]
    return {
        "max": max(counts),
        "avg": round(sum(counts) / len(counts), 1),
        "snapshots": len(counts),
        "occupied": any(c > 0 for c in counts),
        "timeline": " → ".join(str(c) for c in counts),
    }


# ============================================================================
# MATCH GRAPH ROOMS → VERGESENSE SPACES
# ============================================================================

def match_rooms_to_spaces(rooms, spaces):
    """Fuzzy-match by name. Returns list of {graph_room, vs_space, score}."""
    print(f"\n🔗 Matching rooms → VergeSense spaces (threshold ≥ {FUZZY_MATCH_THRESHOLD}%)...")
    matched = []

    for room in rooms:
        rname = room.get("displayName", "")
        best, best_score = None, 0
        for sp in spaces:
            score = fuzz.token_sort_ratio(rname.lower(), sp.get("name", "").lower())
            if score > best_score:
                best_score = score
                best = sp

        if best_score >= FUZZY_MATCH_THRESHOLD and best:
            matched.append({"graph_room": room, "vs_space": best, "score": best_score})
            print(f"   ✅ [{best_score:>3}%]  \"{rname}\"  →  \"{best.get('name')}\"")
        else:
            cand = best.get("name", "—") if best else "—"
            print(f"   ❌ [{best_score:>3}%]  \"{rname}\"  →  No match (closest: \"{cand}\")")

    print(f"\n   Matched: {len(matched)} / {len(rooms)}")
    return matched


# ============================================================================
# BUILD REPORT
# ============================================================================

def build_report(matched, token, start_utc, end_utc):
    """Core loop: for each matched room, fetch meetings + VS occupancy."""
    print(f"\n📊 Building report for last 24 hours (all times in CST)...")
    print(f"   UTC window: {start_utc}  →  {end_utc}\n")

    rows = []

    for pair in matched:
        gr = pair["graph_room"]
        vs = pair["vs_space"]

        room_name = gr.get("displayName", "")
        room_email = gr.get("emailAddress", "")
        vs_name = vs.get("name", "")
        vs_space_id = vs.get("space_id") or vs.get("id", "")

        print(f"   📍 {room_name}  ↔  {vs_name}")

        # ---- Fetch meetings ----
        meetings = get_room_meetings(token, room_email, start_utc, end_utc)
        if not meetings:
            print(f"      ⏭️  No meetings — skipping")
            continue

        print(f"      📅 {len(meetings)} meeting(s)")

        for mtg in meetings:
            # --- Graph meeting fields ---
            subject = mtg.get("subject", "")
            m_start = mtg.get("start", {}).get("dateTime", "")
            m_end = mtg.get("end", {}).get("dateTime", "")
            org_obj = mtg.get("organizer", {}).get("emailAddress", {})
            org_name = org_obj.get("name", "")
            org_email = org_obj.get("address", "")
            attendees = mtg.get("attendees", [])
            is_online = mtg.get("isOnlineMeeting", False)

            # Duration
            dt_s = safe_iso(m_start)
            dt_e = safe_iso(m_end)
            duration_min = int((dt_e - dt_s).total_seconds() / 60) if dt_s and dt_e else 0

            # Attendee vs Invitee counts
            #   Invitees  = everyone on the invite list
            #   Attendees = those who accepted
            invitee_count = len(attendees)
            accepted_count = sum(
                1 for a in attendees
                if a.get("status", {}).get("response") == "accepted"
            )

            # Organizer department (cached)
            org_dept = get_department_cached(token, org_email)

            # --- VergeSense occupancy during this meeting ---
            vs_occ = get_vs_occupancy(vs, m_start, m_end)
            vs_actual = ""
            if vs_occ is not None:
                vs_actual = vs_occ["max"]
            else:
                vs_actual = "N/A"

            # --- Determine meeting status ---
            status = ""
            if vs_occ is not None:
                mx = vs_occ["max"]
                if not vs_occ["occupied"]:
                    status = "GHOST"
                elif invitee_count > 0:
                    ratio = mx / invitee_count
                    if mx > invitee_count:
                        status = "OVER_ATTENDED"
                    elif ratio >= 0.8:
                        status = "WELL_ATTENDED"
                    elif ratio >= 0.5:
                        status = "PARTIALLY_ATTENDED"
                    else:
                        status = "UNDERUTILIZED"
                else:
                    status = "OCCUPIED"
            else:
                status = "VS_DATA_UNAVAILABLE"

            icon = {
                "GHOST": "👻", "UNDERUTILIZED": "📉",
                "PARTIALLY_ATTENDED": "🔶", "WELL_ATTENDED": "✅",
                "OVER_ATTENDED": "🔴", "OCCUPIED": "❓",
                "VS_DATA_UNAVAILABLE": "⚠️",
            }.get(status, "❓")

            print(
                f"      {icon}  {subject[:45]:<45} | "
                f"Invitees: {invitee_count:>2} | Accepted: {accepted_count:>2} | "
                f"VS Actual: {str(vs_actual):>3} | {status}"
            )

            # --- Build row ---
            row = {
                # Graph — Room
                "Graph_Room_Name": room_name,
                "Graph_Room_Email": room_email,

                # Graph — Organizer
                "Graph_Organizer": org_name,
                "Graph_Organizer_Email": org_email,
                "Graph_Organizer_Department": org_dept,

                # Graph — Meeting
                "Graph_Meeting_Subject": subject,
                "Graph_Start_Time_CST": to_cst(m_start),
                "Graph_End_Time_CST": to_cst(m_end),
                "Graph_Meeting_Duration_Min": duration_min,
                "Graph_IsOnlineMeeting": is_online,

                # Graph — People counts
                "Graph_Invitee_Count": invitee_count,
                "Graph_Attendee_Count": accepted_count,

                # VergeSense
                "VS_Room": vs_name,
                "VS_Space_ID": vs_space_id,
                "VS_Building": vs.get("_bldg_name", ""),
                "VS_Floor": vs.get("_floor_name", ""),
                "VS_Capacity": vs.get("capacity", ""),
                "VS_Actual_Occupancy": vs_actual,
                "VS_Avg_Occupancy": vs_occ["avg"] if vs_occ else "N/A",
                "VS_Snapshot_Count": vs_occ["snapshots"] if vs_occ else 0,
                "VS_Occupancy_Timeline": vs_occ["timeline"] if vs_occ else "N/A",

                # Computed
                "Status": status,
                "Match_Score": pair["score"],
            }

            rows.append(row)

    return rows


# ============================================================================
# WRITE CSV
# ============================================================================

def write_csv(rows, filename):
    """Write report rows to CSV."""
    if not rows:
        print("\n⚠️  No data — no meetings found in matched rooms.")
        return False
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n💾 Report saved → {filename}")
    print(f"   Rows: {len(rows)} | Columns: {len(rows[0])}")
    return True


# ============================================================================
# SUMMARY
# ============================================================================

def print_summary(rows):
    """Print console summary."""
    total = len(rows)
    if total == 0:
        return

    status_counts = {}
    for r in rows:
        s = r["Status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    icons = {
        "GHOST": "👻", "UNDERUTILIZED": "📉", "PARTIALLY_ATTENDED": "🔶",
        "WELL_ATTENDED": "✅", "OVER_ATTENDED": "🔴", "OCCUPIED": "❓",
        "VS_DATA_UNAVAILABLE": "⚠️",
    }

    total_duration = sum(r["Graph_Meeting_Duration_Min"] for r in rows)

    print("\n" + "=" * 65)
    print("  📊  SUMMARY")
    print("=" * 65)
    print(f"  Total meetings  : {total}")
    print(f"  Total booked    : {total_duration} min ({total_duration / 60:.1f} hrs)")
    print()

    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        icon = icons.get(status, "❓")
        bar = "█" * int(pct / 2)
        print(f"  {icon}  {status:<25} {count:>3}  ({pct:>5.1f}%)  {bar}")

    # Unique departments
    depts = set(r["Graph_Organizer_Department"] for r in rows if r["Graph_Organizer_Department"])
    if depts:
        print(f"\n  🏢 Departments seen: {', '.join(sorted(depts))}")

    # Ghost meeting organizers
    ghosts = [r for r in rows if r["Status"] == "GHOST"]
    if ghosts:
        print(f"\n  👻 Ghost meeting organizers:")
        ghost_orgs = {}
        for g in ghosts:
            key = g["Graph_Organizer"] or g["Graph_Organizer_Email"]
            ghost_orgs[key] = ghost_orgs.get(key, 0) + 1
        for org, cnt in sorted(ghost_orgs.items(), key=lambda x: -x[1]):
            print(f"      • {org}: {cnt} ghost meeting(s)")

    print("=" * 65)


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 65)
    print("   MEETING ATTENDANCE INTELLIGENCE REPORT")
    print("   Graph API  +  VergeSense  |  All times in CST")
    print("=" * 65)

    # Validate credentials
    missing = []
    if GRAPH_TENANT_ID in ("", "YOUR_TENANT_ID"):
        missing.append("GRAPH_TENANT_ID")
    if GRAPH_CLIENT_ID in ("", "YOUR_CLIENT_ID"):
        missing.append("GRAPH_CLIENT_ID")
    if GRAPH_CLIENT_SECRET in ("", "YOUR_CLIENT_SECRET"):
        missing.append("GRAPH_CLIENT_SECRET")
    if VS_API_KEY in ("", "YOUR_VERGESENSE_API_KEY"):
        missing.append("VS_API_KEY")
    if missing:
        print(f"\n❌ Missing in .env: {', '.join(missing)}")
        sys.exit(1)

    # Time window — last 24 hours in UTC (APIs expect UTC)
    now = datetime.now(timezone.utc)
    start_utc = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
    end_utc = now.strftime("%Y-%m-%dT%H:%M:%S.0000000Z")

    print(f"\n⏰ Window (UTC) : {start_utc}")
    print(f"               → {end_utc}")
    print(f"   (Report timestamps will be converted to CST)")

    # Active filters
    active = {
        k: v for k, v in ROOM_FILTERS.items()
        if v and (not isinstance(v, (int, float)) or v > 0)
    }
    if active:
        print(f"\n🔍 Active room filters:")
        for k, v in active.items():
            print(f"   • {k}: {v}")

    # Step 1: Graph rooms
    token = get_graph_token()
    rooms = get_graph_rooms(token)
    if not rooms:
        print("\n❌ No rooms found. Check Graph permissions (Place.Read.All) and filters.")
        sys.exit(1)

    # Step 2: VergeSense spaces
    spaces = get_vs_spaces()
    if not spaces:
        print("\n❌ No VergeSense spaces found. Check API key.")
        sys.exit(1)

    # Step 3: Match
    matched = match_rooms_to_spaces(rooms, spaces)
    if not matched:
        print(f"\n❌ No matches. Lower FUZZY_MATCH_THRESHOLD ({FUZZY_MATCH_THRESHOLD}) or align names.")
        sys.exit(1)

    # Step 4: Build report
    rows = build_report(matched, token, start_utc, end_utc)

    # Step 5: Write CSV
    write_csv(rows, REPORT_FILENAME)

    # Step 6: Summary
    print_summary(rows)

    print("\n✅ Done.\n")


if __name__ == "__main__":
    main()
