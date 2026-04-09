import json
import time
import os
import re
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

SITES = [
    {"name": "Landor", "url": "https://landor.com/", "region": "해외"},
    {"name": "Interbrand", "url": "https://www.interbrand.com/", "region": "해외"},
    {"name": "Collins", "url": "https://www.wearecollins.com/", "region": "해외"},
    {"name": "Order", "url": "https://order.design/", "region": "해외"},
    {"name": "Moving Brands", "url": "https://movingbrands.com/", "region": "해외"},
    {"name": "Porto Rocha", "url": "https://www.portorocha.com/", "region": "해외"},
    {"name": "Gretel", "url": "https://gretelny.com/", "region": "해외"},
    {"name": "Mother Design", "url": "https://www.motherdesign.com/", "region": "해외"},
    {"name": "Kurppa Hosk", "url": "https://www.kurppahosk.com/", "region": "해외"},
    {"name": "Wolff Olins", "url": "https://www.wolffolins.com/", "region": "해외"},
    {"name": "Pentagram", "url": "https://www.pentagram.com/", "region": "해외"},
    {"name": "Anagrama", "url": "https://www.anagrama.com/", "region": "해외"},
    
    {"name": "Studio fnt", "url": "https://studiofnt.com/", "region": "국내"},
    {"name": "Designfever", "url": "https://designfever.com/", "region": "국내"},
    {"name": "DFY", "url": "https://www.dfy.co.kr/", "region": "국내"},
    {"name": "VinylC", "url": "https://www.vinylc.com/", "region": "국내"},
    {"name": "Emotion", "url": "https://www.emotion.co.kr/", "region": "국내"},
    {"name": "SAM", "url": "https://samseoul.com/", "region": "국내"},
    {"name": "HNINE", "url": "https://www.hnine.com/", "region": "국내"},
    {"name": "Woot Creative", "url": "https://wootcreative.kr/", "region": "국내"},
    {"name": "B-Works", "url": "https://b-works.co.kr/", "region": "국내"},
    {"name": "Plus X", "url": "https://www.plus-ex.com/", "region": "국내"}
]

PORTFOLIO_KEYWORDS = ['work', 'works', 'project', 'projects', 'case', 'cases', 'portfolio', 'archive', 'our-work', 'selected']

IGNORE_KEYWORDS = [
    'about', 'contact', 'news', 'profile', 'career', 'team', 'service', 'privacy', 
    'studio', 'info', 'insight', 'people', 'culture', 'jobs', 'terms', 'policy', 
    'facebook', 'instagram', 'twitter', 'linkedin', 'journal', 'ideas', 'approach', 
    'store', 'clients', 'awards', 'expertise', 'capabilities', 'publications',
    'office', 'login', 'cart', 'search'
]

