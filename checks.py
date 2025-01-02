import json
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from collections import Counter

from dateutil import parser


def parse_time(time_str: str) -> Optional[datetime]:
    if not time_str:
        return None
    try:
        return parser.parse(time_str)
    except Exception:
        return None

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2)**2 
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calc_speed(distance_meters: float, t1: datetime, t2: datetime) -> float:
    if not t1 or not t2:
        return 0.0
    dt = (t2 - t1).total_seconds()
    return distance_meters / dt if dt > 0 else 0.0

def parse_geo_string(geo_str: str) -> Optional[tuple]:

    if not geo_str or "geo:" not in geo_str:
        return None
    try:
        coords = geo_str.split("geo:")[1]
        lat_str, lon_str = coords.split(",")
        return float(lat_str), float(lon_str)
    except Exception:
        return None

def check_time_order(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    issues = []

    for i, entry in enumerate(data):
        start = parse_time(entry.get("startTime"))
        end = parse_time(entry.get("endTime"))
        if start and end and end < start:
            issues.append({
                "index": i,
                "error": "endTime is before startTime",
                "startTime": entry.get("startTime"),
                "endTime": entry.get("endTime")
            })
        if i < len(data) - 1:
            next_start = parse_time(data[i + 1].get("startTime"))
            if end and next_start and next_start < end:
                issues.append({
                    "index": i,
                    "error": "Overlap or backward jump in time between entries",
                    "current_endTime": entry.get("endTime"),
                    "next_startTime": data[i + 1].get("startTime")
                })
    return issues

def check_suspicious_speed(data: List[Dict[str, Any]], max_speed_m_s: float = 44.44) -> List[Dict[str, Any]]:
    issues = []
    for i, entry in enumerate(data):
        if "activity" in entry:
            activity = entry["activity"]
            distance_str = activity.get("distanceMeters")
            start_geo_str = activity.get("start")
            end_geo_str = activity.get("end")
            start_time = parse_time(entry.get("startTime"))
            end_time = parse_time(entry.get("endTime"))

            if distance_str:
                # Use provided distance first
                try:
                    dist_m = float(distance_str)
                except ValueError:
                    dist_m = 0.0
            else:
                # If no distance is given, try to compute from lat/lon
                dist_m = 0.0
                start_coords = parse_geo_string(start_geo_str)
                end_coords = parse_geo_string(end_geo_str)
                if start_coords and end_coords:
                    dist_m = haversine_distance(*start_coords, *end_coords)

            speed = calc_speed(dist_m, start_time, end_time)
            if speed > max_speed_m_s:
                issues.append({
                    "index": i,
                    "error": "Suspiciously high speed",
                    "calculated_speed_m_s": speed
                })
    return issues

def check_inconsistent_probabilities(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    issues = []
    for i, entry in enumerate(data):
        # Activity probability
        if "activity" in entry:
            p = entry["activity"].get("probability")
            if p is not None:
                try:
                    prob = float(p)
                    if prob < 0.0 or prob > 1.0:
                        issues.append({
                            "index": i,
                            "error": "Activity probability out of [0,1] range",
                            "probability": prob
                        })
                except ValueError:
                    issues.append({
                        "index": i,
                        "error": "Activity probability is not a valid float",
                        "probability": p
                    })

        if "visit" in entry:
            p = entry["visit"].get("probability")
            if p is not None:
                try:
                    prob = float(p)
                    if prob < 0.0 or prob > 1.0:
                        issues.append({
                            "index": i,
                            "error": "Visit probability out of [0,1] range",
                            "probability": prob
                        })
                except ValueError:
                    issues.append({
                        "index": i,
                        "error": "Visit probability is not a valid float",
                        "probability": p
                    })

        if "activity" in entry and "topCandidate" in entry["activity"]:
            pc = entry["activity"]["topCandidate"].get("probability")
            if pc is not None:
                try:
                    pc_val = float(pc)
                    if pc_val < 0.0 or pc_val > 1.0:
                        issues.append({
                            "index": i,
                            "error": "topCandidate probability (activity) out of [0,1]",
                            "probability": pc_val
                        })
                except ValueError:
                    issues.append({
                        "index": i,
                        "error": "topCandidate probability (activity) invalid float",
                        "probability": pc
                    })

        if "visit" in entry and "topCandidate" in entry["visit"]:
            pc = entry["visit"]["topCandidate"].get("probability")
            if pc is not None:
                try:
                    pc_val = float(pc)
                    if pc_val < 0.0 or pc_val > 1.0:
                        issues.append({
                            "index": i,
                            "error": "topCandidate probability (visit) out of [0,1]",
                            "probability": pc_val
                        })
                except ValueError:
                    issues.append({
                        "index": i,
                        "error": "topCandidate probability (visit) invalid float",
                        "probability": pc
                    })

    return issues

def check_hierarchy_levels(data: List[Dict[str, Any]], allowed_levels: List[int] = [0,1,2]) -> List[Dict[str, Any]]:
    issues = []
    for i, entry in enumerate(data):
        if "visit" in entry and "hierarchyLevel" in entry["visit"]:
            hl_str = entry["visit"]["hierarchyLevel"]
            try:
                hl = int(hl_str)
                if hl not in allowed_levels:
                    issues.append({
                        "index": i,
                        "error": "Visit hierarchyLevel not in allowed list",
                        "hierarchyLevel": hl
                    })
            except ValueError:
                issues.append({
                    "index": i,
                    "error": "hierarchyLevel not an integer",
                    "hierarchyLevel": hl_str
                })
    return issues

def check_timeline_paths(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For entries that have a 'timelinePath', we can do some extra checks:
    - Confirm each point is a valid geo coordinate.
    - Confirm the offsets are numeric.
    - Possibly compare the total path distance to the overall activity distance if relevant.
    """
    issues = []
    for i, entry in enumerate(data):
        if "timelinePath" in entry:
            timeline_path = entry["timelinePath"]
            if not isinstance(timeline_path, list):
                issues.append({
                    "index": i,
                    "error": "timelinePath is not a list"
                })
                continue

            for j, path_node in enumerate(timeline_path):
                point = path_node.get("point", "")
                coords = parse_geo_string(point)
                if not coords:
                    issues.append({
                        "index": i,
                        "path_index": j,
                        "error": "Invalid geo point in timelinePath",
                        "point": point
                    })
                offset_str = path_node.get("durationMinutesOffsetFromStartTime")
                try:
                    float(offset_str)  # just check if it’s a valid numeric string
                except (TypeError, ValueError):
                    issues.append({
                        "index": i,
                        "path_index": j,
                        "error": "Non-numeric duration offset",
                        "offset": offset_str
                    })

    return issues

def check_for_regular_intervals(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Looks for suspiciously uniform intervals between entries (e.g., always exactly 10 minutes).
    Human data tends to vary.
    """
    issues = []
    intervals = []
    for i in range(len(data) - 1):
        end_cur = parse_time(data[i].get("endTime"))
        start_next = parse_time(data[i + 1].get("startTime"))
        if end_cur and start_next:
            intervals.append((start_next - end_cur).total_seconds())

    if not intervals:
        return issues

    c = Counter(intervals)
    most_common_value, count = c.most_common(1)[0]  # (value, count)
    # If more than half of the intervals are the exact same, we flag it
    if count > len(intervals) / 2:
        issues.append({
            "error": "More than half of intervals are identical",
            "interval_seconds": most_common_value,
            "occurrences": count,
            "total_intervals": len(intervals)
        })

    return issues

def check_local_travel_vs_mode(data: List[Dict[str, Any]], max_walk_speed=1.4, max_run_speed=3.5) -> List[Dict[str, Any]]:
    """
    Example: If an entry says 'type' : 'walking' but the speed is too high, flag it.
    Here we only do a simple check if 'type' is walking/running vs calculated speed.
    """
    issues = []
    for i, entry in enumerate(data):
        if "activity" in entry and "topCandidate" in entry["activity"]:
            mode = entry["activity"]["topCandidate"].get("type", "")
            start_time = parse_time(entry.get("startTime"))
            end_time = parse_time(entry.get("endTime"))
            dist_str = entry["activity"].get("distanceMeters")
            if dist_str is None:
                continue
            try:
                dist_m = float(dist_str)
            except ValueError:
                dist_m = 0.0

            speed = calc_speed(dist_m, start_time, end_time)
            # If user claimed "walking" or "running", check if speeds are plausible
            if "walk" in mode.lower() and speed > max_walk_speed:
                issues.append({
                    "index": i,
                    "error": "Walking speed too high",
                    "calculated_speed_m_s": speed
                })
            if "run" in mode.lower() and speed > max_run_speed:
                issues.append({
                    "index": i,
                    "error": "Running speed too high",
                    "calculated_speed_m_s": speed
                })

    return issues


def run_all_checks(data: List[Dict[str, Any]], max_speed_m_s: float = 44.44) -> Dict[str, List[Dict[str, Any]]]:
    results = {}
    results["time_order_issues"] = check_time_order(data)
    results["speed_issues"] = check_suspicious_speed(data, max_speed_m_s)
    results["probability_issues"] = check_inconsistent_probabilities(data)
    results["hierarchy_issues"] = check_hierarchy_levels(data, [0,1,2])
    results["timeline_path_issues"] = check_timeline_paths(data)
    results["regular_interval_issues"] = check_for_regular_intervals(data)
    results["local_travel_mode_issues"] = check_local_travel_vs_mode(data)

    return results

# --------------------------------------------------
# Example Usage
# --------------------------------------------------
if __name__ == "__main__":

    data = json.load(open("location-history.json", "r"))

    # Run all checks
    check_results = run_all_checks(data, max_speed_m_s=44.44)

    # Print summary
    for check_name, issues in check_results.items():
        print(f"---- {check_name} ----")
        if issues:
            for issue in issues:
                print(issue)
        else:
            print("No issues found.")
        print()
