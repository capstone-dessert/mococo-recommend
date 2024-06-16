import requests


def get_all_clothes():
    url = "http://squarelab.iptime.org:10000" + "/api/clothing/all"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    return response.json()
