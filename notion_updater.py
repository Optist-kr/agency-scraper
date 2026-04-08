import json
import os
import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = "33cce71c8a0180bbb1caffa718dcc1ad" # 혜진 님의 진짜 ID
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")

def add_to_notion(item):
    # GitHub에 저장된 이미지를 외부에서 볼 수 있는 주소로 변환
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
            "Link": {"url": item["link"]}
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
                "image": {
                    "type": "external",
                    "external": {"url": image_url}
                }
            }
        ]
    }
    requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)

with open("data.json", "r", encoding="utf-8") as f:
    for item in json.load(f):
        add_to_notion(item)
