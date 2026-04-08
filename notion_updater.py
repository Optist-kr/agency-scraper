import json
import os
import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
# GitHub 이미지 호스팅 주소 (자신의 계정명과 레포명으로 자동 설정)
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def add_to_notion(item):
    # 깃허브에 저장된 이미지의 절대 경로 (노션이 불러올 수 있는 URL)
    image_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{item['screenshot_local']}"

    data = {
        "parent": {"database_id": DATABASE_ID},
        "cover": {"type": "external", "external": {"url": item["thumbnail"]}},
        "properties": {
            "이름": {"title": [{"text": {"content": item["title"]}}]},
            "Agency": {"select": {"name": item["agency"]}},
            "Link": {"url": item["link"]}
        },
        "children": [ # 페이지 본문에 상세 캡처본 삽입
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
    requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=data)

def main():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for item in data:
        add_to_notion(item)
        print(f"노션 업데이트 완료: {item['title']}")

if __name__ == "__main__":
    main()
