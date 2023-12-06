from __future__ import unicode_literals

import configparser
import json
import os
import random

from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from linebot.models import ImageCarouselColumn, ImageCarouselTemplate, LocationMessage

from z20_azure_sql import StoreInfoQueryBuild, StoreQueryBuild
from Z21_sql_query import SqlQuery
from z30_user_location import UserCoordinate
from z40_chatgpt import ChatGptQuery

chinese_food_image_url = "https://i.imgur.com/oWx7pro.jpg"
japan_food_image_url = "https://i.imgur.com/sIFGvrV.jpg"
western_food_url = "https://i.imgur.com/xsjOjLF.jpeg"
what_food_url = "https://i.imgur.com/X0dzHbS.jpg"
gpt_enabled = False

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


# @handler.add(MessageEvent, message=TextMessage)
@handler.add(MessageEvent)
def handle_message(event):
    global gpt_enabled
    global user_coordinate
    global template_message
    user_id = event.source.user_id
    event_type = event.message.type
    if event_type == "text":
        user_input = event.message.text
    elif event_type == "location":
        user_input = event.message.type
        user_latitude = event.message.latitude
        user_longitude = event.message.longitude
        user_address = event.message.address
        print(user_id, user_latitude, user_longitude, user_address)
        user_coordinate = f"{user_latitude},{user_longitude}"
    elif event_type == "image":
        user_input = event.message.id
    # -----------------------------------------------------------------------------------------------------------
    # ---餐點查詢-------------------------------------------------------------------------------------------------
    if user_input == "餐點查詢":
        user_choices[user_id] = []  # 每次查詢時重置該使用者的選擇
        # --------------------------------------------------------------------------------------------#
        buttons_template_feature = ButtonsTemplate(
            title="目前位置",
            text="選擇地點",
            actions=[
                MessageAction(label="不選擇位置", text="不選擇位置"),
                URIAction(label="位置", uri="https://line.me/R/nv/location/"),
            ],
        )
        template_message_feature = TemplateSendMessage(
            alt_text="價格分析", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message_feature)
        # --------------------------------------------------------------------------------------------#
    elif user_input == "不選擇位置" or event_type == "location":
        if user_input == "不選擇位置":
            user_coordinate = UserCoordinate()
        # --------------------------------------------------------------------------------------------#
        buttons_template = CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=what_food_url,
                    title="餐點選擇",
                    text="請選擇餐點類別",
                    actions=[
                        MessageAction(label="台式", text="'TW'"),
                        MessageAction(label="日韓", text="'J&K'"),
                        MessageAction(label="美式、西式", text="'American','International'"),
                    ],
                ),
                CarouselColumn(
                    thumbnail_image_url=western_food_url,
                    title="餐點選擇",
                    text="請選擇餐點類別",
                    actions=[
                        MessageAction(label="早午餐", text="'Brunch'"),
                        MessageAction(label="素食", text="'Vegetarian'"),
                        MessageAction(label="點心、飲料", text="'Desserts','Drinks'"),
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
        template_message = TemplateSendMessage(
            alt_text="餐點選擇", template=buttons_template
        )
        # --------------------------------------------------------------------------------------------#
        line_bot_api.reply_message(event.reply_token, template_message)
    elif user_input in [
        "'Brunch'",
        "'Desserts','Drinks'",
        "'American','International'",
        "'J&K'",
        "'TW'",
        "'Vegetarian'",
        "random100m",
        "random500m",
        "random1000m",
    ]:
        user_choices[user_id].append(user_input)
        buttons_template_price = ButtonsTemplate(
            title=user_input,
            text="請選擇價格範圍",
            actions=[
                MessageAction(label="100元", text="100"),
                MessageAction(label="200元", text="200"),
                MessageAction(label="不指定", text="pNone"),
            ],
        )
        template_message_price = TemplateSendMessage(
            alt_text="價格選擇", template=buttons_template_price
        )
        line_bot_api.reply_message(event.reply_token, template_message_price)
    elif user_input in ["100", "200", "pNone"]:
        user_choices[user_id].append(user_input)
        buttons_template_feature = ButtonsTemplate(
            title="特色選擇",
            text="請選擇特色",
            actions=[
                MessageAction(label="CP高", text="high_cp"),
                MessageAction(label="乾淨", text="clean"),
                MessageAction(label="不選擇", text="tNone"),
            ],
        )
        template_message_feature = TemplateSendMessage(
            alt_text="特色選擇", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message_feature)
    elif user_input in ["high_cp", "clean", "tNone"]:
        user_choices[user_id].append(user_input)

        # 在這裡處理使用者的選擇
        if len(user_choices[user_id]) == 3:
            type = user_choices[user_id][0]
            price = user_choices[user_id][1]
            feature = user_choices[user_id][2]
            # 在這裡添加基於 category、price 和 feature 的邏輯處理
            # 例如：回應相關的餐點資訊或執行查詢等操作

            reply_message = f"您選擇了類別：{type}，價格：{price}，特色：{feature}，座標:{user_coordinate}。正在處理您的請求..."
            # re_msg = f"您選擇了類別：{type}，價格：{price}，特色：{feature}，座標:{user_coordinate}。正在處理您的請求..."
            food_query_dict = {
                "type": type,
                "price": price,
                "feature": feature,
                "user_coordinate": user_coordinate,
            }
            sql_query = StoreQueryBuild(food_query_dict)
            print(sql_query)
            result = SqlQuery(sql_query)

            # 印出結果
            reply_arr = []
            choice_buttons_text = []
            for row in result:
                name_and_distance = row[0]
                distance = row[1]
                cleaned_name = name_and_distance.split("(")[0].strip()
                cleaned_distance = f"{int(distance)} 公尺"
                # 限制名稱長度為 20 個字元
                if len(cleaned_name) + len(cleaned_distance) > 20:
                    cleaned_name_max = 18 - len(cleaned_distance)  # len(,) =2
                    cleaned_name = cleaned_name[:cleaned_name_max]
                row = f"{cleaned_name}, {cleaned_distance}"
                choice_buttons_text.append(row)

                reply_arr.append(TextSendMessage(f"{row}"))

            reply_message = reply_arr
            print(choice_buttons_text)
        else:
            reply_message = "發生錯誤：無法識別的選擇序列。"

        actions = []
        reply_restaurant = []
        # --------------------------------------------------------------------------------------------#
        global store_choice_info

        template_columns = []
        store_choice_info = []
        for text in choice_buttons_text:
            restaurant_name = text.split(", ")[0]
            restaurant_distance = text.split(", ")[1]
            reply_restaurant.append(restaurant_name)
            store_choice_info.append(restaurant_name + ",food_name")
            store_choice_info.append(restaurant_name + ",commit")
            store_choice_info.append(restaurant_name + ",address")
            template_columns.append(
                CarouselColumn(
                    title=restaurant_name,
                    text=restaurant_distance,
                    actions=[
                        MessageAction(label="菜單", text=f"{restaurant_name},food_name"),
                        MessageAction(label="店家評論", text=f"{restaurant_name},commit"),
                        MessageAction(label="位置", text=f"{restaurant_name},address"),
                    ],
                )
            )
        print(store_choice_info)
        # 如果 choice_buttons_text 為空，加入 "無餐廳" 的 MessageAction
        if not template_columns:
            template_columns.append(
                CarouselColumn(
                    title="無餐廳",
                    text="無餐廳",
                    actions=[MessageAction(label="重新查詢", text="餐點查詢")],
                )
            )
        buttons_template = CarouselTemplate(columns=template_columns)
        template_message = TemplateSendMessage(
            alt_text="餐廳選擇", template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)
        # --------------------------------------------------------------------------------------------#
        # 處理完畢後，清空使用者的選項
    elif user_input in store_choice_info:
        restaurant_name = user_input.split(",")[0]
        store_info = user_input.split(",")[1]
        print(restaurant_name, store_info)
        store_query_dict = {"name": restaurant_name, "info": store_info}
        sql_query = StoreInfoQueryBuild(store_query_dict)
        print(sql_query)
        result = SqlQuery(sql_query)
        text_message = result
        print(result)
        line_bot_api.reply_message(event.reply_token, text_message)
        user_choices[user_id] = []
    # ---餐點查詢-------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # -----------------------------------------------------------------------------------------------------------
    # ---價格分析-------------------------------------------------------------------------------------------------
    elif user_input == "價格分析":
        buttons_template_feature = ButtonsTemplate(
            title="價格分析",
            text="上傳照片",
            actions=[
                URIAction(label="相機拍攝照片", uri="https://line.me/R/nv/camera/"),
                URIAction(label="選擇相簿照片", uri="https://line.me/R/nv/cameraRoll/single"),
            ],
        )
        template_message_feature = TemplateSendMessage(
            alt_text="價格分析", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message_feature)

    # ---價格分析-------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # -----------------------------------------------------------------------------------------------------------
    # ---CHATGPT-------------------------------------------------------------------------------------------------
    elif user_input == "呼叫GPT，我想花佑齊的錢":
        buttons_template_feature = ButtonsTemplate(
            title="CHAT",
            text="GPT",
            actions=[
                MessageAction(label="真的嗎(yes)", text="yes"),
                MessageAction(label="確定喔(yes)", text="yes"),
                MessageAction(label="一則0.01美(no)", text="no"),
            ],
        )
        template_message_feature = TemplateSendMessage(
            alt_text="CHAT", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message_feature)
    elif user_input in ["yes"]:
        reply_msg = "已開啟chatgpt"
        text_message = TextSendMessage(text=reply_msg)
        line_bot_api.reply_message(event.reply_token, text_message)
        gpt_enabled = True
    elif user_input == "closegpt":
        gpt_enabled = False
        reply_msg = "已關閉chatgpt"
        text_message = TextSendMessage(text=reply_msg)
        line_bot_api.reply_message(event.reply_token, text_message)
    elif user_input != None:
        if user_input is not None and gpt_enabled:
            print("已開啟chatgpt")
            ask_msg = "hi ai:" + user_input
            reply_msg = ChatGptQuery(ask_msg)
            text_message = TextSendMessage(text=reply_msg)
            # -----------------------------------------------------------
            buttons_template_feature = ButtonsTemplate(
                title="CHAT",
                text="GPT",
                actions=[
                    MessageAction(label="關閉chatgpt", text="closegpt"),
                ],
            )
            template_message_feature = TemplateSendMessage(
                alt_text="CHAT", template=buttons_template_feature
            )
            # -----------------------------------------------------------
            line_bot_api.reply_message(
                event.reply_token, [text_message, template_message_feature]
            )
    # ---CHATGPT-------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(debug=True)
