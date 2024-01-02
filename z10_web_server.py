from __future__ import unicode_literals

import configparser
import json
import os
import random
import re
import urllib.parse

from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from linebot.models import (
    BubbleContainer,
    FlexSendMessage,
    ImageCarouselColumn,
    ImageCarouselTemplate,
    ImageComponent,
    LocationMessage,
)

from z20_azure_sql import (
    FoodQueryBuild,
    RandomFood,
    StoreFoodNameQueryBuild,
    StoreInfoQueryBuild,
)
from z21_sql_query import SqlQuery
from z30_user_location import UserCoordinate
from z40_chatgpt import ChatGptCommitQuery, ChatGptQuery
from z50_upload_image_azure_blob import upload_image_to_azure_blob
from z60_ImagePredictor import ImagePredictor
from z70_googlemap import get_directions

# LINE 聊天機器人的token
app = Flask(__name__)
config = configparser.ConfigParser()
config.read("../LINEBOT_API_KEY/config.ini")
line_bot_api = LineBotApi(config.get("line-bot", "channel_access_token"))
handler = WebhookHandler(config.get("line-bot", "channel_secret"))

# 設定變數
user_choices = {}
user_id = "none"
store_choice_info = []
store_choice_map = []
store_choice_commit = []
store_choice_address = []
user_choices[user_id] = []
gpt_enabled = False
# linebot圖卡圖片
chinese_food_image_url = "https://i.imgur.com/oWx7pro.jpg"
japan_food_image_url = "https://i.imgur.com/sIFGvrV.jpg"
western_food_url = "https://i.imgur.com/xsjOjLF.jpeg"
what_food_url = "https://i.imgur.com/X0dzHbS.jpg"


# *********************************************************************************************************************************************************************
# *********************************************************************************************************************************************************************
# def
def generate_google_maps_link(address):
    # 將googlemap地址轉換為 URL 安全的格式
    encoded_address = urllib.parse.quote(address)

    # Google Maps 靜態地圖 API 的基本 URL
    base_url = "https://maps.googleapis.com/maps/api/staticmap"

    # 構建完整的 URL
    map_url = f"{base_url}?center={encoded_address}&size=400x400&markers=color:red%7Clabel:A%7C{encoded_address}"

    return map_url


def create_location_buttons_template():
    # 使用者位置
    # 無輸入變數
    buttons_template_feature = ButtonsTemplate(
        title="目前位置",
        text="選擇地點",
        actions=[
            MessageAction(label="不選擇位置", text="不選擇位置"),
            URIAction(label="位置", uri="https://line.me/R/nv/location/"),
        ],
    )
    template_message = TemplateSendMessage(
        alt_text="價格分析", template=buttons_template_feature
    )
    return template_message


