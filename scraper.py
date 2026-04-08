import json
import time
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

SITES = [
    {"name": "Landor", "work_url": "https://landor.com/en/our-work/"},
    {"name": "Interbrand", "work_url": "https://www.interbrand.com/work/"}
]

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    all_projects = []

    for site in SITES:
        try:
            print(f"\n--- {site['name']} 전체 수집 시작 ---")
            work_url = site['work_url']
            page.goto(work_url, wait_until="networkidle")
            time.sleep(5) # 초기 로딩 대기
            
            # [업그레이드] 무한 스크롤: 더 이상 새로운 내용이 안 나올 때까지 내림
            last_height = page.evaluate("document.body.scrollHeight")
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3) # 로딩 대기
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height: # 바닥에 도달함
                    break
                last_height = new_height
                print(f"스크롤 중... 현재 높이: {new_height}")

            # 하위 프로젝트 링크 수집
            links = page.locator("a").element_handles()
            project_urls = set()
            for link in links:
                href = link.get_attribute("href")
                if href:
                    full_url = urljoin(work_url, href)
                    if full_url.startswith(work_url) and len(full_url) > len(work_url):
                        if "#" not in full_url and "?" not in full_url:
                            project_urls.add(full_url)

            project_urls = list(project_urls)
            print(f"확인된 총 프로젝트 개수: {len(project_urls)}개")

            # [업그레이드] [:10] 제한 삭제 -> 발견된 모든 링크 수집
            for i, p_url in enumerate(project_urls):
                try:
                    print(f"[{i+1}/{len(project_urls)}] 캡처 중: {p_url}")
                    detail_page = context.new_page()
                    detail_page.goto(p_url, wait_until="networkidle", timeout=90000)
                    time.sleep(4) 
                    
                    title = detail_page.title().split('|')[0].split('-')[0].strip()
                    if not title: title = f"Project_{i}"
                    
                    thumbnail = ""
                    imgs = detail_page.locator("img").element_handles()
                    for img in imgs:
                        src = img.get_attribute("src")
                        if src and "logo" not in src.lower() and "icon" not in src.lower():
                            thumbnail = urljoin(p_url, src)
                            break

                    clean_title = "".join([c for c in title if c.isalnum()]).rstrip()
                    file_name = f"screenshots/{site['name']}_{i}_{clean_title}.png"
                    
                    detail_page.screenshot(path=file_name, full_page=True)
                    
                    all_projects.append({
                        "agency": site['name'],
                        "title": title,
                        "link": p_url,
                        "thumbnail": thumbnail,
                        "screenshot_local": file_name
                    })
                    detail_page.close()
                except Exception as e:
                    print(f"패스 ({p_url}): {e}")

        except Exception as e:
            print(f"접속 에러: {e}")

    browser.close()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_projects, f, ensure_ascii=False, indent=4)
    print(f"\n완료! 총 {len(all_projects)}개가 수집되었습니다.")

with sync_playwright() as playwright:
    run(playwright)
