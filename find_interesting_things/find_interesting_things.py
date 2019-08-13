import requests
from pprint import pprint
from math import cos


def find_interesting_things(event, context):
    """ Function to query OpenStreetMaps"""
    # Make bounding box (south, west, north, east)
    # Latitude: 1 deg = 110.574 km
    # Longitude: 1 deg = 111.320*cos(latitude) km
    center_lat = event["latitude"]
    center_lon = event["longitude"]
    center_lat_rad = center_lat * 3.141_592_653_589_79 / 180.0
    offset_lat = 0.5 / 110.574
    offset_lon = 0.5 / (111.320 * cos(center_lat_rad))

    # Make a 1km box around the center point
    # e.g. pubs in London (53.2987342,-6.3870259,53.4105416,-6.1148829)
    bounding_box = (
        center_lat - offset_lat,
        center_lon - offset_lon,
        center_lat + offset_lat,
        center_lon + offset_lon,
    )

    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = (
        f'[out:json];(node["amenity"]{bounding_box};'
        f'way["amenity"]{bounding_box};'
        f'relation["amenity"]{bounding_box};);out;'
    )
    response = requests.get(overpass_url, params={"data": overpass_query})
    data = response.json()

    return data


if __name__ == "__main__":
    test = find_interesting_things({"latitude": 35.6870, "longitude": -105.9378}, "")
    pprint(test)
