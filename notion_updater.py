import json
import os
import requests
from datetime import datetime

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = "33cce71c8a0180bbb1caffa718dcc1ad"
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")

def get_existing_links():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    response = requests.post(url, headers=headers)
    if response.status_code != 200: return []
    return [page["properties"]["Link"]["url"] for page in response.json().get("results", []) if page["properties"]["Link"]["url"]]

def add_to_notion(item):
    image_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{item['screenshot_local']}"
    today = datetime.now().strftime("%Y-%m-%d")

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    data = {
        "parent": {"database_id": DATABASE_ID},
        "cover": {"type": "external", "external": {"url": item["thumbnail"]}},
        "properties": {
            "이름": {"title": [{"text": {"content": item["title"]}}]},
            "Agency": {"select": {"name": item["agency"]}},
            "Link": {"url": item["link"]},
            "제품군": {"select": {"name": item.get("product_type", "기타 산업")}},
            "디자인 종류": {"select": {"name": item.get("design_type", "분류 안됨")}},
            "구분": {"select": {"name": item.get("region", "해외")}},
            "등록일": {"date": {"start": today}}
        },
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "Full Project Capture"}}]}
            },
            {
                "object": "block",
                "type": "image",
                "image": {"type": "external", "external": {"url": image_url}}
            }
        ]
    }
    
    requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)

def main():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    existing_links = get_existing_links()
    
    for item in data:
        if item["link"] in existing_links:
            continue
        add_to_notion(item)
        print(f"새 프로젝트 추가 완료: {item['title']}")

if __name__ == "__main__":
    main()
