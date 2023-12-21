import configparser
from urllib.parse import quote

import requests

# 設定 Google Maps API 金鑰
config = configparser.ConfigParser()
config.read("../LINEBOT_API_KEY/googlemap_api.ini")
google_maps_api_key = config.get("googlemap", "key")


def get_address_from_coordinates(latitude, longitude):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{latitude},{longitude}",
        "key": google_maps_api_key,
    }

    response = requests.get(base_url, params=params)

    data = response.json()

    if data["status"] == "OK":
        if len(data["results"]) > 0:
            address = data["results"][0]["formatted_address"]
            return address
    return None


def get_directions(start_coordinates, end_address):
    # 取得起點地址
    start_address = get_address_from_coordinates(*start_coordinates)

    if start_address:
        base_url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": start_address,
            "destination": end_address,
            "key": google_maps_api_key,
        }

        response = requests.get(base_url, params=params)
        data = response.json()

        if data["status"] == "OK":
            # 取得導航連結
            directions_url = f"https://www.google.com/maps/dir/?api=1&origin={start_address}&destination={end_address}"
            # 編碼URL
            directions_url = quote(directions_url, safe=":/&=?")
            return directions_url
    return None


if __name__ == "__main__":
    start_coordinates = (25.03413655927905, 121.54343435506429)
    end_address = "TRUEWIN初韻 (永和福和店),新北市永和區福和路264號"
    url = get_directions(start_coordinates, end_address)
    print(url)
