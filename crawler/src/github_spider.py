from __future__ import annotations

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_github_hot() -> list[dict]:
    print("Github spider running")

    url = "https://github.com/trending"
    result: list[dict] = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        repos = soup.select("article.Box-row")

        for repo in repos[:5]:
            title = repo.h2.text.strip().replace("\n", "").replace(" ", "")
            stars_node = repo.select_one("a.Link--muted")
            stars = stars_node.text.strip() if stars_node else "N/A"

            result.append({
                "platform": "github",
                "title": title,
                "hot_value": f"{stars} stars"
            })

    except Exception as e:
        print(f"Github spider failed: {e}")

    return result