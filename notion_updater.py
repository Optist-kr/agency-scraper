import json
import os
import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = "33cce71c8a0180bbb1caffa718dcc1ad"
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")

def add_to_notion(item):
    image_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{item['screenshot_local']}"

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
            # 💡 노션에 방금 만든 [제품군]과 [디자인 종류] 컬럼에 데이터를 넣습니다.
            "제품군": {"select": {"name": item.get("product_type", "기타")}},
            "디자인 종류": {"select": {"name": item.get("design_type", "분류 안됨")}}
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
    
    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
    if response.status_code != 200:
        print(f"노션 업로드 에러: {response.text}")

with open("data.json", "r", encoding="utf-8") as f:
    for item in json.load(f):
        add_to_notion(item)
