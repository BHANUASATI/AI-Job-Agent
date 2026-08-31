from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time


def scrape_internshala():
    jobs = []

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get("https://internshala.com/internships/")
    time.sleep(5)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.individual_internship")

    print(f"Cards Found: {len(cards)}")

    for card in cards:
        try:
            try:
                role = card.find_element(
                    By.CSS_SELECTOR,
                    ".job-internship-name a"
                ).text.strip()
            except:
                role = "N/A"

            try:
                company = card.find_element(
                    By.CSS_SELECTOR,
                    ".company-name"
                ).text.strip()
            except:
                company = "N/A"

            try:
                location = card.find_element(
                    By.CSS_SELECTOR,
                    ".locations span a"
                ).text.strip()
            except:
                location = "N/A"

            try:
                stipend = card.find_element(
                    By.CSS_SELECTOR,
                    ".stipend"
                ).text.strip()
            except:
                stipend = "N/A"

            jobs.append({
                "role": role,
                "company": company,
                "location": location,
                "stipend": stipend
            })

        except Exception as e:
            print("Error:", e)

    driver.quit()
    return jobs


if __name__ == "__main__":
    jobs = scrape_internshala()

    print(f"\nTotal Jobs: {len(jobs)}\n")

    for job in jobs[:10]:
        print(job)