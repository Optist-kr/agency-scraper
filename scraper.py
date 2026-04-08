import json
import time
import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

# 💡 [업그레이드] 이제 /work 같은 상세 주소 없이 '메인 홈페이지'만 넣어도 알아서 찾아냅니다!
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

# 💡 [핵심] 전 세계 에이전시들이 쓰는 포트폴리오 용어 사전
PORTFOLIO_KEYWORDS = ['work', 'works', 'project', 'projects', 'case', 'cases', 'portfolio', 'archive', 'story', 'stories', 'selected']

# 💡 [핵심] 절대 들어가면 안 되는 메뉴 용어 사전
IGNORE_KEYWORDS = ['about', 'contact', 'news', 'profile', 'career', 'team', 'service', 'privacy', 'studio', 'info', 'insight', 'people', 'culture', 'jobs']

def categorize_project(title, text):
    content = (title + " " + text).lower()
    
    # 1. 산업/제품군 (12개 카테고리로 세분화)
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

    # 2. 디자인 종류 (7개로 세분화)
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
            time.sleep(4)
            
            # 홈페이지 메인에서 링크 탐색
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

            links = page.locator("a").element_handles()
            project_urls = set()
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href: continue
                    
                    full_url = urljoin(site['url'], href)
                    
                    # 💡 스마트 필터링 1: 외부 사이트 링크 버리기
                    if urlparse(full_url).netloc != urlparse(site['url']).netloc: continue
                    
                    # 💡 스마트 필터링 2: 쓸데없는 메뉴(about 등) 버리기
                    if any(ig in full_url.lower() for ig in IGNORE_KEYWORDS): continue
                    
                    # 💡 스마트 필터링 3: URL을 단어 단위로 쪼개서 포트폴리오 키워드가 있는지 정확히 검사!
                    # (예: /our-work/apple -> ['our', 'work', 'apple'] 로 쪼갠 뒤 검사)
                    url_segments = full_url.lower().replace('-', ' ').replace('_', ' ').split('/')
                    
                    has_portfolio_keyword = False
                    for segment in url_segments:
                        words = segment.split()
                        if any(kw in words for kw in PORTFOLIO_KEYWORDS):
                            has_portfolio_keyword = True
                            break
                    
                    # 키워드가 포함되어 있고, 단순히 목록 페이지가 아니라 상세 페이지인 경우(URL 길이가 긴 경우)
                    if has_portfolio_keyword and len(url_segments) > 4:
                        if "#" not in full_url and "?" not in full_url:
                            project_urls.add(full_url)
                except: pass

            project_urls = list(project_urls)
            print(f"포트폴리오 관련 하위 링크 {len(project_urls)}개 발견 (최대 5개 수집)")

            for i, p_url in enumerate(project_urls[:5]):
                try:
                    print(f"[{i+1}/5] 수집 중: {p_url}")
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
