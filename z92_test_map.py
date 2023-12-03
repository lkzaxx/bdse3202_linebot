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
from linebot import LineBotApi
from linebot.models import (
    TemplateSendMessage,
    ButtonsTemplate,
    PostbackAction,
    LocationMessage,
)

chinese_food_image_url = "https://i.imgur.com/oWx7pro.jpg"
japan_food_image_url = "https://i.imgur.com/sIFGvrV.jpg"
western_cuisine_url = "blob:https://imgur.com/c7989078-43e7-40cd-8969-d9e8640e56ee"
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


# ---------------------------------------------------------------------------------------
# 處理使用者點擊 Google 地圖按鈕觸發的 postback 事件
def handle_google_map_request(event):
    reply_message = TemplateSendMessage(
        alt_text="選擇位置",
        template=ButtonsTemplate(
            title="Google 地圖",
            text="點擊下方按鈕開啟 Google 地圖",
            actions=[
                PostbackAction(label="開啟 Google 地圖", data="action=open_google_map")
            ],
        ),
    )
    line_bot_api.reply_message(event.reply_token, reply_message)


# 處理使用者點擊 Google 地圖按鈕後觸發的 postback 事件
def handle_open_google_map(event):
    # 透過 LocationMessage 回傳使用者的座標
    location_message = LocationMessage(
        title="使用者位置", address="使用者所在地址", latitude=25.033, longitude=121.565
    )
    line_bot_api.reply_message(event.reply_token, location_message)


# ---------------------------------------------------------------------------------------


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text
    user_coordinate = UserCoordinate()
    print(user_coordinate)
    if user_input == "'googlemap":
        # 在這裡處理使用者的選擇
        # --------------------------------------------------------------------------------#

        handle_google_map_request(event)  # 使用者發送了開啟 Google 地圖的請求

        # 假設使用者點擊了按鈕觸發的事件
        user_postback_data = "action=open_google_map"

        # 簡單的處理邏輯
        if "action=open_google_map" in user_postback_data:
            handle_open_google_map(event)  # 使用者點擊了開啟 Google 地圖的按鈕
        # --------------------------------------------------------------------------------#
        if len(user_choices[user_id]) == 3:
            category = user_choices[user_id][0]
            price = user_choices[user_id][1]
            feature = user_choices[user_id][2]
            # 在這裡添加基於 category、price 和 feature 的邏輯處理
            # 例如：回應相關的餐點資訊或執行查詢等操作

            reply_message = f"您選擇了類別：{category}，價格：{price}，特色：{feature}，座標:{user_coordinate}。正在處理您的請求..."
        else:
            reply_message = "發生錯誤：無法識別的選擇序列。"

        # 處理完畢後，清空使用者的選項
        user_choices[user_id] = []
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=reply_message)
        )


if __name__ == "__main__":
    app.run(debug=True)
