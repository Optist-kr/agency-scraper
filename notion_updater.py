import json
import os
import requests

# 환경 변수에서 노션 키와 DB ID를 가져옵니다
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_existing_links():
    """노션 DB에 이미 있는 포트폴리오 링크들을 가져와 중복을 방지합니다."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    
    if response.status_code != 200:
        print("노션 DB 조회 실패:", response.text)
        return []

    results = response.json().get("results", [])
    existing_links = []
    
    for page in results:
        props = page.get("properties", {})
        link_prop = props.get("Link", {}).get("url")
        if link_prop:
            existing_links.append(link_prop)
            
    return existing_links

def add_to_notion(item):
    """새 포트폴리오를 노션 페이지로 생성합니다."""
    url = "https://api.notion.com/v1/pages"
    
    # 노션 페이지 데이터 구조
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "이름": { # 노션의 기본 Title 속성 이름에 맞게 수정 (기본값: 이름)
                "title": [{"text": {"content": item["title"]}}]
            },
            "Agency": {
                "select": {"name": item["agency"]}
            },
            "Link": {
                "url": item["link"]
            }
        }
    }
    
    # 이미지가 있으면 노션 페이지의 '커버(Cover)' 이미지로 설정합니다.
    if item.get("image") and item["image"].startswith("http"):
        data["cover"] = {
            "type": "external",
            "external": {"url": item["image"]}
        }

    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(f"✅ 노션 추가 완료: {item['title']}")
    else:
        print(f"❌ 노션 추가 실패 ({item['title']}): {response.text}")

def main():
    if not NOTION_TOKEN or not DATABASE_ID:
        print("노션 환경 변수가 설정되지 않았습니다.")
        return

    # scraper.py가 생성한 data.json 읽기
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            scraped_data = json.load(f)
    except FileNotFoundError:
        print("data.json 파일이 없습니다. 스크래퍼가 먼저 실행되어야 합니다.")
        return

    existing_links = get_existing_links()
    new_items_count = 0

    for item in scraped_data:
        # 이미 노션에 있는 링크면 건너뜀
        if item["link"] in existing_links:
            continue
            
        add_to_notion(item)
        new_items_count += 1

    print(f"총 {new_items_count}개의 새로운 포트폴리오를 노션에 업데이트했습니다.")

if __name__ == "__main__":
    main()
