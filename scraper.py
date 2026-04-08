import json
import time
import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

SITES = [
    {"name": "Landor", "url": "https://landor.com"},
    {"name": "Interbrand", "url": "https://www.interbrand.com"}
]

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    # 실제 디자이너가 보는 것처럼 고해상도 설정
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    all_projects = []

    for site in SITES:
        try:
            print(f"\n--- {site['name']} 탐색 시작 ---")
            page.goto(site['url'], wait_until="networkidle")
            time.sleep(3)

            # 1. 'Work/Project' 목록 페이지 주소 찾기
            keywords = ['work', 'projects', 'cases', 'portfolio', 'stories']
            links = page.locator("a").element_handles()
            work_url = None
            
            for link in links:
                href = link.get_attribute("href")
                if href and any(kw in href.lower() for kw in keywords):
                    work_url = urljoin(site['url'], href)
                    break
            
            if not work_url: work_url = site['url'] # 못 찾으면 홈에서 시도
            
            print(f"목록 페이지 접속: {work_url}")
            page.goto(work_url, wait_until="networkidle")
            
            # 2. 프로젝트 카드들 추출 (이미지가 포함된 링크 위주)
            for _ in range(3): # 스크롤하여 더 많이 로드
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

            project_links = []
            elements = page.locator("a:has(img)").element_handles()
            
            for el in elements:
                href = el.get_attribute("href")
                if href:
                    full_url = urljoin(work_url, href)
                    # 목록 페이지 자체이거나 외부 링크면 제외
                    if full_url != work_url and urlparse(full_url).netloc == urlparse(site['url']).netloc:
                        if full_url not in [p['link'] for p in project_links]:
                            project_links.append(full_url)

            print(f"총 {len(project_links)}개의 프로젝트를 발견했습니다. 상위 10개를 캡처합니다.")

            # 3. 각 프로젝트 상세 페이지 접속 및 전체 캡처
            for i, p_url in enumerate(project_links[:10]):
                try:
                    detail_page = context.new_page()
                    detail_page.goto(p_url, wait_until="networkidle")
                    time.sleep(4) # 애니메이션 대기

                    title = detail_page.title().split('|')[0].strip()
                    clean_title = "".join([c for c in title if c.isalnum()]).rstrip()
                    file_name = f"screenshots/{site['name']}_{i}_{clean_title}.png"
                    
                    # 썸네일용 작은 이미지 추출
                    thumb_el = detail_page.locator("img").first
                    thumbnail = thumb_el.get_attribute("src") if thumb_el else ""

                    # 전체 페이지 캡처
                    detail_page.screenshot(path=file_name, full_page=True)
                    print(f"성공: {title}")
                    
                    all_projects.append({
                        "agency": site['name'],
                        "title": title,
                        "link": p_url,
                        "thumbnail": thumbnail,
                        "screenshot_local": file_name
                    })
                    detail_page.close()
                except Exception as e:
                    print(f"상세 페이지 캡처 실패: {e}")

        except Exception as e:
            print(f"사이트 접속 에러: {e}")

    browser.close()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_projects, f, ensure_ascii=False, indent=4)

with sync_playwright() as playwright:
    run(playwright)
