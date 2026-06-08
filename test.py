from playwright.sync_api import sync_playwright

BB_URL = "https://www.bb.org.bd/en/index.php/investfacility/prizebond"

QUERY = "0790001~0799999,1234567"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set True later
        page = browser.new_page()

        print("Opening page...")
        page.goto(BB_URL, timeout=60000)

        print("Filling input...")
        page.fill("input[name='bondnumber']", QUERY)

        print("Submitting...")
        page.keyboard.press("Enter")

        print("Waiting for result...")
        page.wait_for_timeout(5000)

        html = page.content()

        print("\n===== RESPONSE PREVIEW =====\n")
        print(html[:2000])

        browser.close()


if __name__ == "__main__":
    run()