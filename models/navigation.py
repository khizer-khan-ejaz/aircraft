import math
from typing import Tuple, Optional
from geographiclib.geodesic import Geodesic
import datetime
from allclass import Point  # Assuming Point is defined in allclass

class Navigation:
    def get_track_angle(self, dep: Point, arr: Point, magnetic: bool = True, date: Optional[datetime.datetime] = None) -> float:
        """Calculate true or magnetic bearing between two points."""
        if not (-90 <= dep.lat <= 90 and -180 <= dep.long <= 180 and 
                -90 <= arr.lat <= 90 and -180 <= arr.long <= 180):
            raise ValueError("Invalid latitude or longitude")
        if (dep.lat, dep.long) == (arr.lat, arr.long):
            return 0.0

        lat1, lon1 = math.radians(dep.lat), math.radians(dep.long)
        lat2, lon2 = math.radians(arr.lat), math.radians(arr.long)
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        true_bearing = math.degrees(math.atan2(y, x))
        true_bearing = (true_bearing + 360) % 360
        
        if not magnetic:
            return round(true_bearing, 2)
        
        magnetic_variation = self.get_magnetic_variation(dep.lat, dep.long, date)
        magnetic_bearing = (true_bearing - magnetic_variation + 360) % 360
        return round(magnetic_bearing, 2)

    def get_magnetic_variation(self, lat: float, lon: float, date: Optional[datetime.datetime] = None) -> float:
        """Calculate magnetic variation at a given point."""
        try:
            from pygeomag import GeoMag
            geo = GeoMag()
            date = date or datetime.datetime.utcnow()
            dec_year = self.decimal_year(date)
            result = geo.calculate(glat=lat, glon=lon, alt=0, time=dec_year)
            return float(result.dec)
        except ImportError:
            return -12.0  # Fallback for New York
        except Exception as e:
            print(f"Error calculating magnetic variation: {e}")
            return -12.0

    def decimal_year(self, date: datetime.datetime) -> float:
        """Convert datetime to decimal year."""
        year_start = datetime.datetime(date.year, 1, 1)
        year_end = datetime.datetime(date.year + 1, 1, 1)
        year_length = (year_end - year_start).total_seconds()
        seconds_into_year = (date - year_start).total_seconds()
        return date.year + seconds_into_year / year_length

    def get_midpoint(self, dep: Point, arr: Point) -> Point:
        """Calculate geographic midpoint between two points."""
        lat1, lon1 = math.radians(dep.lat), math.radians(dep.long)
        lat2, lon2 = math.radians(arr.lat), math.radians(arr.long)
        
        x1, y1, z1 = math.cos(lat1) * math.cos(lon1), math.cos(lat1) * math.sin(lon1), math.sin(lat1)
        x2, y2, z2 = math.cos(lat2) * math.cos(lon2), math.cos(lat2) * math.sin(lon2), math.sin(lat2)
        
        x, y, z = (x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2
        lon = math.atan2(y, x)
        hyp = math.sqrt(x * x + y * y)
        lat = math.atan2(z, hyp)
        
        return Point(round(math.degrees(lat), 4), round(math.degrees(lon), 4))

    def get_route_magnitude(self, dep: Point, arr: Point, unit: str = 'km') -> float:
        """Calculate great-circle distance between two points."""
        R = 6371.0 if unit == 'km' else 3440.1 if unit == 'nm' else 3958.8
        lat1, lon1 = math.radians(dep.lat), math.radians(dep.long)
        lat2, lon2 = math.radians(arr.lat), math.radians(arr.long)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return round(distance, 2)

    @staticmethod
    def calculate_groundspeed(tas: float, course_deg: float, wind_speed: float, wind_dir_deg: float) -> float:
        """Calculate ground speed given TAS, course, wind speed, and wind direction."""
        tc_rad = math.radians(course_deg)
        wd_rad = math.radians(wind_dir_deg)
        wca_rad = math.asin((wind_speed / tas) * math.sin(wd_rad - tc_rad))
        gs = tas * math.cos(wca_rad) - wind_speed * math.cos(wd_rad - tc_rad)
        return round(gs, 2)

    @staticmethod
    def calculate_etp(distance: float, gs_return: float, gs_outbound: float) -> Tuple[float, float]:
        """Calculate Equi-Time Point (ETP) distance and time."""
        etp_distance = (distance * gs_return) / (gs_outbound + gs_return)
        time_to_etp = etp_distance / gs_outbound
        return round(etp_distance, 2), round(time_to_etp * 60, 2)