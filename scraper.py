import json
import time
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

SITES = [
    # 시작 주소를 아예 Work/Portfolio 목록 페이지로 고정하여 정확도를 100%로 높입니다.
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
            print(f"\n--- {site['name']} 탐색 시작 ---")
            work_url = site['work_url']
            print(f"목록 페이지 접속: {work_url}")
            
            page.goto(work_url, wait_until="networkidle")
            time.sleep(3)
            
            # 스크롤을 끝까지 내려서 숨겨진 프로젝트 링크들을 모두 화면에 띄웁니다.
            for i in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

            # 1. 페이지 안의 모든 링크(a 태그)를 싹 다 가져옵니다.
            links = page.locator("a").element_handles()
            project_urls = set() # 중복 링크를 방지하기 위해 set 사용

            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href: continue
                    
                    full_url = urljoin(work_url, href)
                    
                    # [핵심 로직] 하위 프로젝트 페이지(ex: /work/lego/)만 완벽하게 걸러내기
                    # 조건 1: 주소가 work_url로 시작해야 함
                    # 조건 2: 주소 길이가 work_url보다 무조건 길어야 함 (자기 자신 제외)
                    # 조건 3: 페이지 넘기기(?page=)나 필터링(#) 기호가 없어야 함
                    if full_url.startswith(work_url) and len(full_url) > len(work_url):
                        if "#" not in full_url and "?" not in full_url:
                            project_urls.add(full_url)
                except Exception:
                    pass

            project_urls = list(project_urls)
            print(f"총 {len(project_urls)}개의 하위 프로젝트 링크를 발견했습니다!")

            # 2. 찾은 하위 링크들에 하나씩 들어가서 전체 화면을 캡처합니다. (최대 10개)
            for i, p_url in enumerate(project_urls[:10]):
                try:
                    print(f"[{i+1}/10] 상세 페이지 캡처 중: {p_url}")
                    detail_page = context.new_page()
                    detail_page.goto(p_url, wait_until="networkidle", timeout=60000)
                    time.sleep(3) # 화면 애니메이션이 끝날 때까지 대기
                    
                    # 페이지 제목 가져오기
                    title = detail_page.title().split('|')[0].split('-')[0].strip()
                    if not title: title = f"Project_{i}"
                    
                    # 썸네일용 이미지 하나 찾기
                    thumbnail = ""
                    imgs = detail_page.locator("img").element_handles()
                    for img in imgs:
                        src = img.get_attribute("src")
                        if src and "logo" not in src.lower() and "icon" not in src.lower():
                            thumbnail = urljoin(p_url, src)
                            break

                    # 파일 이름에 특수문자 없애기
                    clean_title = "".join([c for c in title if c.isalnum()]).rstrip()
                    file_name = f"screenshots/{site['name']}_{i}_{clean_title}.png"
                    
                    # 화면 전체 길게 캡처!
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
                    print(f"캡처 실패 ({p_url}): {e}")

        except Exception as e:
            print(f"사이트 접속 에러: {e}")

    browser.close()
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_projects, f, ensure_ascii=False, indent=4)
        
    print(f"\n최종 수집 완료! 총 {len(all_projects)}개의 프로젝트가 저장되었습니다.")

with sync_playwright() as playwright:
    run(playwright)
