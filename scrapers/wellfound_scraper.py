from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time


def scrape_wellfound():
    """
    Scrape job listings from Wellfound (formerly AngelList).
    
    Returns:
        List of job dictionaries with role, company, location, etc.
    """
    jobs = []
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Navigate to Wellfound jobs page
        driver.get("https://wellfound.com/jobs")
        time.sleep(5)
        
        # Wellfound uses dynamic loading, so we'll try to find job cards
        # Note: This is a basic implementation and may need adjustment based on site structure
        cards = driver.find_elements(By.CSS_SELECTOR, "[data-test='job-item']")
        
        print(f"Cards Found: {len(cards)}")
        
        for card in cards[:10]:  # Limit to first 10 jobs
            try:
                try:
                    role = card.find_element(By.CSS_SELECTOR, "[data-test='job-title']").text.strip()
                except:
                    role = "N/A"
                
                try:
                    company = card.find_element(By.CSS_SELECTOR, "[data-test='company-name']").text.strip()
                except:
                    company = "N/A"
                
                try:
                    location = card.find_element(By.CSS_SELECTOR, "[data-test='location']").text.strip()
                except:
                    location = "N/A"
                
                jobs.append({
                    "role": role,
                    "company": company,
                    "location": location,
                    "source": "Wellfound"
                })
                
            except Exception as e:
                print(f"Error parsing card: {e}")
        
        driver.quit()
        return jobs
        
    except Exception as e:
        print(f"Error scraping Wellfound: {e}")
        return []


if __name__ == "__main__":
    jobs = scrape_wellfound()
    
    print(f"\nTotal Jobs: {len(jobs)}\n")
    
    for job in jobs:
        print(job)