from openai import OpenAI
import openai
from flask import Flask, request

# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage  # 載入 TextSendMessage 模組
import json
import configparser
import os


app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read("config.ini")
line_bot_api = LineBotApi(config.get("line-bot", "channel_access_token"))
handler = WebhookHandler(config.get("line-bot", "channel_secret"))


@app.route("/food", methods=["POST"])
def linebot():
    body = request.get_data(as_text=True)
    json_data = json.loads(body)
    print(json_data)
    try:
        signature = request.headers["X-Line-Signature"]
        handler.handle(body, signature)
        tk = json_data["events"][0]["replyToken"]
        msg = json_data["events"][0]["message"]["text"]
        # 取出文字的前五個字元，轉換成小寫
        ai_msg = msg[:6].lower()
        reply_msg = ""
        # 取出文字的前五個字元是 hi ai:
        if ai_msg == "hi ai:":
            # # 設定 OpenAI API 金鑰
            client = OpenAI(
                api_key="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"
            )
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                # 將第六個字元之後的訊息發送給 OpenAI
                prompt=msg[6:],
                max_tokens=256,
                temperature=0.5,
            )
            # 接收到回覆訊息後，移除換行符號
            reply_msg = response.choices[0].text.replace("\n", "")
        else:
            reply_msg = msg
        text_message = TextSendMessage(text=reply_msg)
        line_bot_api.reply_message(tk, text_message)
    except Exception as e:
        print(f"Error with vendor_id : {e}")
    return "OK"


if __name__ == "__main__":
    app.run(debug=True)
