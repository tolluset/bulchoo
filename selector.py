from datetime import datetime
import dotenv
import os
import json
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from elasticsearch import Elasticsearch
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

dotenv.load_dotenv()

base_url = os.getenv("BASE_URL")
es_cert_fingerprint = os.getenv("ES_CERT_FINGERPRINT")
es_password = os.getenv("ES_PASSWORD")
slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
slack_channel = os.getenv("SLACK_CHANNEL")


llm = ChatOpenAI(model="gpt-4o").bind(response_format={"type": "json_object"})


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

es = Elasticsearch(
    "https://localhost:9200/",
    ssl_assert_fingerprint=es_cert_fingerprint,
    basic_auth=("elastic", es_password),
)

vs = ElasticsearchStore(
    index_name="blogs",
    embedding=embeddings,
    es_connection=es,
)


client = WebClient(token=slack_bot_token)


def main():
    user_input = "프론트엔드 개발자가 좋아할법한 블로그"
    now = datetime.now().strftime("%Y-%m-%d")

    results = vs.similarity_search(query=user_input, k=10, filters=[{"date": now}])

    res_text = ""
    for res in results:
        res_text += f"llm_summary: {res.page_content} \n metadata: {res.metadata} \n"

    recommend = llm.invoke(
        [
            (
                "system",
                f"Get 3 blogs from user input: {user_input}. Add llm_summary in data. You have to make output in pure JSON as {{'blogs': [...]}}. Don't translate or manipulate the origin source.",
            ),
            ("human", res_text),
        ],
    ).content
    print(f"🚀 : selector.py:57: recommend={recommend}")

    blogs = json.loads(str(recommend))["blogs"]

    for blog in blogs:
        meta = blog["metadata"]
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{meta['title']}* \n\n {blog['llm_summary']} \n\n *tags*: {', '.join(['#' + tag for tag in meta['tags']])} \n {meta['link']}",
                },
            }
        ]

        send_to_slack(blocks)


def send_to_slack(blocks):
    try:
        client.chat_postMessage(channel=slack_channel, blocks=blocks)
    except SlackApiError as e:
        assert e.response["error"]


if __name__ == "__main__":
    main()
