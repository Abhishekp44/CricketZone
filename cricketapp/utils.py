# yourapp/utils.py

import requests

API_KEY = "32830b13-a398-4f31-8e3c-f45c48cf681a"
BASE_URL = "https://api.cricapi.com/v1"

def fetch_fixtures():
    url = f"{BASE_URL}/matches"
    params = {
        "apikey": API_KEY,
        "offset": 0
    }
    try:
        response = requests.get(url, params=params)
        return response.json().get("data", [])
    except:
        return []

# def fetch_results():
#     url = f"{BASE_URL}/match_info"
#     # Example match ID required. CricAPI does not return bulk completed matches directly.
#     # This function will be modified to work for specific match_id (when clicking on a match).
#     return []  
