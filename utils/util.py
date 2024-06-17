import requests
import os

from dotenv import load_dotenv

load_dotenv()


def get_all_clothes():
    url = os.getenv("API_KEY") + "/api/clothing/all"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    return response.json()
