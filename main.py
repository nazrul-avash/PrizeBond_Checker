import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from bs4 import BeautifulSoup

from datetime import datetime

today = datetime.utcnow()

# last day check
next_day = today.replace(day=today.day + 1) if today.day < 28 else None

if next_day is not None:
    print("Not last day of month, skipping")
    exit()

BB_URL = "https://www.bb.org.bd/en/index.php/investfacility/prizebond/pbsearch.php"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHEET_ID = os.environ["SHEET_ID"]
GOOGLE_CREDS = os.environ["GOOGLE_CREDENTIALS_JSON"]


# ---------------- TELEGRAM ----------------
def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=30,
    )


# ---------------- GOOGLE SHEET ----------------
def get_entries():
    creds = Credentials.from_service_account_info(
        eval(GOOGLE_CREDS),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )

    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).sheet1

    return [x.strip() for x in sheet.col_values(1) if x.strip()]


# ---------------- FETCH ----------------
def fetch_results(search_string):
    session = requests.Session()

    # load page (cookies/session safety)
    session.get(BB_URL, timeout=30)

    payload = {
        "bondnumber": search_string
    }

    r = session.post(BB_URL, data=payload, timeout=60)
    return r.text


# ---------------- PARSER ----------------
def parse_winners(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    if "No Match Found" in text:
        return []

    if "Congratulations" not in text:
        return []

    rows = soup.select("table tr")

    winners = []

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        if len(cols) >= 4 and cols[0].isdigit():
            winners.append({
                "number": cols[0],
                "draw": cols[1],
                "prize": cols[2],
                "amount": cols[3],
            })

    return winners


# ---------------- MAIN ----------------
def main():
    entries = get_entries()
    search_string = ",".join(entries)

    html = fetch_results(search_string)
    winners = parse_winners(html)

    if len(winners) > 0:
        message = "🎉 PRIZE BOND WINNER FOUND!\n\n"

        for w in winners[:20]:
            message += (
                f"Number: {w['number']}\n"
                f"Draw: {w['draw']}\n"
                f"Prize: {w['prize']}\n"
                f"Amount: {w['amount']}\n\n"
            )

        message += f"Total Wins: {len(winners)}"

    else:
        message = (
            "❌ No Prize Bond Matches Found\n\n"
            f"Searched Entries: {len(entries)}\n"
            "Status: All clear"
        )

    send_telegram(message)


if __name__ == "__main__":
    main()