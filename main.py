import os
import requests
import csv
from io import StringIO
from bs4 import BeautifulSoup

SHEET_ID = os.environ["SHEET_ID"]

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

BB_URL = "https://www.bb.org.bd/en/index.php/investfacility/prizebond/pbsearch.php"


# ---------------- TELEGRAM ----------------
def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": message},
        timeout=30,
    )


# ---------------- READ GOOGLE SHEET (CSV) ----------------
def get_entries():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    f = StringIO(r.text)
    reader = csv.reader(f)

    return [row[0].strip() for row in reader if row and row[0].strip()]


# ---------------- SEARCH BB ----------------
def fetch_results(search_string):
    session = requests.Session()

    # load page first (important for cookies/session)
    session.get(BB_URL, timeout=30)

    payload = {
        "bondnumber": search_string
    }

    r = session.post(BB_URL, data=payload, timeout=60)
    return r.text


# ---------------- PARSE RESULT ----------------
def parse_result(html):
    text = BeautifulSoup(html, "html.parser").get_text(separator=" ")

    text = text.lower()

    # normalize spaces
    text = re.sub(r"\s+", " ", text)

    if "no match found" in text:
        return False, 0

    # extract "X match found"
    match = re.search(r"(\d+)\s+match found", text)

    if match:
        return True, int(match.group(1))

    # fallback: if table exists, assume success
    if "number" in text and "draw" in text:
        return True, 1

    return False, 0


# ---------------- MAIN ----------------
def main():
    entries = get_entries()

    search_string = ",".join(entries)

    html = fetch_results(search_string)

    found, count = parse_result(html)

    if found and count > 0:
        message = (
            "🎉 PRIZE BOND WINNER FOUND!\n\n"
            f"Total Matches: {count}\n"
            f"Searched Items: {len(entries)}\n\n"
            "Check details on Bangladesh Bank site."
        )
    else:
        message = (
            "❌ No Prize Bond Matches Found\n\n"
            f"Searched Items: {len(entries)}\n"
            "Status: All clear"
        )

    send_telegram(message)


if __name__ == "__main__":
    main()