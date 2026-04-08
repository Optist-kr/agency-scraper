import json
import time
from playwright.sync_api import sync_playwright

SITES = [
    {"name": "Landor", "url": "https://landor.com/work", "selector": "article"},
    {"name": "Interbrand", "url": "https://www.interbrand.com/work/", "selector": ".card, article"} # 실제 돔 구조에 맞춰 미세조정 필요
]

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    
    results = []
    
    for site in SITES:
        try:
            print(f"Scraping {site['name']}...")
            page.goto(site['url'], wait_until="networkidle")
            
            # SPA 로딩을 위해 약간의 스크롤 및 대기
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
            
            items = page.locator(site['selector']).element_handles()
            
            for item in items[:5]: # 최신 5개만 가져오기
                try:
                    title = item.query_selector("h2, h3").inner_text() if item.query_selector("h2, h3") else "No Title"
                    img_element = item.query_selector("img")
                    img_url = img_element.get_attribute("src") if img_element else ""
                    link_element = item.query_selector("a")
                    link = link_element.get_attribute("href") if link_element else site['url']
                    
                    if not link.startswith("http"):
                        from urllib.parse import urljoin
                        link = urljoin(site['url'], link)
                        
                    results.append({
                        "agency": site['name'],
                        "title": title.strip(),
                        "image": img_url,
                        "link": link
                    })
                except Exception as e:
                    print(f"아이템 파싱 에러: {e}")
                    
        except Exception as e:
            print(f"사이트 접속 에러 {site['name']}: {e}")

    browser.close()
    
    # JSON으로 저장
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
        
    print(f"총 {len(results)}개의 포트폴리오를 수집했습니다.")

with sync_playwright() as playwright:
    run(playwright)
