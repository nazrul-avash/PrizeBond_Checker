import os
import requests
import csv
from io import StringIO
from bs4 import BeautifulSoup
import re

SHEET_ID = os.environ["SHEET_ID"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

BB_URL = "https://www.bb.org.bd/en/index.php/investfacility/prizebond"


# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=30,
    )


# ---------------- GOOGLE SHEET (CSV) ----------------
def get_entries():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

    r = requests.get(url, timeout=30)
    r.raise_for_status()

    f = StringIO(r.text)
    reader = csv.reader(f)

    return [row[0].strip() for row in reader if row and row[0].strip()]


# ---------------- FETCH BB RESULT ----------------
def fetch_result(query):
    session = requests.Session()
    session.get(BB_URL, timeout=30)

    payload = {"bondnumber": query}

    r = session.post(BB_URL, data=payload, timeout=60)
    return r.text


# ---------------- PARSER (BULLETPROOF) ----------------
def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    text_norm = re.sub(r"\s+", " ", text.lower())

    # ❌ NO MATCH CASE
    if "no match found" in text_norm:
        return False, 0, []

    # ✅ MATCH COUNT
    match = re.search(r"(\d+)\s+match found", text_norm)
    count = int(match.group(1)) if match else 0

    # ✅ TABLE PARSING (WINNING NUMBERS)
    winners = []
    table = soup.find("table")

    if table:
        rows = table.find_all("tr")

        for r in rows[1:]:
            cols = [c.get_text(strip=True) for c in r.find_all("td")]

            if len(cols) >= 4 and cols[0].isdigit():
                winners.append({
                    "number": cols[0],
                    "draw": cols[1],
                    "prize": cols[2],
                    "amount": cols[3],
                })

    return True if count > 0 or winners else False, count, winners


# ---------------- MAIN ----------------
def main():
    entries = get_entries()

    query = ",".join(entries)

    html = fetch_result(query)

    found, count, winners = parse(html)

    if found:
        msg = "🎉 PRIZE BOND WINNER FOUND!\n\n"

        if winners:
            for w in winners[:20]:
                msg += (
                    f"Number: {w['number']}\n"
                    f"Draw: {w['draw']}\n"
                    f"Prize: {w['prize']}\n"
                    f"Amount: {w['amount']}\n\n"
                )

            msg += f"Total Winners: {len(winners)}"

        else:
            msg += f"Match Count: {count}"

    else:
        msg = (
            "❌ No Prize Bond Matches Found\n\n"
            f"Searched Entries: {len(entries)}"
        )

    send_telegram(msg)


if __name__ == "__main__":
    main()