def create_distance_buttons_template(text="請選擇距離"):
    # 使用者距離
    # 無輸入變數
    buttons_template = CarouselTemplate(
        columns=[
            CarouselColumn(
                thumbnail_image_url=what_food_url,
                title="餐廳距離",
                text=text,
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
    return template_message


def create_type_buttons_template():
    # 使用者type
    # 無輸入變數
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
                thumbnail_image_url=chinese_food_image_url,
                title="類別選擇",
                text="請選擇餐點類別",
                actions=[
                    MessageAction(label="異國料理", text="International"),
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
    template_message = TemplateSendMessage(alt_text="類型選擇", template=buttons_template)
    return template_message


def chatgpt_commit(user_input):
    # chatgpt整合評價
    # 輸入為user_input
    # 輸出為line格式,放至return --> line_bot_api.reply_message(event.reply_token, return)
    (
        restaurant_name,
        store_info,
        restaurant_address,
        food_name,
        pic_url,
        directions_url,
    ) = map(str.strip, user_input.split(","))

    store_query_dict = {"name": restaurant_name, "info": store_info}
    result_info = ""

    if store_info == "commit":
        # ----------------------------------------------------------
        # --向SQL要求google評價
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

        print(f"google評價字數為:{len(result_info)}")
        ask_msg = f"hi ai:店名:{restaurant_name},地址:{restaurant_address},餐點名稱:{food_name},店家評價:{result_info}"
        reply_msg = ChatGptCommitQuery(ask_msg)

        if "推薦度=" in reply_msg:
            intro, rating = reply_msg.split("推薦度=")
            # 去除 "★☆" 符號
            reply_msg = re.sub("[★☆]", "", intro)
        else:
            # 在沒有 "推薦度=" 的情況下再次執行 ChatGptCommitQuery
            reply_msg = ChatGptCommitQuery(ask_msg)
            # 可以再次檢查 "推薦度=" 是否存在，然後進行相應的處理
            if "推薦度=" in reply_msg:
                intro, rating = reply_msg.split("推薦度=")
                # 去除 "★☆" 符號
                reply_msg = re.sub("[★☆]", "", intro)
            else:
                # 在沒有 "推薦度=" 的情況下再次執行 ChatGptCommitQuery
                reply_msg = ChatGptCommitQuery(ask_msg)
                # 可以再次檢查 "推薦度=" 是否存在，然後進行相應的處理
                if "推薦度=" in reply_msg:
                    intro, rating = reply_msg.split("推薦度=")
                    # 去除 "★☆" 符號
                    reply_msg = re.sub("[★☆]", "", intro)

        contents = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": pic_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": restaurant_name,
                        "weight": "bold",
                        "size": "xl",
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "CHAT GPT推薦度",
                                "flex": 0,
                                "margin": "md",
                                "size": "sm",
                            },
                            {
                                "type": "text",
                                "size": "sm",
                                "color": "#FF8000",
                                "margin": "md",
                                "flex": 0,
                                "style": "normal",
                                "text": rating,
                            },
                        ],
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "餐點名稱：",
                                        "size": "sm",
                                        "color": "#000000",
                                        "weight": "bold",
                                        "flex": 0,
                                    },
                                    {
                                        "type": "text",
                                        "text": food_name,
                                        "flex": 0,
                                        "size": "sm",
                                        "color": "#000000",
                                        "weight": "bold",
                                    },
                                ],
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "店家評價：",
                                        "color": "#000000",
                                        "size": "sm",
                                        "flex": 1,
                                        "weight": "bold",
                                    }
                                ],
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "color": "#000000",
                                        "size": "sm",
                                        "wrap": True,
                                        "text": reply_msg,
                                    }
                                ],
                            },
                        ],
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "uri",
                            "uri": directions_url,
                            "label": "GOOGLE MAP",
                        },
                    }
                ],
                "flex": 0,
            },
            "styles": {"footer": {"separator": True, "separatorColor": "#000000"}},
        }
        template_message = FlexSendMessage(alt_text="chatgpt", contents=contents)
        # text_message = TextSendMessage(text=reply_msg)
        return template_message


def create_food_buttons_template(choice_buttons_text):
    # 餐點圖卡
    # 輸入查詢user選擇後的結果
    global store_choice_info
    global store_choice_commit
    global store_choice_address
    global store_choice_map
    template_columns = []
    store_choice_info = []
    store_choice_commit = []
    store_choice_address = []
    for sub_list in choice_buttons_text:
        restaurant_name = sub_list["restaurant_name"]
        food_name = sub_list["food_name"]
        food_price = sub_list["price"]
        restaurant_address = sub_list["address"]
        restaurant_distance = sub_list["distance"]
        pic_id = sub_list["pic_id"]
        pic_url = "https://linebotblob.blob.core.windows.net/food-image/" + pic_id
        google_coordinate = tuple(map(float, user_coordinate.split(",")))
        directions_url = get_directions(
            google_coordinate, f"{restaurant_name},{restaurant_address}"
        )
        store_choice_info.append(
            restaurant_name
            + ",commit,"
            + restaurant_address
            + ","
            + food_name
            + ","
            + pic_url
            + ","
            + directions_url
        )
        # 處理字數過多問題
        food_name = food_name[:20]
        restaurant_name = restaurant_name[:20]
        # 加入list
        store_choice_commit.append(restaurant_name + ",commit," + food_name)
        store_choice_address.append(restaurant_name + ",restaurant_address")

        # 處理字數過多問題
        if len(restaurant_address) > 20:
            desired_part = restaurant_address.split(", ")[-2:]
            restaurant_address = ", ".join(desired_part)
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
                    MessageAction(
                        label="看看店家評價(稍等10秒)",
                        text=f"{restaurant_name},commit,{food_name}",
                    ),
                    URIAction(label="GOOGLE MAP", uri=directions_url),
                    MessageAction(label="重新查詢", text="餐點查詢"),
                ],
            )
        )

    # 如果 template_columns 為空，加入 "無餐廳" 的 CarouselColumn
    if not template_columns:
        template_columns.append(
            CarouselColumn(
                title="無餐廳",
                text="無餐廳",
                actions=[MessageAction(label="重新查詢", text="餐點查詢")],
            )
        )

    buttons_template = CarouselTemplate(columns=template_columns)
    template_message = TemplateSendMessage(alt_text="餐廳選擇", template=buttons_template)
    return template_message


