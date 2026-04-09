import json
import time
import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

# 💡 메인 홈페이지 주소만 넣어둡니다.
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

# 💡 이 단어들이 메뉴에 있으면 클릭해서 포트폴리오 창으로 진입합니다.
PORTFOLIO_KEYWORDS = ['work', 'works', 'project', 'projects', 'case', 'cases', 'portfolio', 'archive', 'our-work', 'selected']

# 💡 하위 링크들 중 이 단어가 포함되어 있으면 세부 프로젝트가 아니므로 버립니다.
IGNORE_KEYWORDS = [
    'about', 'contact', 'news', 'profile', 'career', 'team', 'service', 'privacy', 
    'studio', 'info', 'insight', 'people', 'culture', 'jobs', 'terms', 'policy', 
    'facebook', 'instagram', 'twitter', 'linkedin', 'journal', 'ideas', 'approach', 
    'store', 'clients', 'awards', 'expertise', 'capabilities', 'publications',
    'office', 'login', 'cart', 'search'
]

def categorize_project(title, text):
    content = (title + " " + text).lower()
    product = "기타 산업"
    if any(w in content for w in ["sport", "golf", "tennis", "athletic", "nike", "adidas", "스포츠", "골프", "운동", "피트니스", "아웃도어"]): product = "스포츠/레저"
    elif any(w in content for w in ["auto", "car", "mobility", "vehicle", "motor", "자동차", "모빌리티", "차량"]): product = "자동차/모빌리티"
    elif any(w in content for w in ["cosmetic", "beauty", "makeup", "skincare", "뷰티", "화장품", "스킨케어"]): product = "화장품/뷰티"
    elif any(w in content for w in ["food", "beverage", "snack", "drink", "coffee", "restaurant", "식음료", "푸드", "카페", "베이커리", "f&b"]): product = "식음료(F&B)"
    elif any(w in content for w in ["kid", "child", "baby", "toy", "키즈", "유아", "어린이", "장난감"]): product = "유아동/키즈"
    elif any(w in content for w in ["tech", "software", "app", "digital", "platform", "it", "플랫폼", "소프트웨어"]): product = "IT/테크"
    elif any(w in content for w in ["finance", "bank", "card", "pay", "금융", "은행", "카드", "결제", "핀테크"]): product = "금융/핀테크"
    elif any(w in content for w in ["fashion", "clothing", "apparel", "wear", "패션", "의류", "브랜드", "잡화"]): product = "패션/의류"
    elif any(w in content for w in ["health", "medical", "hospital", "bio", "pharma", "헬스케어", "의료", "병원", "제약", "바이오"]): product = "의료/헬스케어"
    elif any(w in content for w in ["movie", "music", "game", "enter", "tv", "엔터테인먼트", "영화", "음악", "게임", "방송"]): product = "엔터/미디어"
    elif any(w in content for w in ["edu", "school", "university", "academy", "교육", "학교", "대학", "학원"]): product = "교육/학습"
    elif any(w in content for w in ["public", "gov", "city", "museum", "공공기관", "정부", "도시", "박물관", "미술관"]): product = "공공/문화"

    design = "브랜드 경험/전략"
    if any(w in content for w in ["packaging", "package", "label", "패키지"]): design = "패키지 디자인"
    elif any(w in content for w in ["ui", "ux", "website", "digital experience", "웹", "앱 디자인", "디지털"]): design = "UI/UX 디자인"
    elif any(w in content for w in ["video", "motion", "film", "3d", "animation", "영상", "모션", "애니메이션", "필름"]): design = "영상/모션 그래픽"
    elif any(w in content for w in ["space", "interior", "architecture", "exhibition", "공간", "인테리어", "건축", "전시"]): design = "공간/전시 디자인"
    elif any(w in content for w in ["editorial", "magazine", "book", "brochure", "print", "편집", "인쇄", "매거진"]): design = "편집/인쇄물"
    elif any(w in content for w in ["campaign", "promotion", "advertising", "commercial", "캠페인", "프로모션", "광고"]): design = "광고/캠페인"
    elif any(w in content for w in ["logo", "identity", "bi", "ci", "typography", "아이덴티티", "로고", "타이포그래피"]): design = "로고/아이덴티티"
    
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
            print(f"\n--- {site['name']} ({site['region']}) 탐색 시작 ---")
            page.goto(site['url'], wait_until="networkidle", timeout=60000)
            time.sleep(3)

            # 💡 [핵심 1] 홈페이지에서 '포트폴리오(Work, Cases 등)' 메뉴를 찾아 진입합니다.
            work_link = None
            links = page.locator("a").element_handles()
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.inner_text().lower()
                    if href and any(kw in href.lower() or kw in text for kw in PORTFOLIO_KEYWORDS):
                        # 자사 도메인 내의 링크인지 확인
                        if urlparse(urljoin(site['url'], href)).netloc == urlparse(site['url']).netloc:
                            work_link = urljoin(site['url'], href)
                            break
                except: pass

            if work_link:
                print(f"포트폴리오 목록 페이지 진입: {work_link}")
                page.goto(work_link, wait_until="networkidle", timeout=60000)
            else:
                print("포트폴리오 메뉴를 찾지 못해 현재(메인) 페이지를 기준으로 탐색합니다.")
                work_link = site['url']

            time.sleep(4)
            
            # 목록 페이지 스크롤하여 숨겨진 썸네일들 로딩
            for _ in range(6):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

            # 💡 [핵심 2] 현재 페이지에 있는 모든 링크를 수집한 뒤, 세부 프로젝트만 걸러냅니다.
            project_urls = set()
            for link in page.locator("a").element_handles():
                try:
                    href = link.get_attribute("href")
                    if not href: continue
                    full_url = urljoin(work_link, href).split('#')[0].split('?')[0]
                    
                    # 1. 외부 링크 제외
                    if urlparse(full_url).netloc != urlparse(site['url']).netloc: continue
                    # 2. 홈페이지 및 포트폴리오 목록 자체 페이지 제외 (단일 1개만 수집되는 문제 해결)
                    if full_url.rstrip('/') == site['url'].rstrip('/') or full_url.rstrip('/') == work_link.rstrip('/'): continue
                    # 3. 쓸데없는 메뉴(about 등) 제외
                    if any(ig in full_url.lower() for ig in IGNORE_KEYWORDS): continue
                    # 4. 최소한 경로(path)가 있는(깊이가 있는) 주소만 담기
                    if len(urlparse(full_url).path.strip('/')) > 0:
                        project_urls.add(full_url)
                except: pass

            project_urls = list(project_urls)
            print(f"최종 세부 프로젝트 링크 {len(project_urls)}개 발견")

            # 💡 각 사이트당 상위 30개씩 수집 (시간 단축 및 오류 방지)
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
    print(f"\n완료! 총 {len(all_projects)}개의 작업물이 저장되었습니다.")

with sync_playwright() as playwright:
    run(playwright)
