from __future__ import unicode_literals

import configparser
import json
import os
import random
import urllib.parse

from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from linebot.models import ImageCarouselColumn, ImageCarouselTemplate, LocationMessage

from z20_azure_sql import FoodQueryBuild, StoreFoodNameQueryBuild, StoreInfoQueryBuild
from Z21_sql_query import SqlQuery
from z30_user_location import UserCoordinate
from z40_chatgpt import ChatGptCommitQuery, ChatGptQuery
from z50_upload_image_azure_blob import upload_image_to_azure_blob
from z60_ImagePredictor import ImagePredictor

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
global store_choice_info
store_choice_info = []
store_choice_commit = []
store_choice_address = []

# 接收 LINE 的資訊


def generate_google_maps_link(address):
    # 將地址轉換為 URL 安全的格式
    encoded_address = urllib.parse.quote(address)

    # Google Maps 靜態地圖 API 的基本 URL
    base_url = "https://maps.googleapis.com/maps/api/staticmap"

    # 構建完整的 URL
    map_url = f"{base_url}?center={encoded_address}&size=400x400&markers=color:red%7Clabel:A%7C{encoded_address}"

    return map_url


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

        # ---位置-----------------------------------------------------------------------------------------#
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
        # --位置end------------------------------------------------------------------------------------------#
        # --距離------------------------------------------------------------------------------------------#
    elif user_input == "不選擇位置" or event_type == "location":
        if user_input == "不選擇位置":
            user_coordinate = UserCoordinate()

        buttons_template = CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=what_food_url,
                    title="餐廳距離",
                    text="請選擇距離",
                    actions=[
                        MessageAction(label="500m", text="500m"),
                        MessageAction(label="1000m", text="1000m"),
                        MessageAction(label="2000m", text="2000m"),
                    ],
                ),
            ]
        )
        template_message = TemplateSendMessage(
            alt_text="location", template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)
        # ---距離end-----------------------------------------------------------------------------------------#
    elif user_input in [
        "500m",
        "1000m",
        "2000m",
    ]:
        user_choices[user_id].append(user_input)
        buttons_template = CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=what_food_url,
                    title="類別選擇",
                    text="請選擇類別",
                    actions=[
                        MessageAction(label="台式", text="TW"),
                        MessageAction(label="日韓", text="J&K"),
                        MessageAction(label="美式", text="American"),
                    ],
                ),
                CarouselColumn(
                    thumbnail_image_url=western_food_url,
                    title="類別選擇",
                    text="請選擇餐點類別",
                    actions=[
                        MessageAction(label="西式", text="International"),
                        MessageAction(label="早午餐", text="Brunch"),
                        MessageAction(label="素食", text="Vegetarian"),
                    ],
                ),
                CarouselColumn(
                    thumbnail_image_url=western_food_url,
                    title="類別選擇",
                    text="請選擇餐點類別",
                    actions=[
                        MessageAction(label="點心", text="Desserts"),
                        MessageAction(label="飲料", text="Drinks"),
                        MessageAction(label="不選擇", text="none"),
                    ],
                ),
            ]
        )
        template_message = TemplateSendMessage(
            alt_text="餐點選擇", template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)
        # --------------------------------------------------------------------------------------------#
        # --價錢選擇-----------------------------------------------------------------------------------#
    elif user_input in [
        "Brunch",
        "Desserts",
        "Drinks",
        "American",
        "International",
        "J&K",
        "TW",
        "Vegetarian",
        "none",
    ]:
        user_choices[user_id].append(user_input)
        # --------------------------------------------------------------------------------------------#
        buttons_template = CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=what_food_url,
                    title="價格選擇",
                    text="請選擇價格範圍",
                    actions=[
                        MessageAction(label="0~50元", text="0~50"),
                        MessageAction(label="50~100元", text="50~100"),
                        MessageAction(label="100~150元", text="100~150"),
                    ],
                ),
                CarouselColumn(
                    thumbnail_image_url=western_food_url,
                    title="價格選擇",
                    text="請選擇價格範圍",
                    actions=[
                        MessageAction(label="150~200元", text="150~200"),
                        MessageAction(label="200~300元", text="200~300"),
                        MessageAction(label="300元以上", text="300up"),
                    ],
                ),
            ]
        )
        template_message_price = TemplateSendMessage(
            alt_text="價格選擇", template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message_price)
        # --------------------------------------------------------------------------------------------#
    elif user_input in [
        "0~50",
        "50~100",
        "100~150",
        "150~200",
        "200~300",
        "300up",
    ]:
        user_choices[user_id].append(user_input)
        buttons_template_feature = ButtonsTemplate(
            title="特色選擇",
            text="請選擇特色",
            actions=[
                MessageAction(label="服務", text="服務"),
                MessageAction(label="環境", text="環境"),
                MessageAction(label="美味", text="美味"),
            ],
        )
        template_message_feature = TemplateSendMessage(
            alt_text="特色選擇", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message_feature)
    elif user_input in [
        "服務",
        "環境",
        "美味",
    ]:
        user_choices[user_id].append(user_input)

        # 在這裡處理使用者的選擇
        if len(user_choices[user_id]) == 4:
            distance = user_choices[user_id][0]
            type = user_choices[user_id][1]
            price = user_choices[user_id][2]
            sort = user_choices[user_id][3]
            # 在這裡添加基於 category、price 和 feature 的邏輯處理
            # 例如：回應相關的餐點資訊或執行查詢等操作

            reply_message = (
                f"您選擇了類別：{type}，價格：{price}，特色：{sort}，座標:{user_coordinate}。正在處理您的請求..."
            )
            # re_msg = f"您選擇了類別：{type}，價格：{price}，特色：{feature}，座標:{user_coordinate}。正在處理您的請求..."
            food_query_dict = {
                "type": type,
                "price": price,
                "sort": sort,
                "distance": distance,
                "user_coordinate": user_coordinate,
            }
            sql_query = FoodQueryBuild(food_query_dict)
            print(sql_query)
            result = SqlQuery(sql_query)
            # result = food_name,price,address,distance
            # 印出結果
            reply_arr = []
            choice_buttons_text = []
            for row in result:
                food_name = row[0]
                price = row[1]
                address = row[2]
                pic_id = row[3]
                restaurant_name = row[4]
                distance = row[5]
                cleaned_distance = f"{int(distance)} 公尺"
                # 創建字典，將資訊加入其中
                item_dict = {
                    "restaurant_name": restaurant_name,
                    "food_name": food_name,
                    "price": price,
                    "address": address,
                    "distance": cleaned_distance,
                    "pic_id": pic_id,
                }
                choice_buttons_text.append(item_dict)
        else:
            reply_message = "發生錯誤：無法識別的選擇序列。"
        print(choice_buttons_text)
        # --------------------------------------------------------------------------------------------#
        reply_restaurant = []
        template_columns = []
        for sub_list in choice_buttons_text:
            restaurant_name = sub_list["restaurant_name"]
            food_name = sub_list["food_name"]
            food_price = sub_list["price"]
            restaurant_address = sub_list["address"]
            restaurant_distance = sub_list["distance"]
            pic_id = sub_list["pic_id"]
            pic_url = f"https://linebotblob.blob.core.windows.net/food-image/{pic_id}"
            print(pic_url)
            reply_restaurant.append(restaurant_name)
            store_choice_commit.append(restaurant_name + ",commit")
            store_choice_address.append(restaurant_name + ",restaurant_address")
            store_choice_info.append(restaurant_name + ",commit")
            # google_maps_link = generate_google_maps_link(restaurant_address)
            # print(google_maps_link)
            template_columns.append(
                CarouselColumn(
                    thumbnail_image_url=pic_url,
                    title=food_name,
                    text=str(food_price)[:-2]
                    + "元"
                    + "\n"
                    + restaurant_name
                    + "\n"
                    + restaurant_address
                    + "\n"
                    + restaurant_distance,
                    actions=[
                        MessageAction(label="看看店家評價", text=f"{restaurant_name},commit"),
                        MessageAction(
                            label="GOOGLE MAP",
                            text=restaurant_name + "," + restaurant_address,
                        ),
                        MessageAction(label="重新查詢", text="餐點查詢"),
                    ],
                )
            )
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

        # --------------------------------------------------------------------------------------------#
    elif user_input in store_choice_info:
        restaurant_name = user_input.split(",")[0]
        store_info = user_input.split(",")[1]
        store_query_dict = {"name": restaurant_name, "info": store_info}
        result_info = []
        if store_info == "commit":
            # ----------------------------------------------------------
            sql_query = StoreInfoQueryBuild(store_query_dict)
            print(sql_query)
            result = SqlQuery(sql_query)
            for row in result:
                result_info = row[0]
            # ----------------------------------------------------------
            # 移除換行符號
            result_info = result_info.replace("\n", "")
            # 移除空白
            result_info = " ".join(result_info.split())
            print(len(result_info))
            # ask_msg = f"hi ai:以下是{restaurant_name}店家評價，請整合評價內容來簡單介紹店家，請使用150個字內的中文，評價={result_info }"
            ask_msg = f"hi ai:店名:{restaurant_name},店家評價:{result_info}"
            reply_msg = ChatGptCommitQuery(ask_msg)
            text_message = TextSendMessage(text=reply_msg)

        line_bot_api.reply_message(event.reply_token, text_message)
        # 處理完畢後，清空使用者的選項
        user_choices[user_id] = []
    # ---餐點查詢-------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # -----------------------------------------------------------------------------------------------------------
    # ---價格分析-------------------------------------------------------------------------------------------------
    elif user_input == "價格分析":
        user_choices[user_id] = []
        user_choices[user_id].append("analyze")

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
    elif event_type == "image":
        message_id = event.message.id
        message_content = line_bot_api.get_message_content(message_id)

        upload_image_to_azure_blob(message_id + ".jpg", message_content.content)
        # ImagePredictor(模型位置, 圖片網址)
        predictor = ImagePredictor(
            r"./CNN-ResNet-DenseNet-01_best_model.h5",
            r"https://linebotblob.blob.core.windows.net/upload-image",
        )

        pic_url = (
            f"https://linebotblob.blob.core.windows.net/upload-image/{message_id}.jpg"
        )
        # 圖片預測
        # predictor.predict_image('圖片名稱')
        result = predictor.predict_image(f"{message_id}.jpg")
        user_choices[user_id].append(result)
        buttons_template_feature = ButtonsTemplate(
            thumbnail_image_url=pic_url,
            title="預測結果",
            text=result + "元",
            actions=[
                MessageAction(label="查詢類似餐點", text="查詢類似餐點"),
                MessageAction(label="再分析一次", text="價格分析"),
            ],
        )
        template_message_feature = TemplateSendMessage(
            alt_text="CHAT", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message_feature)
    elif user_input == "查詢類似餐點":
        # ---位置-----------------------------------------------------------------------------------------#
        buttons_template_feature = ButtonsTemplate(
            title="目前位置",
            text="選擇地點",
            actions=[
                MessageAction(label="不選擇位置m", text="不選擇位置m"),
                URIAction(label="位置", uri="https://line.me/R/nv/location/"),
            ],
        )
        template_message_feature = TemplateSendMessage(
            alt_text="價格分析", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message_feature)
        # --位置end------------------------------------------------------------------------------------------#
        # --距離------------------------------------------------------------------------------------------#
    elif user_input == "不選擇位置m" or event_type == "location":
        if user_input == "不選擇位置m":
            user_coordinate = UserCoordinate()

        buttons_template = CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=what_food_url,
                    title="餐廳距離",
                    text="請選擇距離",
                    actions=[
                        MessageAction(label="500m", text="500m"),
                        MessageAction(label="1000m", text="1000m"),
                        MessageAction(label="2000m", text="2000m"),
                    ],
                ),
            ]
        )
        template_message = TemplateSendMessage(
            alt_text="location", template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)
        # ---距離end-----------------------------------------------------------------------------------------#
    elif user_input in [
        "500m",
        "1000m",
        "2000m",
    ]:
        user_choices[user_id].append(user_input)

        buttons_template = CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=what_food_url,
                    title="類別選擇",
                    text="請選擇類別",
                    actions=[
                        MessageAction(label="台式", text="TW"),
                        MessageAction(label="日韓", text="J&K"),
                        MessageAction(label="美式", text="American"),
                    ],
                ),
                CarouselColumn(
                    thumbnail_image_url=western_food_url,
                    title="類別選擇",
                    text="請選擇餐點類別",
                    actions=[
                        MessageAction(label="西式", text="International"),
                        MessageAction(label="早午餐", text="Brunch"),
                        MessageAction(label="素食", text="Vegetarian"),
                    ],
                ),
                CarouselColumn(
                    thumbnail_image_url=western_food_url,
                    title="類別選擇",
                    text="請選擇餐點類別",
                    actions=[
                        MessageAction(label="點心", text="Desserts"),
                        MessageAction(label="飲料", text="Drinks"),
                        MessageAction(label="不選擇", text="none"),
                    ],
                ),
            ]
        )
        template_message = TemplateSendMessage(
            alt_text="餐點選擇", template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)
    elif user_input in [
        "Brunch",
        "Desserts",
        "Drinks",
        "American",
        "International",
        "J&K",
        "TW",
        "Vegetarian",
        "none",
    ]:
        user_choices[user_id].append(user_input)

        buttons_template_feature = ButtonsTemplate(
            title="特色選擇",
            text="請選擇特色",
            actions=[
                MessageAction(label="服務", text="服務"),
                MessageAction(label="環境", text="環境"),
                MessageAction(label="美味", text="美味"),
            ],
        )
        template_message_feature = TemplateSendMessage(
            alt_text="特色選擇", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message_feature)
    elif user_input in ["服務", "環境", "美味"]:
        user_choices[user_id].append(user_input)

        # 在這裡處理使用者的選擇
        print(user_choices[user_id])
        if len(user_choices[user_id]) == 5:
            price = user_choices[user_id][1]
            distance = user_choices[user_id][2]
            type = user_choices[user_id][3]
            sort = user_choices[user_id][4]

            food_query_dict = {
                "type": type,
                "price": price,
                "sort": sort,
                "distance": distance,
                "user_coordinate": user_coordinate,
            }
            sql_query = FoodQueryBuild(food_query_dict)
            print(sql_query)
            result = SqlQuery(sql_query)
            # result = food_name,price,address,distance
            # 印出結果
            reply_arr = []
            choice_buttons_text = []
            for row in result:
                food_name = row[0]
                price = row[1]
                address = row[2]
                pic_id = row[3]
                restaurant_name = row[4]
                distance = row[5]
                cleaned_distance = f"{int(distance)} 公尺"
                # 創建字典，將資訊加入其中
                item_dict = {
                    "restaurant_name": restaurant_name,
                    "food_name": food_name,
                    "price": price,
                    "address": address,
                    "distance": cleaned_distance,
                    "pic_id": pic_id,
                }
                choice_buttons_text.append(item_dict)
        else:
            reply_message = "發生錯誤：無法識別的選擇序列。"
        print(choice_buttons_text)
        # --------------------------------------------------------------------------------------------#
        reply_restaurant = []
        template_columns = []
        for sub_list in choice_buttons_text:
            restaurant_name = sub_list["restaurant_name"]
            food_name = sub_list["food_name"]
            food_price = sub_list["price"]
            restaurant_address = sub_list["address"]
            restaurant_distance = sub_list["distance"]
            pic_id = sub_list["pic_id"]
            pic_url = "https://linebotblob.blob.core.windows.net/food-image/" + pic_id
            reply_restaurant.append(restaurant_name)
            store_choice_commit.append(restaurant_name + ",commit")
            store_choice_address.append(restaurant_name + ",restaurant_address")
            store_choice_info.append(restaurant_name + ",commit")

            # google_maps_link = generate_google_maps_link(restaurant_address)
            # print(google_maps_link)
            template_columns.append(
                CarouselColumn(
                    thumbnail_image_url=pic_url,
                    title=food_name,
                    text=str(food_price)[:-2]
                    + "元"
                    + "\n"
                    + restaurant_name
                    + "\n"
                    + restaurant_address
                    + "\n"
                    + restaurant_distance,
                    actions=[
                        MessageAction(label="看看店家評價", text=f"{restaurant_name},commit"),
                        MessageAction(
                            label="GOOGLE MAP",
                            text=restaurant_name + "," + restaurant_address,
                        ),
                        MessageAction(label="重新查詢", text="餐點查詢"),
                    ],
                )
            )
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

        # --------------------------------------------------------------------------------------------#
    elif user_input in store_choice_info:
        restaurant_name = user_input.split(",")[0]
        store_info = user_input.split(",")[1]
        store_query_dict = {"name": restaurant_name, "info": store_info}
        result_info = []
        if store_info == "commit":
            # ----------------------------------------------------------
            sql_query = StoreInfoQueryBuild(store_query_dict)
            print(sql_query)
            result = SqlQuery(sql_query)
            for row in result:
                result_info = row[0]
            # ----------------------------------------------------------
            # 移除換行符號
            result_info = result_info.replace("\n", "")
            # 移除空白
            result_info = " ".join(result_info.split())
            print(len(result_info))
            # ask_msg = f"hi ai:以下是{restaurant_name}店家評價，請整合評價內容來簡單介紹店家，請使用150個字內的中文，評價={result_info }"
            ask_msg = f"hi ai:店名:{restaurant_name},店家評價:{result_info}"
            reply_msg = ChatGptCommitQuery(ask_msg)
            text_message = TextSendMessage(text=reply_msg)

        line_bot_api.reply_message(event.reply_token, text_message)
        # 處理完畢後，清空使用者的選項
        user_choices[user_id] = []
        # --------------------------------------------------------------------------------------------#
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
