import json
import time
from playwright.sync_api import sync_playwright

SITES = [
    {"name": "Landor", "url": "https://landor.com/work"},
    {"name": "Interbrand", "url": "https://www.interbrand.com/work/"}
]

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    results = []
    
    for site in SITES:
        try:
            print(f"Scraping {site['name']}...")
            # 사이트 접속 후 강제로 넉넉하게 5초 대기 (로딩 문제 해결)
            page.goto(site['url'], wait_until="domcontentloaded")
            time.sleep(5)
            
            for i in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                print(f"스크롤 내리는 중... ({i+1}/5)")
                time.sleep(3)
            
            # 구조에 상관없이 '이미지(img)를 포함한 링크(a)'를 싹 다 긁어옵니다.
            items = page.locator("a:has(img)").element_handles()
            print(f"{site['name']}에서 총 {len(items)}개의 요소를 발견했습니다.")
            
            for item in items:
                try:
                    img_element = item.query_selector("img")
                    img_url = img_element.get_attribute("src") if img_element else ""
                    
                    link = item.get_attribute("href")
                    if not link: continue
                    
                    if not link.startswith("http"):
                        from urllib.parse import urljoin
                        link = urljoin(site['url'], link)
                        
                    # 텍스트가 없으면 이미지의 대체 텍스트(alt)를 제목으로 씁니다.
                    title = item.inner_text().strip()
                    if not title:
                        title = img_element.get_attribute("alt") if img_element else "포트폴리오"
                    title = title.replace("\n", " ")[:50] # 너무 길면 자르기
                    
                    # 로고 같은 불필요한 이미지 필터링
                    if "logo" in img_url.lower() or "icon" in img_url.lower():
                        continue
                        
                    results.append({
                        "agency": site['name'],
                        "title": title,
                        "image": img_url,
                        "link": link
                    })
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"사이트 접속 에러 {site['name']}: {e}")

    browser.close()
    
    # 중복 수집 방지 (동일한 링크 제거)
    unique_results = list({each['link']: each for each in results}.values())
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(unique_results, f, ensure_ascii=False, indent=4)
        
    print(f"총 {len(unique_results)}개의 포트폴리오를 수집했습니다.")

with sync_playwright() as playwright:
    run(playwright)
