import json
import time
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

SITES = [
    {"name": "Landor", "url": "https://landor.com/work", "card": "article"},
    {"name": "Interbrand", "url": "https://www.interbrand.com/work/", "card": ".card, article"}
]

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    results = []

    # 스크린샷 저장 폴더 생성
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    for site in SITES:
        try:
            print(f"\n--- {site['name']} 프로젝트 수집 시작 ---")
            page.goto(site['url'], wait_until="networkidle")
            
            # 프로젝트 로딩을 위해 스크롤
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

            # 프로젝트 카드 찾기
            cards = page.locator(site['card']).element_handles()
            print(f"{len(cards)}개의 프로젝트 후보를 찾았습니다.")

            for i, card in enumerate(cards[:15]): # 초기 세팅 시 15개 정도가 적당합니다.
                try:
                    # 1. 제목 및 링크 추출
                    link_element = card.query_selector("a")
                    if not link_element: continue
                    
                    project_url = urljoin(site['url'], link_element.get_attribute("href"))
                    title = card.inner_text().split('\n')[0].strip() or f"Project_{i}"
                    
                    # 2. 대표 썸네일 추출
                    img_element = card.query_selector("img")
                    thumbnail = img_element.get_attribute("src") if img_element else ""

                    # 3. 상세 페이지 전체 캡처 (가장 중요한 부분!)
                    print(f"[{i+1}] 상세 페이지 캡처 중: {title}")
                    detail_page = context.new_page()
                    detail_page.goto(project_url, wait_until="networkidle")
                    time.sleep(3) # 애니메이션 대기
                    
                    # 파일명에 특수문자 제거
                    clean_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).rstrip()
                    screenshot_path = f"screenshots/{site['name']}_{clean_title}.png"
                    
                    # 전체 페이지 스크린샷 (full_page=True)
                    detail_page.screenshot(path=screenshot_path, full_page=True)
                    detail_page.close()

                    results.append({
                        "agency": site['name'],
                        "title": title,
                        "link": project_url,
                        "thumbnail": thumbnail,
                        "screenshot_local": screenshot_path
                    })
                except Exception as e:
                    print(f"항목 수집 에러: {e}")

        except Exception as e:
            print(f"사이트 접속 에러 {site['name']}: {e}")

    browser.close()
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

with sync_playwright() as playwright:
    run(playwright)
