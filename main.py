import os
import csv
import requests
from io import StringIO
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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


# ---------------- GOOGLE SHEET CSV ----------------
def get_entries():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    f = StringIO(r.text)
    reader = csv.reader(f)

    return [row[0].strip() for row in reader if row and row[0].strip()]


# ---------------- PLAYWRIGHT SEARCH ----------------
def fetch_result(query):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = browser.new_page()

        page.goto(BB_URL, timeout=60000)

        # input field
        page.fill("input[name='bondnumber']", query)

        # submit form
        page.keyboard.press("Enter")

        # wait for response
        page.wait_for_timeout(5000)

        html = page.content()

        browser.close()

        return html


# ---------------- PARSER ----------------
def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    if "no match found" in text:
        return False, 0, []

    winners = []
    table = soup.find("table")

    if table:
        rows = table.find_all("tr")

        for r in rows[1:]:
            cols = [c.get_text(strip=True) for c in r.find_all("td")]

            if len(cols) >= 4 and cols[0].isdigit():
                winners.append(cols[0])

    if winners:
        return True, len(winners), winners

    return False, 0, []


# ---------------- MAIN ----------------
def main():
    entries = get_entries()
    query = ",".join(entries)

    html = fetch_result(query)
    found, count, winners = parse(html)

    if found:
        msg = "🎉 PRIZE BOND WINNER FOUND!\n\n"

        msg += f"Total Matches: {count}\n\n"

        for w in winners[:20]:
            msg += f"{w}\n"

    else:
        msg = (
            "❌ No Prize Bond Matches Found\n\n"
            f"Searched: {len(entries)} numbers"
        )

    send_telegram(msg)


if __name__ == "__main__":
    main()