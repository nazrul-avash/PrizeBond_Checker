import requests
from bs4 import BeautifulSoup

URL = "https://prizebond.ird.gov.bd/hybrid_action_b2e.php"

QUERY = "790431"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://prizebond.ird.gov.bd/SingleNumber.php",
}

def run():
    print("Sending range query...")

    r = requests.post(URL, data={"from": QUERY}, headers=headers, timeout=30)

    print("STATUS:", r.status_code)

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    print("\n===== RESULT =====\n")
    print(text[:2000])


if __name__ == "__main__":
    run()