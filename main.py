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


# ---------------- READ GOOGLE SHEET ----------------
def get_input():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    f = StringIO(r.text)
    reader = csv.reader(f)

    for row in reader:
        if row and row[0].strip():
            return row[0].strip()

    return None


# ---------------- FETCH IRD ----------------
def fetch_result(query):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://prizebond.ird.gov.bd/SingleNumber.php",
    }

    r = requests.post(URL, data={"from": query}, headers=headers, timeout=30)
    return r.text


# ---------------- PARSE ONLY MATCHED NUMBERS ----------------
def extract_matches(html, query):
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")

    if not table:
        return []

    matches = []

    rows = table.find_all("tr")

    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        if len(cols) >= 1:
            num = cols[0]

            # ONLY check against your input
            if query.replace("-", "").replace(",", "") in num:
                matches.append(num)

    return matches


# ---------------- MAIN ----------------
def main():
    query = get_input()

    if not query:
        send_telegram("❌ No input found in Google Sheet")
        return

    html = fetch_result(query)

    matches = extract_matches(html, query)

    if matches:
        msg = "🎉 PRIZE BOND MATCH FOUND!\n\n"
        msg += f"Input: {query}\n\n"

        for m in matches:
            msg += f"- {m}\n"

        msg += f"\nTotal Matches: {len(matches)}"

    else:
        msg = f"❌ No Match Found\nInput: {query}"

    send_telegram(msg)
    print(msg)


if __name__ == "__main__":
    main()