import os
import re
import requests
from bs4 import BeautifulSoup

# ---------------- ENV ----------------
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = "https://prizebond.ird.gov.bd/hybrid_action_b2e.php"


# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=30,
    )


# ---------------- PARSE WINNERS ----------------
def extract_winners(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # find all 7-digit numbers in result page
    numbers = re.findall(r"\b\d{7}\b", text)

    # remove duplicates
    return sorted(set(numbers))


# ---------------- FETCH IRD ----------------
def fetch_result(query):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://prizebond.ird.gov.bd/SingleNumber.php",
    }

    data = {
        "from": query
    }

    r = requests.post(URL, data=data, headers=headers, timeout=30)
    return r.text


# ---------------- MAIN ----------------
def main():
    # Example input (later replace with Google Sheet)
    query = "0790061-0799965"

    html = fetch_result(query)

    winners = extract_winners(html)

    if winners:
        msg = "🎉 PRIZE BOND MATCH FOUND!\n\n"
        msg += "Winning Numbers:\n\n"

        for w in winners[:20]:  # limit spam
            msg += f"- {w}\n"

        msg += f"\nTotal Matches: {len(winners)}"

    else:
        msg = "❌ No Prize Bond Matches Found"

    send_telegram(msg)
    print(msg)


if __name__ == "__main__":
    main()