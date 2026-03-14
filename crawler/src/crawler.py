import json
from zhihu_spider import fetch_zhihu_hot
from github_spider import fetch_github_hot

print("crawler started")

def run():

    trends = []

    # 先抓知乎
    zhihu_data = fetch_zhihu_hot()

    if zhihu_data:
        trends += zhihu_data
    else:
        print("Zhihu failed, switching to Github")

        github_data = fetch_github_hot()
        trends += github_data

    with open("crawler/src/hot_trends.json", "w", encoding="utf-8") as f:
        json.dump(trends, f, ensure_ascii=False, indent=4)

    print("抓取完成!")
    print(trends)


if __name__ == "__main__":
    run()