def categorize_project(title, text):
    content = (title + " " + text).lower()
    
    # 영단어는 독립된 단어일 때만 인식 (예: skincare에서 car 인식 방지)
    def match(words):
        for w in words:
            if re.match(r'^[a-z]+$', w):
                if re.search(r'\b' + w + r'\b', content): return True
            else:
                if w in content: return True
        return False

    product = "기타 산업"
    if match(["sport", "golf", "tennis", "athletic", "nike", "adidas", "스포츠", "골프", "운동", "피트니스", "아웃도어"]): product = "스포츠/레저"
    elif match(["auto", "car", "mobility", "vehicle", "motor", "자동차", "모빌리티", "차량"]): product = "자동차/모빌리티"
    elif match(["cosmetic", "beauty", "makeup", "skincare", "뷰티", "화장품", "스킨케어"]): product = "화장품/뷰티"
    elif match(["food", "beverage", "snack", "drink", "coffee", "restaurant", "식음료", "푸드", "카페", "베이커리", "f&b"]): product = "식음료(F&B)"
    elif match(["kid", "child", "baby", "toy", "키즈", "유아", "어린이", "장난감"]): product = "유아동/키즈"
    elif match(["tech", "software", "app", "digital", "platform", "it", "플랫폼", "소프트웨어"]): product = "IT/테크"
    elif match(["finance", "bank", "card", "pay", "금융", "은행", "카드", "결제", "핀테크"]): product = "금융/핀테크"
    elif match(["fashion", "clothing", "apparel", "wear", "패션", "의류", "브랜드", "잡화"]): product = "패션/의류"
    elif match(["health", "medical", "hospital", "bio", "pharma", "헬스케어", "의료", "병원", "제약", "바이오"]): product = "의료/헬스케어"
    elif match(["movie", "music", "game", "enter", "tv", "엔터테인먼트", "영화", "음악", "게임", "방송"]): product = "엔터/미디어"
    elif match(["edu", "school", "university", "academy", "교육", "학교", "대학", "학원"]): product = "교육/학습"
    elif match(["public", "gov", "city", "museum", "공공기관", "정부", "도시", "박물관", "미술관"]): product = "공공/문화"

    design = "브랜드 경험/전략"
    if match(["packaging", "package", "label", "패키지"]): design = "패키지 디자인"
    elif match(["ui", "ux", "website", "digital experience", "웹", "앱 디자인", "디지털"]): design = "UI/UX 디자인"
    elif match(["video", "motion", "film", "3d", "animation", "영상", "모션", "애니메이션", "필름"]): design = "영상/모션 그래픽"
    elif match(["space", "interior", "architecture", "exhibition", "공간", "인테리어", "건축", "전시"]): design = "공간/전시 디자인"
    elif match(["editorial", "magazine", "book", "brochure", "print", "편집", "인쇄", "매거진"]): design = "편집/인쇄물"
    elif match(["campaign", "promotion", "advertising", "commercial", "캠페인", "프로모션", "광고"]): design = "광고/캠페인"
    elif match(["logo", "identity", "bi", "ci", "typography", "아이덴티티", "로고", "타이포그래피"]): design = "로고/아이덴티티"
    
    return product, design

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    all_projects = []

    for site in SITES:
        try:
            print(f"\n--- {site['name']} ({site['region']}) 스마트 탐색 시작 ---")
            page.goto(site['url'], wait_until="networkidle", timeout=60000)
            time.sleep(3)

            work_link = None
            links = page.locator("a").element_handles()
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.inner_text().lower()
                    if href and any(kw in href.lower() or kw in text for kw in PORTFOLIO_KEYWORDS):
                        if urlparse(urljoin(site['url'], href)).netloc == urlparse(site['url']).netloc:
                            work_link = urljoin(site['url'], href)
                            break
                except: pass

            if work_link:
                print(f"포트폴리오 목록 페이지 진입: {work_link}")
                page.goto(work_link, wait_until="networkidle", timeout=60000)
            else:
                print("포트폴리오 메뉴를 찾지 못해 메인 페이지에서 탐색합니다.")
                work_link = site['url']

            time.sleep(4)
            
            for _ in range(6):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

            project_urls = set()
            for link in page.locator("a").element_handles():
                try:
                    href = link.get_attribute("href")
                    if not href: continue
                    full_url = urljoin(work_link, href).split('#')[0].split('?')[0]
                    
                    if urlparse(full_url).netloc != urlparse(site['url']).netloc: continue
                    if full_url.rstrip('/') == site['url'].rstrip('/') or full_url.rstrip('/') == work_link.rstrip('/'): continue
                    if any(ig in full_url.lower() for ig in IGNORE_KEYWORDS): continue
                    
                    if len(urlparse(full_url).path.strip('/')) > 0:
                        project_urls.add(full_url)
                except: pass

            project_urls = list(project_urls)
            print(f"세부 프로젝트 링크 {len(project_urls)}개 발견")

            for i, p_url in enumerate(project_urls[:30]):
                try:
                    print(f"[{i+1}/{min(len(project_urls), 30)}] 수집 중: {p_url}")
                    detail_page = context.new_page()
                    detail_page.goto(p_url, wait_until="networkidle", timeout=60000)
                    time.sleep(3)
                    
                    title = detail_page.title().split('|')[0].split('-')[0].strip() or f"Project_{i}"
                    page_text = detail_page.locator("body").inner_text()
                    product_type, design_type = categorize_project(title, page_text)
                    
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
                        "screenshot_local": file_name,
                        "product_type": product_type,
                        "design_type": design_type,
                        "region": site['region']
                    })
                    detail_page.close()
                except Exception as e:
                    print(f"패스 ({p_url}): {e}")

        except Exception as e:
            print(f"접속 에러: {e}")

    browser.close()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_projects, f, ensure_ascii=False, indent=4)
    print(f"\n수집 완료! 총 {len(all_projects)}개 항목 준비됨.")

with sync_playwright() as playwright:
    run(playwright)
