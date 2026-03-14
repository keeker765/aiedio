import requests
from bs4 import BeautifulSoup


def fetch_zhihu_hot():

    print("Zhihu spider running")

    url = "https://www.zhihu.com/hot"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.select(".HotItem")

    result = []

    for item in items[:5]:

        title = item.select_one(".HotItem-title")

        if title is None:
            continue

        hot = item.select_one(".HotItem-metrics")

        result.append({
            "platform": "zhihu",
            "title": title.text.strip(),
            "hot_value": hot.text.strip() if hot else ""
        })

    return result