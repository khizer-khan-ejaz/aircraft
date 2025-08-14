import random
import math
from typing import Dict, List, NamedTuple
import logging
from geographiclib.geodesic import Geodesic
import datetime
from pygeomag import GeoMag

geo = GeoMag()

class Point(NamedTuple):
    lat: float
    long: float

class Airport(NamedTuple):
    code: str
    name: str
    lat: float
    long: float
    reference: str

class Navigation:
    def get_track_angle(self, dep, arr, magnetic=True, date=None):
        if not (-90 <= dep.lat <= 90 and -180 <= dep.long <= 180 and 
                -90 <= arr.lat <= 90 and -180 <= arr.long <= 180):
            raise ValueError("Invalid latitude or longitude")
        if (dep.lat, dep.long) == (arr.lat, arr.long):
            return 0.0

        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
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

    def get_magnetic_variation(self, lat, lon, date=None):
        if geo is None:
            print("GeoMag unavailable. Using fallback magnetic variation (-12.0 for New York).")
            return -12.0
        try:
            date = date or datetime.datetime.utcnow()
            dec_year = self.decimal_year(date)
            result = geo.calculate(glat=lat, glon=lon, alt=0, time=dec_year)
            return float(result.dec)
        except Exception as e:
            print(f"Error calculating magnetic variation: {e}")
            return -12.0

    def decimal_year(self, date):
        year_start = datetime.datetime(date.year, 1, 1)
        year_end = datetime.datetime(date.year + 1, 1, 1)
        year_length = (year_end - year_start).total_seconds()
        seconds_into_year = (date - year_start).total_seconds()
        return date.year + seconds_into_year / year_length

    def get_midpoint(self, dep, arr):
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        x1 = math.cos(lat1) * math.cos(lon1)
        y1 = math.cos(lat1) * math.sin(lon1)
        z1 = math.sin(lat1)
        x2 = math.cos(lat2) * math.cos(lon2)
        y2 = math.cos(lat2) * math.sin(lon2)
        z2 = math.sin(lat2)
        
        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        z = (z1 + z2) / 2
        
        lon = math.atan2(y, x)
        hyp = math.sqrt(x * x + y * y)
        lat = math.atan2(z, hyp)
        
        mid_lat = math.degrees(lat)
        mid_lon = math.degrees(lon)
        
        return Point(round(mid_lat, 4), round(mid_lon, 4))

    def get_route_magnitude(self, dep, arr, unit='km'):
        R = 6371.0
        
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        if unit == 'nm':
            distance *= 0.539957
        elif unit == 'mi':
            distance *= 0.621371
            
        return round(distance, 2)