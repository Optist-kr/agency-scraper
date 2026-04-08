import json
import time
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

SITES = [
    {"name": "Landor", "work_url": "https://landor.com/en/our-work/"},
    {"name": "Interbrand", "work_url": "https://www.interbrand.com/work/"}
]

# 💡 [새로운 기능] 페이지의 글자를 읽고 카테고리를 판단하는 함수
def categorize_project(title, text):
    content = (title + " " + text).lower()
    
    # 1. 제품군 판단 (영문 키워드 기반)
    product = "기타 산업"
    if any(w in content for w in ["auto", "car", "mobility", "vehicle", "hyundai", "kia", "bmw", "motor"]):
        product = "자동차/모빌리티"
    elif any(w in content for w in ["cosmetic", "beauty", "makeup", "skincare"]):
        product = "화장품/뷰티"
    elif any(w in content for w in ["food", "beverage", "snack", "drink", "coffee", "restaurant"]):
        product = "식음료(F&B)"
    elif any(w in content for w in ["kid", "child", "baby", "toy"]):
        product = "유아동/키즈"
    elif any(w in content for w in ["tech", "software", "app", "digital", "platform", "finance", "bank"]):
        product = "IT/금융"
    elif any(w in content for w in ["fashion", "clothing", "apparel", "wear"]):
        product = "패션/의류"

    # 2. 디자인 종류 판단
    design = "브랜드 경험/전략"
    if any(w in content for w in ["packaging", "package", "label"]):
        design = "패키지 디자인"
    elif any(w in content for w in ["logo", "identity", "bi", "ci", "typography"]):
        design = "로고/아이덴티티"
    elif any(w in content for w in ["editorial", "magazine", "book", "brochure", "print"]):
        design = "편집/인쇄"
    elif any(w in content for w in ["campaign", "promotion", "advertising", "commercial"]):
        design = "홍보/캠페인"
    elif any(w in content for w in ["ui", "ux", "website", "digital experience"]):
        design = "UI/UX 디자인"
        
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
            print(f"\n--- {site['name']} 수집 시작 ---")
            work_url = site['work_url']
            page.goto(work_url, wait_until="networkidle")
            time.sleep(5)
            
            # 무한 스크롤
            last_height = page.evaluate("document.body.scrollHeight")
            while True:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height: break
                last_height = new_height

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
            
            for i, p_url in enumerate(project_urls):
                try:
                    print(f"[{i+1}/{len(project_urls)}] 수집 중: {p_url}")
                    detail_page = context.new_page()
                    detail_page.goto(p_url, wait_until="networkidle", timeout=90000)
                    time.sleep(4)
                    
                    title = detail_page.title().split('|')[0].split('-')[0].strip() or f"Project_{i}"
                    
                    # 💡 [핵심] 페이지에 있는 텍스트를 읽어와서 카테고리 함수에 넘겨줍니다.
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
                        "product_type": product_type, # 분류된 제품군 저장
                        "design_type": design_type    # 분류된 디자인 종류 저장
                    })
                    detail_page.close()
                except Exception as e:
                    print(f"패스 ({p_url}): {e}")

        except Exception as e:
            print(f"접속 에러: {e}")

    browser.close()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_projects, f, ensure_ascii=False, indent=4)

with sync_playwright() as playwright:
    run(playwright)
