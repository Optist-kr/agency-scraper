import json
import time
from playwright.sync_api import sync_playwright

SITES = [
    {"name": "Landor", "url": "https://landor.com/work", "selector": "article"},
    {"name": "Interbrand", "url": "https://www.interbrand.com/work/", "selector": ".card, article"}
]

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    
    results = []
    
    for site in SITES:
        try:
            print(f"Scraping {site['name']}...")
            page.goto(site['url'], wait_until="networkidle")
            
            # [수정된 부분] 초기 세팅을 위해 화면을 아래로 7번 반복해서 스크롤합니다.
            # (에이전시 사이트들은 스크롤을 내려야 예전 포트폴리오가 로딩되기 때문입니다)
            for i in range(7):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                print(f"스크롤 내리는 중... ({i+1}/7)")
                time.sleep(3) # 이미지 로딩을 기다리는 시간
            
            items = page.locator(site['selector']).element_handles()
            print(f"{site['name']}에서 총 {len(items)}개의 요소를 발견했습니다.")
            
            # [수정된 부분] [:5] 제한을 없애고 찾은 모든 항목을 수집합니다.
            for item in items: 
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
                    pass
                    
        except Exception as e:
            print(f"사이트 접속 에러 {site['name']}: {e}")

    browser.close()
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
        
    print(f"총 {len(results)}개의 포트폴리오를 수집했습니다.")

with sync_playwright() as playwright:
    run(playwright)
