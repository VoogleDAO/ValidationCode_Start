import json
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from collections import Counter
from dateutil import parser

class AndroidLocationHistoryValidator:
    def __init__(self, max_speed_m_s: float = 44.44, allowed_hierarchy_levels: List[int] = [0, 1, 2]):
        self.max_speed_m_s = max_speed_m_s
        self.allowed_hierarchy_levels = allowed_hierarchy_levels
        self.max_walk_speed = 1.4
        self.max_run_speed = 3.5
        
    @staticmethod
    def parse_time(time_str: str) -> Optional[datetime]:
        if not time_str:
            return None
        try:
            # Android format uses ISO 8601 with timezone
            return parser.parse(time_str)
        except Exception:
            return None

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371_000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = phi2 - phi1
        dlambda = math.radians(lon2 - lon1)

        a = (math.sin(dphi / 2)**2 
             + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def calc_speed(distance_meters: float, t1: datetime, t2: datetime) -> float:
        if not t1 or not t2:
            return 0.0
        dt = (t2 - t1).total_seconds()
        return distance_meters / dt if dt > 0 else 0.0

    def check_time_order(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 1.0
            
        issues = 0
        total_checks = len(data) * 2 - 1  # Two checks per entry plus transitions
        
        for i, entry in enumerate(data):
            start = self.parse_time(entry.get("startTime"))
            end = self.parse_time(entry.get("endTime"))
            if start and end and end < start:
                issues += 1
            if i < len(data) - 1:
                next_start = self.parse_time(data[i + 1].get("startTime"))
                if end and next_start and next_start < end:
                    issues += 1
        
        return 1.0 - (issues / total_checks)

    def check_suspicious_speed(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 1.0
            
        valid_entries = 0
        total_checked = 0
        
        for entry in data:
            if "activities" in entry and entry["activities"]:
                total_checked += 1
                distance = entry.get("distance", 0)
                start_time = self.parse_time(entry.get("startTime"))
                end_time = self.parse_time(entry.get("endTime"))

                try:
                    dist_m = float(distance) if distance else 0.0
                except ValueError:
                    dist_m = 0.0

                speed = self.calc_speed(dist_m, start_time, end_time)
                if speed <= self.max_speed_m_s:
                    valid_entries += 1
        
        return valid_entries / total_checked if total_checked > 0 else 1.0

    def check_inconsistent_probabilities(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 1.0
            
        valid_probs = 0
        total_probs = 0
        
        for entry in data:
            if "activities" in entry:
                for activity in entry["activities"]:
                    if "probability" in activity:
                        total_probs += 1
                        try:
                            prob = float(activity["probability"])
                            if 0.0 <= prob <= 1.0:
                                valid_probs += 1
                        except ValueError:
                            pass
        
        return valid_probs / total_probs if total_probs > 0 else 1.0

    def check_hierarchy_levels(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 1.0
        valid_levels = 0
        total_checked = 0
        
        for entry in data:
            if "placeVisit" in entry:
                place = entry["placeVisit"].get("location", {})
                if "locationConfidence" in place:
                    total_checked += 1
                    try:
                        confidence = float(place["locationConfidence"])
                        if 0.0 <= confidence <= 1.0:
                            valid_levels += 1
                    except ValueError:
                        pass
        
        return valid_levels / total_checked if total_checked > 0 else 1.0

    def check_waypoints(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 1.0
            
        valid_points = 0
        total_points = 0
        
        for entry in data:
            if "activitySegment" in entry:
                waypoints = entry["activitySegment"].get("waypointPath", {}).get("waypoints", [])
                for waypoint in waypoints:
                    total_points += 2  # Two checks per point: lat and lng
                    
                    if "latE7" in waypoint and "lngE7" in waypoint:
                        try:
                            lat = float(waypoint["latE7"]) / 1e7
                            lng = float(waypoint["lngE7"]) / 1e7
                            if -90 <= lat <= 90 and -180 <= lng <= 180:
                                valid_points += 2
                        except ValueError:
                            pass
        
        return valid_points / total_points if total_points > 0 else 1.0

    def check_for_regular_intervals(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 1.0
            
        intervals = []
        for i in range(len(data) - 1):
            end_cur = self.parse_time(data[i].get("endTime"))
            start_next = self.parse_time(data[i + 1].get("startTime"))
            if end_cur and start_next:
                intervals.append((start_next - end_cur).total_seconds())

        if not intervals:
            return 1.0

        c = Counter(intervals)
        uniqueness_ratio = len(c) / len(intervals)
        return uniqueness_ratio

    def check_local_travel_vs_mode(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 1.0
            
        valid_modes = 0
        total_checked = 0
        
        for entry in data:
            if "activitySegment" in entry:
                activity_type = entry["activitySegment"].get("activityType", "").lower()
                if not (activity_type and ("walking" in activity_type or "running" in activity_type)):
                    continue
                    
                total_checked += 1
                start_time = self.parse_time(entry["activitySegment"].get("startTime"))
                end_time = self.parse_time(entry["activitySegment"].get("endTime"))
                
                try:
                    dist_m = float(entry["activitySegment"].get("distance", 0))
                except ValueError:
                    dist_m = 0.0

                speed = self.calc_speed(dist_m, start_time, end_time)
                
                if ("walking" in activity_type and speed <= self.max_walk_speed) or \
                   ("running" in activity_type and speed <= self.max_run_speed):
                    valid_modes += 1
        
        return valid_modes / total_checked if total_checked > 0 else 1.0

    def check_time_span(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 0.0
        
        earliest_time = None
        latest_time = None
        
        for entry in data:
            start = self.parse_time(entry.get("startTime"))
            end = self.parse_time(entry.get("endTime"))
            
            if start:
                if earliest_time is None or start < earliest_time:
                    earliest_time = start
            if end:
                if latest_time is None or end > latest_time:
                    latest_time = end
        
        if earliest_time and latest_time:
            return ((latest_time - earliest_time).total_seconds())/86400.0
        return 0.0

    def validate(self, data: List[Dict[str, Any]]) -> float:
        # Android data is already a list of segments
        segments = data
        print(f"\nStarting validation with {len(segments)} segments")
        
        checks = [
            ("Time Order", self.check_time_order(segments)),
            ("Suspicious Speed", self.check_suspicious_speed(segments)),
            ("Probabilities", self.check_inconsistent_probabilities(segments)),
            ("Hierarchy Levels", self.check_hierarchy_levels(segments)),
            ("Waypoints", self.check_waypoints(segments)),
            ("Regular Intervals", self.check_for_regular_intervals(segments)),
            ("Local Travel", self.check_local_travel_vs_mode(segments))
        ]
        
        print("\nIndividual check results:")
        for name, value in checks:
            print(f"{name}: {value:.3f}")
            
        valid = sum(value for _, value in checks)
        print(f"\nSum of all checks: {valid:.3f}")
        print(f"Minimum threshold: {7*0.1}")
        
        if valid < (7*0.1):
            print("Failed validation - returning -1")
            return -1
        
        time_span = self.check_time_span(segments)
        print(f"\nTime span in days: {time_span:.2f}")
        print(f"Time span score (divided by 60): {time_span/60.0:.3f}")
        
        final_score = min(time_span/60.0, 1.0)
        print(f"Final clamped score: {final_score:.3f}")
        
        return final_score


if __name__ == "__main__":
    with open("android-location-history.json", "r") as f:
        data = json.load(f)

    validator = AndroidLocationHistoryValidator()
    results = validator.validate(data)
    print(results) 