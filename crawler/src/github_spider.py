import requests
from bs4 import BeautifulSoup


def fetch_github_hot():

    print("Github spider running")

    url = "https://github.com/trending"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    repos = soup.select("article.Box-row")

    result = []

    for repo in repos[:5]:

        title = repo.h2.text.strip().replace("\n", "").replace(" ", "")

        stars = repo.select_one("a.Link--muted").text.strip()

        result.append({
            "platform": "github",
            "title": title,
            "hot_value": stars + " stars"
        })

    return result