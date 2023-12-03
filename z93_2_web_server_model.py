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


chinese_food_image_url = "https://i.imgur.com/oWx7pro.jpg"
japan_food_image_url = "https://i.imgur.com/sIFGvrV.jpg"
western_food_url = "https://i.imgur.com/xsjOjLF.jpeg"
what_food_url = "https://i.imgur.com/X0dzHbS.jpg"

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


def create_image_carousel_template():
    # 創建 ImageCarouselTemplate
    image_carousel_template = ImageCarouselTemplate(
        columns=[
            ImageCarouselColumn(
                MessageAction(label="台式", text="TW"),
                MessageAction(label="日韓", text="J&K"),
                MessageAction(label="早午餐", text="Brunch"),
                MessageAction(label="美式、西式", text="American、International"),
            ),
            ImageCarouselColumn(
                MessageAction(label="點心", text="Desserts"),
                MessageAction(label="素食", text="Vegetarian"),
                MessageAction(label="飲料", text="Drinks"),
                MessageAction(label="不指定", text="None"),
            ),
        ]
    )

    # 創建 TemplateSendMessage
    template_message = TemplateSendMessage(
        alt_text="餐點選擇", template=image_carousel_template
    )

    return template_message


# ------------------------------------------------------------------------------------------------------------#
# --餐點選擇---------------------------------------------------------------------------------------------------#
def reset_user_choices(user_id):
    user_choices[user_id] = []


def create_category_template():
    return CarouselTemplate(
        columns=[
            CarouselColumn(
                thumbnail_image_url=what_food_url,
                title="餐點選擇",
                text="請選擇餐點類別",
                actions=[
                    MessageAction(label="台式", text="TW"),
                    MessageAction(label="日韓", text="J&K"),
                    MessageAction(label="美式、西式", text="American、International"),
                ],
            ),
            CarouselColumn(
                thumbnail_image_url=western_food_url,
                title="餐點選擇",
                text="請選擇餐點類別",
                actions=[
                    MessageAction(label="早午餐", text="Brunch"),
                    MessageAction(label="素食", text="Vegetarian"),
                    MessageAction(label="點心、飲料", text="Desserts、Drinks"),
                ],
            ),
            CarouselColumn(
                thumbnail_image_url=chinese_food_image_url,
                title="餐點選擇",
                text="請選擇餐點類別",
                actions=[
                    MessageAction(label="隨機100公尺內", text="random100m"),
                    MessageAction(label="隨機500公尺內", text="random500m"),
                    MessageAction(label="隨機1000公尺內", text="random1000m"),
                ],
            ),
        ]
    )


def handle_category_selection(event):
    user_id = event.source.user_id
    user_input = event.message.text

    reset_user_choices(user_id)

    if user_input == "餐點查詢":
        template_message = TemplateSendMessage(
            alt_text="餐點選擇", template=create_category_template()
        )
        line_bot_api.reply_message(event.reply_token, template_message)


def handle_user_input_selection(event, options, next_template, next_alt_text):
    user_id = event.source.user_id
    user_input = event.message.text

    if user_input in options:
        user_choices[user_id].append(user_input)

        template_message = TemplateSendMessage(
            alt_text=next_alt_text, template=next_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)


def handle_user_choices(event):
    user_id = event.source.user_id

    if len(user_choices[user_id]) == 3:
        category = user_choices[user_id][0]
        price = user_choices[user_id][1]
        feature = user_choices[user_id][2]

        # Add logic based on category, price, and feature
        # For example, respond with relevant meal information or execute a query

        user_coordinate = UserCoordinate()  # Assuming this function exists
        reply_message = f"您選擇了類別：{category}，價格：{price}，特色：{feature}，座標:{user_coordinate}。正在處理您的請求..."
    else:
        reply_message = "發生錯誤：無法識別的選擇序列。"

    reset_user_choices(user_id)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))


# --餐點選擇---------------------------------------------------------------------------------------------------#
# ------------------------------------------------------------------------------------------------------------#
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text

    if user_input == "餐點查詢":
        handle_category_selection(event)
    elif user_input in [
        "Brunch",
        "Desserts、Drinks",
        "American、International",
        "J&K",
        "TW",
        "Vegetarian",
        "random100m",
        "random500m",
        "random1000m",
    ]:
        handle_user_input_selection(
            event,
            ["100", "200", "None"],
            ButtonsTemplate(
                title="價格選擇",
                text="請選擇價格範圍",
                actions=[
                    MessageAction(label="100元", text="100"),
                    MessageAction(label="200元", text="200"),
                    MessageAction(label="不指定", text="None"),
                ],
            ),
            "價格選擇",
        )
    elif user_input in ["100", "200", "None"]:
        handle_user_input_selection(
            event,
            ["high_cp", "clean", "None"],
            ButtonsTemplate(
                title="特色選擇",
                text="請選擇特色",
                actions=[
                    MessageAction(label="CP高", text="high_cp"),
                    MessageAction(label="乾淨", text="clean"),
                    MessageAction(label="不選擇", text="None"),
                ],
            ),
            "特色選擇",
        )
    elif user_input in ["high_cp", "clean", "None"]:
        handle_user_choices(event)


if __name__ == "__main__":
    app.run(debug=True)
