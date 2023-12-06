from __future__ import unicode_literals

import configparser
import os
import random

from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from linebot.models import ImageCarouselColumn, ImageCarouselTemplate

from z30_user_location import UserCoordinate
from z40_chatgpt import ChatGptCommitQuery

chinese_food_image_url = "https://i.imgur.com/oWx7pro.jpg"
japan_food_image_url = "https://i.imgur.com/sIFGvrV.jpg"
western_food_url = "https://i.imgur.com/xsjOjLF.jpeg"
what_food_url = "https://i.imgur.com/X0dzHbS.jpg"
global gpt_enabled

user_choices = {}
app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config.get("line-bot", "channel_access_token"))
handler = WebhookHandler(config.get("line-bot", "channel_secret"))

# 接收 LINE 的資訊


@app.route("/food", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        print(body, signature)
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text
    user_coordinate = UserCoordinate()
    print(user_coordinate)
    if user_input == "呼叫GPT，我想花佑齊的錢":
        buttons_template_feature = ButtonsTemplate(
            title="CHAT",
            text="GPT",
            actions=[
                MessageAction(label="真的嗎", text="yes"),
                MessageAction(label="確定喔", text="yes"),
                MessageAction(label="一則0.01美", text="no"),
            ],
        )
        template_message_feature = TemplateSendMessage(
            alt_text="CHAT", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message_feature)
    elif user_input in ["yes"]:
        # reply_msg = "在要問GPT的句子打上hi ai:"
        # text_message = TextSendMessage(text=reply_msg)
        reply_msg = "hi ai:請問python是甚麼"
        reply_msg = ChatGptCommitQuery(reply_msg)
        print(reply_msg)
        text_message = TextSendMessage(text=reply_msg)
        line_bot_api.reply_message(event.reply_token, text_message)

        # gpt_enabled = True
        # while gpt_enabled == True:
        #     buttons_template_feature = ButtonsTemplate(
        #         title="CHAT",
        #         text="GPT",
        #         actions=[
        #             MessageAction(label="結束GPT連線", text="gpt_enabled = false"),
        #         ],
        #     )
        #     template_message_feature = TemplateSendMessage(
        #         alt_text="CHAT", template=buttons_template_feature
        #     )
        #     line_bot_api.reply_message(event.reply_token, template_message_feature)
        #     if user_input == "gpt_enabled = false":
        #         gpt_enabled = False
        #     ChatGptQuery(user_input)


if __name__ == "__main__":
    app.run(debug=True)
