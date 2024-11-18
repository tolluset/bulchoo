from typing import List
from dataclasses import dataclass
import feedparser
from bs4 import BeautifulSoup
import html2text
import requests
import dotenv
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from elasticsearch import Elasticsearch
from langchain_core.documents import Document


dotenv.load_dotenv()

base_url = os.getenv("BASE_URL")
es_host = os.getenv("ELASTIC_HOST")
es_cert_fingerprint = os.getenv("ELASTIC_CERT_FINGERPRINT")
es_password = os.getenv("ELASTIC_PASSWORD")

llm = ChatOpenAI(model="gpt-4o")


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


es = Elasticsearch(
    es_host,
    ssl_assert_fingerprint=es_cert_fingerprint,
    basic_auth=("elastic", es_password),
)


vs = ElasticsearchStore(
    index_name="blogs",
    embedding=embeddings,
    es_connection=es,
)


@dataclass
class Blog:
    id: str
    title: str
    link: str
    summary: str
    date: str
    tags: List[str]


def main():
    existing_ids = get_existing_ids()
    print(f"🚀 : collector.py:54: existing_ids={existing_ids}")

    feeds = get_feeds()

    feeds_contents = []
    new_blogs = 0
    for feed in feeds:
        blog = build_blog(feed)
        print(f"🚀 : parser.py:41: blog={blog}")

        if blog.id in existing_ids:
            print(f"🚀 : parser.py:45: blog.id={blog.id} is already existed.")
            continue

        new_blogs += 1

        markdown_content = get_markdown_content(blog.link)

        gpt_summary = get_gpt_summary(markdown_content)

        doc = Document(page_content=gpt_summary, metadata={**vars(blog)})
        print(f"🚀 : parser.py:79: doc={doc}")

        feeds_contents.append(doc)

        ids = [item.metadata["id"] for item in feeds_contents]
        vs.add_documents(feeds_contents, ids=ids)

    print(f"🚀 : parser.py:85: new_blogs={new_blogs}")
    return


def get_existing_ids():
    query = {
        "size": 100,
        "sort": [{"metadata.date": {"order": "desc"}}],
        "_source": ["_id"],
    }
    try:
        res = es.search(index="blogs", body=query)
    except Exception as e:
        print(f"🚀 : parser.py:65: e={e}")
        return []

    hits = res["hits"]["hits"]
    ids = [hit["_id"] for hit in hits]

    return ids


def get_feeds():
    feed = feedparser.parse(base_url)
    entries = feed["entries"]
    return entries


def build_blog(feed):
    id = feed["id"]
    title = feed["title"]
    link = feed["link"]
    summary = feed["summary"]
    time = feed["published_parsed"]
    date = f"{time.tm_year}-{time.tm_mon}-{time.tm_mday}"
    tags = [tag["term"] for tag in feed.get("tags", [])]

    return Blog(id, title, link, summary, date, tags)


def get_markdown_content(link):
    response = requests.get(link)

    soup = BeautifulSoup(response.content, "html.parser")

    znc_elements = soup.find(class_="znc")
    assert znc_elements is not None

    markdown_content = html2text.html2text(str(znc_elements))
    return markdown_content


def get_gpt_summary(markdown_content) -> str:
    summary = llm.invoke(
        [
            (
                "system",
                "Make short summary of the blog post as three lines. TRANSLATE TO KOREAN FOR MAKE OUTPUT SUMMARY.",
            ),
            ("human", markdown_content),
        ]
    ).content

    return str(summary)


if __name__ == "__main__":
    main()
