import json
import time
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright

# [수정됨] 뒤에 /work 같은 상세 주소 없이 기본 홈페이지 주소만 적어주면 됩니다!
SITES = [
    {"name": "Landor", "url": "https://landor.com"},
    {"name": "Interbrand", "url": "https://www.interbrand.com"}
]

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    # PC 화면 사이즈로 설정해서 더 많은 이미지가 보이게 함
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()
    results = []

    for site in SITES:
        try:
            print(f"\n--- {site['name']} 사이트 탐색 시작 ---")
            page.goto(site['url'], wait_until="domcontentloaded")
            time.sleep(3)

            # 1. 사이트 안에서 '포트폴리오' 냄새가 나는 페이지 링크 모두 찾기
            print("포트폴리오 관련 페이지를 수색 중입니다...")
            target_urls = set([site['url']]) # 기본 홈페이지 포함
            
            keywords = ['work', 'portfolio', 'project', 'case']
            links = page.locator("a").element_handles()
            
            for link in links:
                href = link.get_attribute("href")
                if href:
                    full_url = urljoin(site['url'], href)
                    # 외부 사이트 링크는 빼고, 같은 도메인 안에서만 찾기
                    if urlparse(full_url).netloc == urlparse(site['url']).netloc:
                        if any(kw in full_url.lower() for kw in keywords):
                            target_urls.add(full_url)
            
            # 너무 오래 걸리지 않게, 포트폴리오 관련 페이지를 최대 4개까지만 방문
            target_urls = list(target_urls)[:4]
            print(f"방문할 상세 페이지들: {target_urls}")

            # 2. 찾아낸 페이지들을 돌아다니며 이미지 싹쓸이
            for target_url in target_urls:
                print(f"접속 중: {target_url}")
                try:
                    page.goto(target_url, wait_until="domcontentloaded")
                    time.sleep(3)
                    
                    # 화면을 끝까지 계속 내려서 숨겨진 이미지까지 로딩시킴
                    for i in range(5):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(2)
                        
                    # 페이지 내의 모든 이미지 태그 찾기
                    images = page.locator("img").element_handles()
                    
                    for img in images:
                        src = img.get_attribute("src")
                        if not src: continue
                        
                        src = urljoin(target_url, src)
                        alt = img.get_attribute("alt") or "포트폴리오 이미지"
                        
                        # [핵심] 쓸데없는 아이콘, 로고, 배지 이미지 걸러내기
                        src_lower = src.lower()
                        if "logo" in src_lower or "icon" in src_lower or "svg" in src_lower:
                            continue
                            
                        results.append({
                            "agency": site['name'],
                            "title": alt.strip()[:50], # 제목이 너무 길면 자르기
                            "image": src,
                            "link": target_url
                        })
                except Exception as e:
                    print(f"상세 페이지 에러 ({target_url}): {e}")

        except Exception as e:
            print(f"사이트 접속 에러 {site['name']}: {e}")

    browser.close()
    
    # 3. 똑같은 이미지를 두 번 가져오지 않도록 중복 제거
    unique_results = []
    seen_images = set()
    for r in results:
        if r['image'] not in seen_images:
            seen_images.add(r['image'])
            unique_results.append(r)
            
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(unique_results, f, ensure_ascii=False, indent=4)
        
    print(f"\n최종 수집 완료: 총 {len(unique_results)}개의 유효한 이미지를 수집했습니다.")

with sync_playwright() as playwright:
    run(playwright)