# *********************************************************************************************************************************************************************
# *********************************************************************************************************************************************************************
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


# @handler.add(MessageEvent, message=TextMessage)
@handler.add(MessageEvent)
def handle_message(event):
    # 設定全域變數
    global gpt_enabled
    global user_coordinate
    global template_message
    global store_choice_info
    global store_choice_commit
    global store_choice_map
    global store_choice_address
    global template_columns
    # 處理user的jason
    user_id = event.source.user_id
    event_type = event.message.type

    # 處理user選澤
    try:
        if not user_choices[user_id][0]:
            # user_choices[user_id][0] 是空列表的情況
            user_choices[user_id] = []
            user_choices[user_id].append("none")
        else:
            # user_choices[user_id][0] 不是空列表的情況
            print("")
    except:
        # 處理可能的 IndexError，即 user_id 或 0 可能不存在的情況
        user_choices[user_id] = []
        user_choices[user_id].append("none")
    # 處理user_input為文字、座標、圖片
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
    # *********************************************************************************************************************************************************************
    # *********************************************************************************************************************************************************************
    # -----------------------------------------------------------------------------------------------------------------------#
    # ---餐點查詢 mark:search-------------------------------------------------------------------------------------------------#
    # --位置------------------------------------------------------------------------------------------------------------------#
    if user_input == "餐點查詢":
        user_choices[user_id] = []  # 每次查詢時重置該使用者的選擇
        user_choices[user_id].append("search")
        # --位置template---------------------------------------------------------------------------------#
        template_message = create_location_buttons_template()
        line_bot_api.reply_message(event.reply_token, template_message)
        # --user input: 不選擇位置
        # --位置end---------------------------------------------------------------------------------------#
        # --距離distance------------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "search" and (
        user_input == "不選擇位置" or event_type == "location"
    ):
        if user_input == "不選擇位置":
            user_coordinate = UserCoordinate()

        # --距離distance template----------------------------------------------------------------------------------#
        template_message = create_distance_buttons_template()
        line_bot_api.reply_message(event.reply_token, template_message)
        # --user input: 500m 1000m 2000m
        # --距離distance end---------------------------------------------------------------------------------------#
        # --類別type------------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "search" and user_input in [
        "500m",
        "1000m",
        "2000m",
    ]:
        user_choices[user_id].append(user_input)
        # --類別type template----------------------------------------------------------------------------------#
        template_message = create_type_buttons_template()
        line_bot_api.reply_message(event.reply_token, template_message)
        # --user input: Brunch Desserts Drinks American International J&K TW Vegetarian none
        # --類別type end---------------------------------------------------------------------------------------#
        # -------------------------------------------------------------------------------------------------#
        # --價錢選擇----------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "search" and user_input in [
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
    elif user_choices[user_id][0] == "search" and user_input in [
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
            text="請選擇特色\n選完特色後將查詢餐點\n請稍待約10秒",
            actions=[
                MessageAction(label="服務", text="服務"),
                MessageAction(label="環境", text="環境"),
                MessageAction(label="美味", text="美味"),
            ],
        )
        template_message = TemplateSendMessage(
            alt_text="特色選擇", template=buttons_template_feature
        )

        line_bot_api.reply_message(event.reply_token, template_message)
    elif user_choices[user_id][0] == "search" and user_input in [
        "服務",
        "環境",
        "美味",
    ]:
        user_choices[user_id].append(user_input)

        # 在這裡處理使用者的選擇
        if len(user_choices[user_id]) == 5:
            distance = user_choices[user_id][1]
            type = user_choices[user_id][2]
            price = user_choices[user_id][3]
            sort = user_choices[user_id][4]
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
        # --食物圖卡*10 template-------------------------------------------------------------------------------------#
        template_message = create_food_buttons_template(choice_buttons_text)
        line_bot_api.reply_message(event.reply_token, template_message)
        # --食物圖卡 end---------------------------------------------------------------------------------------------#

        # --chatgpt評價整合------------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "search" and user_input in store_choice_commit:
        store_data = next(
            (
                data
                for data in store_choice_info
                if user_input.split(",")[0] and user_input.split(",")[2] in data
            ),
            None,
        )
        print(store_data)
        template_message = chatgpt_commit(store_data)
        line_bot_api.reply_message(event.reply_token, template_message)

    # ----googlemap-------------------------------------------------------------------------------------------------------
    # elif user_choices[user_id][0] == "search" and user_input in store_choice_map:
    #     restaurant_address = user_input
    #     google_coordinate = tuple(map(float, user_coordinate.split(",")))
    #     directions_url = get_directions(google_coordinate, restaurant_address)
    #     print(directions_url)
    #     buttons_template_feature = ButtonsTemplate(
    #         title="餐廳地址",
    #         text="地圖導航",
    #         actions=[
    #             URIAction(label="相機拍攝照片", uri=f"{directions_url}"),
    #         ],
    #     )
    #     template_message_feature = TemplateSendMessage(
    #         alt_text="map", template=buttons_template_feature
    #     )
    #     line_bot_api.reply_message(event.reply_token, template_message_feature)
    # ---餐點查詢-------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # -----------------------------------------------------------------------------------------------------------
    # ---價格預測 mark:analyze-------------------------------------------------------------------------------------------------
    elif user_input == "價格預測":
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
        template_message = TemplateSendMessage(
            alt_text="價格分析", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message)
    elif user_choices[user_id][0] == "analyze" and event_type == "image":
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
                MessageAction(label="再預測一次", text="價格預測"),
            ],
        )
        template_message = TemplateSendMessage(
            alt_text="CHAT", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message)
    elif user_choices[user_id][0] == "analyze" and user_input == "查詢類似餐點":
        # ---位置-----------------------------------------------------------------------------------------#
        template_message = create_location_buttons_template()
        line_bot_api.reply_message(event.reply_token, template_message)
        # --位置end------------------------------------------------------------------------------------------#
        # --距離------------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "analyze" and (
        user_input == "不選擇位置" or event_type == "location"
    ):
        if user_input == "不選擇位置":
            user_coordinate = UserCoordinate()

        # ---距離template-----------------------------------------------------------------------------------------#
        template_message = create_distance_buttons_template()
        line_bot_api.reply_message(event.reply_token, template_message)
        # ---距離end-----------------------------------------------------------------------------------------#
        # --類別type-------------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "analyze" and user_input in [
        "500m",
        "1000m",
        "2000m",
    ]:
        user_choices[user_id].append(user_input)

        # --類別type template----------------------------------------------------------------------------------#
        template_message = create_type_buttons_template()
        line_bot_api.reply_message(event.reply_token, template_message)
        # --user input: Brunch Desserts Drinks American International J&K TW Vegetarian none
        # --類別type end---------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "analyze" and user_input in [
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
            text="請選擇特色\n選完特色後將查詢餐點\n請稍待約10秒",
            actions=[
                MessageAction(label="服務", text="服務"),
                MessageAction(label="環境", text="環境"),
                MessageAction(label="美味", text="美味"),
            ],
        )
        template_message = TemplateSendMessage(
            alt_text="特色選擇", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message)
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
        # --食物圖卡*10 template-------------------------------------------------------------------------------------#
        template_message = create_food_buttons_template(choice_buttons_text)
        line_bot_api.reply_message(event.reply_token, template_message)
        # --食物圖卡 end---------------------------------------------------------------------------------------------#

        # --chatgpt------------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "analyze" and user_input in store_choice_commit:
        store_data = next(
            (
                data
                for data in store_choice_info
                if user_input.split(",")[0] and user_input.split(",")[2] in data
            ),
            None,
        )
        template_message = chatgpt_commit(store_data)
        line_bot_api.reply_message(event.reply_token, template_message)

        # ----------------------------------------------------------------------------------------------------#
    # ---價格分析end-------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # -----------------------------------------------------------------------------------------------------------
    # ---隨機餐點 mark:random-------------------------------------------------------------------------------------------------
    elif user_input == "隨機餐點":
        user_choices[user_id] = []
        user_choices[user_id].append("random")

        sql_query = RandomFood()
        print(sql_query)
        result = SqlQuery(sql_query)
        # 印出結果
        choice_buttons_text = []
        for row in result:
            food_name = row[0]
            price = row[1]
            address = row[2]
            pic_id = row[3]
            restaurant_name = row[4]
            restaurant_type = row[5]
            restaurant_sort = row[6]
            # 創建字典，將資訊加入其中
            item_dict = {
                "restaurant_name": restaurant_name,
                "food_name": food_name,
                "price": price,
                "address": address,
                "pic_id": pic_id,
                "type": restaurant_type,
                "sort": restaurant_sort,
            }
            choice_buttons_text.append(item_dict)
        print(choice_buttons_text)
        # --------------------------------------------------------------------------------------------#
        template_columns = []
        for sub_list in choice_buttons_text:
            restaurant_name = sub_list["restaurant_name"]
            food_name = sub_list["food_name"]
            price = sub_list["price"]
            restaurant_address = sub_list["address"]
            restaurant_type = sub_list["type"]
            restaurant_sort = sub_list["sort"]
            pic_id = sub_list["pic_id"]
            pic_url = "https://linebotblob.blob.core.windows.net/food-image/" + pic_id
            if price <= 50:
                food_price = "0~50"
            elif price <= 100:
                food_price = "50~100"
            elif price <= 150:
                food_price = "100~150"
            elif price <= 200:
                food_price = "150~200"
            elif price <= 300:
                food_price = "200~300"
            else:
                food_price = "300up"
            user_choices[user_id].append(food_price)
            user_choices[user_id].append(restaurant_type)
            user_choices[user_id].append(restaurant_sort)
            template_columns.append(
                CarouselColumn(
                    thumbnail_image_url=pic_url,
                    title=food_name[:20],
                    text=str(price)[:-2]
                    + "元"
                    + "\n"
                    + restaurant_name[:20]
                    + "\n"
                    + restaurant_address[:25],
                    actions=[
                        MessageAction(label="再隨機一次", text="隨機餐點"),
                        MessageAction(label="查看類似餐點", text="查看類似餐點"),
                    ],
                )
            )

        buttons_template = CarouselTemplate(columns=template_columns)
        print(buttons_template)
        template_message = TemplateSendMessage(
            alt_text="隨機餐點", template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)
    elif user_choices[user_id][0] == "random" and user_input == "查看類似餐點":
        # ---位置-----------------------------------------------------------------------------------------#
        template_message = create_location_buttons_template()
        line_bot_api.reply_message(event.reply_token, template_message)
        # --位置end------------------------------------------------------------------------------------------#
        # --距離------------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "random" and (
        user_input == "不選擇位置" or event_type == "location"
    ):
        if user_input == "不選擇位置":
            user_coordinate = UserCoordinate()

        # ---距離template-----------------------------------------------------------------------------------------#
        template_message = create_distance_buttons_template(
            text="請選擇距離\n選完距離後將查詢餐點\n請稍待約10秒"
        )
        line_bot_api.reply_message(event.reply_token, template_message)
        # ---距離end-----------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "random" and user_input in [
        "500m",
        "1000m",
        "2000m",
    ]:
        user_choices[user_id].append(user_input)

        # 在這裡處理使用者的選擇
        print(user_choices[user_id])
        if len(user_choices[user_id]) == 5:
            price = user_choices[user_id][1]
            type = user_choices[user_id][2]
            sort = user_choices[user_id][3]
            distance = user_choices[user_id][4]

            food_query_dict = {
                "type": type,
                "price": price,
                "sort": sort,
                "distance": distance,
                "user_coordinate": user_coordinate,
            }
            print(food_query_dict)
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
        # --食物圖卡*10 template-------------------------------------------------------------------------------------#
        template_message = create_food_buttons_template(choice_buttons_text)
        line_bot_api.reply_message(event.reply_token, template_message)
        # --食物圖卡 end---------------------------------------------------------------------------------------------#

        # --chatgpt------------------------------------------------------------------------------------------#
    elif user_choices[user_id][0] == "random" and user_input in store_choice_commit:
        store_data = next(
            (
                data
                for data in store_choice_info
                if user_input.split(",")[0] and user_input.split(",")[2] in data
            ),
            None,
        )
        template_message = chatgpt_commit(store_data)
        line_bot_api.reply_message(event.reply_token, template_message)

    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # ************************************************************************************************************************
    # -----------------------------------------------------------------------------------------------------------
    # ---CHATGPT-------------------------------------------------------------------------------------------------
    elif user_input == "呼叫GPT":
        buttons_template_feature = ButtonsTemplate(
            title="CHAT",
            text="GPT",
            actions=[
                MessageAction(label="(yes)", text="yes"),
                MessageAction(label="(yes)", text="yes"),
                MessageAction(label="(no)", text="no"),
            ],
        )
        template_message = TemplateSendMessage(
            alt_text="CHAT", template=buttons_template_feature
        )
        line_bot_api.reply_message(event.reply_token, template_message)
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
            template_message = TemplateSendMessage(
                alt_text="CHAT", template=buttons_template_feature
            )
            # -----------------------------------------------------------
            line_bot_api.reply_message(
                event.reply_token, [text_message, template_message]
            )
    # ---CHATGPT-------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(debug=True)
