try:
    import unzip_requirements
except ImportError:
    pass

from typing import Dict, Any
from math import cos

import requests

LambdaDict = Dict[str, Any]


def find_interesting_things(event: LambdaDict, context: LambdaDict) -> LambdaDict:
    """
    Function do query OpenStreetMap

    :param event: Input AWS Lambda event dict
    :param context: Input AWS Lambda context dict
    :return: Output AWS Lambda dict
    """
    # Decode the request
    request_body = event.get('body')
    center_lat = float(request_body['lat'])
    center_lon = float(request_body['lon'])
    search_radius = float(request_body['distance'])

    # Make bounding box (south, west, north, east)
    # Latitude: 1 deg = 110.574 km
    # Longitude: 1 deg = 111.320*cos(latitude) km
    center_lat_rad = center_lat * 3.141_592_653_589_79 / 180.0
    offset_lat = search_radius / 110.574
    offset_lon = search_radius / (111.320 * cos(center_lat_rad))

    # Make a 1km box around the center point
    bounding_box = (
        center_lat - offset_lat,
        center_lon - offset_lon,
        center_lat + offset_lat,
        center_lon + offset_lon,
    )

    # Set up the Overpass query and perform the request
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = (
        f'[out:json];(node["amenity"]{bounding_box};'
        f'way["amenity"]{bounding_box};'
        f'relation["amenity"]{bounding_box};);out;'
    )
    response = requests.get(overpass_url, params={"data": overpass_query})
    data = response.json()

    # Parse out interesting amenities
    bad_amenities = [
        'parking',
        'toilets',
        'shelter'
    ]
    interesting_things = dict()
    for element in data['elements']:
        if element['tags']['amenity'] not in bad_amenities:
            # Try catches for dict elements
            # If NO NAME or NO AMENITY TYPE appears, probably blacklist in bad_amenities
            try:
                name = element['tags']['name']
            except KeyError:
                continue
            try:
                amenity_type = element['tags']['amenity']
            except KeyError:
                continue

            # Add entry to return dictionary
            interesting_things.update(
                {
                    name: amenity_type
                }
            )

    result = {
        'statusCode': 200,
        'body': interesting_things
    }
    return result
