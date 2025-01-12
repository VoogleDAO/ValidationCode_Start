import json
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from collections import Counter
from dateutil import parser

class LocationHistoryValidator:
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

    @staticmethod
    def parse_geo_string(geo_str: str) -> Optional[tuple]:
        if not geo_str or "geo:" not in geo_str:
            return None
        try:
            coords = geo_str.split("geo:")[1]
            lat_str, lon_str = coords.split(",")
            return float(lat_str), float(lon_str)
        except Exception:
            return None

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
            if "activity" in entry:
                total_checked += 1
                activity = entry["activity"]
                distance_str = activity.get("distanceMeters")
                start_time = self.parse_time(entry.get("startTime"))
                end_time = self.parse_time(entry.get("endTime"))

                try:
                    dist_m = float(distance_str) if distance_str else 0.0
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
            for key in ["activity", "visit"]:
                if key in entry:
                    # Check main probability
                    if "probability" in entry[key]:
                        total_probs += 1
                        try:
                            prob = float(entry[key]["probability"])
                            if 0.0 <= prob <= 1.0:
                                valid_probs += 1
                        except ValueError:
                            pass
                            
                    # Check topCandidate probability
                    if "topCandidate" in entry[key] and "probability" in entry[key]["topCandidate"]:
                        total_probs += 1
                        try:
                            prob = float(entry[key]["topCandidate"]["probability"])
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
            if "visit" in entry and "hierarchyLevel" in entry["visit"]:
                total_checked += 1
                try:
                    hl = int(entry["visit"]["hierarchyLevel"])
                    if hl in self.allowed_hierarchy_levels:
                        valid_levels += 1
                except ValueError:
                    pass
        
        return valid_levels / total_checked if total_checked > 0 else 1.0

    def check_timeline_paths(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 1.0
            
        valid_points = 0
        total_points = 0
        
        for entry in data:
            if "timelinePath" in entry and isinstance(entry["timelinePath"], list):
                for path_node in entry["timelinePath"]:
                    total_points += 2  # Two checks per point
                    
                    if self.parse_geo_string(path_node.get("point", "")):
                        valid_points += 1
                        
                    try:
                        float(path_node.get("durationMinutesOffsetFromStartTime"))
                        valid_points += 1
                    except (TypeError, ValueError):
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
            if "activity" in entry and "topCandidate" in entry["activity"]:
                mode = entry["activity"]["topCandidate"].get("type", "").lower()
                if not (mode and ("walk" in mode or "run" in mode)):
                    continue
                    
                total_checked += 1
                start_time = self.parse_time(entry.get("startTime"))
                end_time = self.parse_time(entry.get("endTime"))
                
                try:
                    dist_m = float(entry["activity"].get("distanceMeters", 0))
                except ValueError:
                    dist_m = 0.0

                speed = self.calc_speed(dist_m, start_time, end_time)
                
                if ("walk" in mode and speed <= self.max_walk_speed) or \
                   ("run" in mode and speed <= self.max_run_speed):
                    valid_modes += 1
        
        return valid_modes / total_checked if total_checked > 0 else 1.0

    def check_time_span(self, data: List[Dict[str, Any]]) -> float:
        if not data:
            return 0.0
        
        # Initialize with None to handle first valid times found
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
        valid = sum([self.check_time_order(data), self.check_suspicious_speed(data), self.check_inconsistent_probabilities(data), self.check_hierarchy_levels(data), self.check_timeline_paths(data), self.check_for_regular_intervals(data), self.check_local_travel_vs_mode(data)])
        if valid < 7*0.9:
            return -1
        else:
            return min(self.check_time_span(data)/60.0, 1.0) #max score at 60 days clamped to 1.0


if __name__ == "__main__":
    with open("location-history.json", "r") as f:
        data = json.load(f)

    validator = LocationHistoryValidator()
    results = validator.validate(data)
    