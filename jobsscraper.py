from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time

def extract_jobs_anti_bot(target_pages=10):
    all_jobs = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        
        # navigator.webdriver বাইপাস
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        
        print("Opening Indeed...")
        page.goto("https://www.indeed.com/jobs?q=web+developer&l=London", timeout=60000)
        
        for current_page in range(1, target_pages + 1):
            print(f"\n--- Scraping Page {current_page} of {target_pages} ---")
            
            time.sleep(4)
            
            # যদি Cloudflare Captcha চলে আসে, তবে আপনাকে ১৫ সেকেন্ড সময় দেবে ক্যাপচা পূরণ করার
            if "Verify you are human" in page.content() or "Additional Verification" in page.content():
                print("⚠️ Cloudflare Captcha এসেছে! দয়া করে ব্রাউজারে হাত দিয়ে ক্যাপচা টিক দিন (১৫ সেকেন্ড সময় আছে)...")
                time.sleep(15)
            
            # পেজ স্ক্রলিং
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            soup = BeautifulSoup(page.content(), "html.parser")
            job_cards = soup.find_all("div", class_="cardOutline") or \
                        soup.find_all("div", class_="job_seen_beacon") or \
                        soup.find_all("td", class_="resultContent")
            
            extracted_count = 0
            for card in job_cards:
                title_elem = card.find("h2", class_="jobTitle") or card.find("a")
                title = title_elem.get_text(strip=True) if title_elem else "N/A"
                
                company_elem = card.find("span", {"data-testid": "company-name"}) or card.find("span", class_="companyName")
                company = company_elem.get_text(strip=True) if company_elem else "N/A"
                
                salary_elem = card.find("div", {"data-testid": "attribute_snippet_testid"}) or \
                              card.find("div", class_="salary-snippet-container") or \
                              card.find("div", class_="metadata")
                salary = salary_elem.get_text(strip=True) if salary_elem else "Not Specified"
                
                summary_elem = card.find("div", class_="underLine") or \
                               card.find("div", class_="job-snippet") or \
                               card.find("ul", class_="css-152e2at")
                summary = summary_elem.get_text(strip=True).replace("\n", " ") if summary_elem else "N/A"
                
                if title != "N/A" and title != "":
                    all_jobs.append({
                        "Title": title,
                        "Company": company,
                        "Salary": salary,
                        "Summary": summary
                    })
                    extracted_count += 1
            
            print(f"Jobs found on Page {current_page}: {extracted_count}")

            if current_page < target_pages:
                try:
                    next_button = page.locator('a[aria-label="Next Page"], a[data-testid="pagination-page-next"], a[aria-label="Next"]')
                    
                    if next_button.count() > 0 and next_button.first.is_visible():
                        print("Clicking Next Page button...")
                        next_button.first.scroll_into_view_if_needed()
                        time.sleep(2)
                        next_button.first.click()
                    else:
                        print("Next button not found, loading URL directly...")
                        time.sleep(3)
                        start_num = current_page * 10
                        next_url = f"https://www.indeed.com/jobs?q=web+developer&l=London&start={start_num}"
                        page.goto(next_url)
                        
                except Exception as e:
                    print("Error moving to next page:", e)
                    break
                    
        browser.close()
        return all_jobs

jobs_data = extract_jobs_anti_bot(target_pages=10)

df = pd.DataFrame(jobs_data)
df.to_csv("indeed_jobs.csv", index=False)

print(f"\nTotal jobs successfully extracted: {len(jobs_data)}")
            
            