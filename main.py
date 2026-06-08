import os
import csv
import requests
from io import StringIO
from bs4 import BeautifulSoup

# ---------------- ENV ----------------
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SHEET_ID = "1A-zGg9WT8F33DAhmWbFrGzch06AzDYkvy4v_okNO2wM"

URL = "https://prizebond.ird.gov.bd/hybrid_action_b2e.php"


# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=30,
    )


# ---------------- READ SHEET ----------------
def get_inputs():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    f = StringIO(r.text)
    reader = csv.reader(f)

    return [row[0].strip() for row in reader if row and row[0].strip()]


# ---------------- FETCH ----------------
def fetch_result(query):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://prizebond.ird.gov.bd/SingleNumber.php",
    }

    r = requests.post(URL, data={"from": query}, headers=headers, timeout=30)
    return r.text


# ---------------- EXTRACT WINNERS ----------------
def extract_winners(html):
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if not table:
        return []

    winners = []

    for row in table.find_all("tr")[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        if len(cols) >= 1:
            winners.append(cols[0])

    return winners


# ---------------- MAIN ----------------
def main():
    inputs = get_inputs()

    all_winners = set()  # 🔥 deduplication

    for query in inputs:
        print(f"Checking: {query}")

        html = fetch_result(query)
        winners = extract_winners(html)

        # store globally
        for w in winners:
            all_winners.add(w)

    # ---------------- FINAL RESULT ----------------
    if all_winners:
        msg = "🎉 PRIZE BOND WINNERS FOUND!\n\n"
        msg += "Winning Bonds:\n\n"

        for w in sorted(all_winners):
            msg += f"- {w}\n"

        msg += f"\nTotal Unique Winners: {len(all_winners)}"

    else:
        msg = "❌ No Prize Bond Winners Found"

    send_telegram(msg)
    print(msg)


if __name__ == "__main__":
    main()