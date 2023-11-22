from __future__ import unicode_literals

import configparser
import os
import random

from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

user_choices = {}
app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

# 接收 LINE 的資訊


@app.route("/food", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        print(body, signature)
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text

    if user_input == '餐點查詢':
        user_choices[user_id] = []  # 每次查詢時重置該使用者的選擇
        buttons_template = ButtonsTemplate(
            title='餐點選擇', text='請選擇餐點類別', actions=[
                MessageAction(label='中式', text='taiwanese'),
                MessageAction(label='日式', text='japanese'),
                MessageAction(label='不指定', text='None')
            ])
        template_message = TemplateSendMessage(
            alt_text='餐點選擇', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif user_input in ['taiwanese', 'japanese', 'None']:
        user_choices[user_id].append(user_input)
        buttons_template_price = ButtonsTemplate(
            title='價格選擇', text='請選擇價格範圍', actions=[
                MessageAction(label='100元', text='100'),
                MessageAction(label='200元', text='200'),
                MessageAction(label='不指定', text='None')
            ])
        template_message_price = TemplateSendMessage(
            alt_text='價格選擇', template=buttons_template_price)
        line_bot_api.reply_message(event.reply_token, template_message_price)
    elif user_input in ['100', '200', 'None']:
        user_choices[user_id].append(user_input)
        buttons_template_feature = ButtonsTemplate(
            title='特色選擇', text='請選擇特色', actions=[
                MessageAction(label='CP高', text='high_cp'),
                MessageAction(label='乾淨', text='clean'),
                MessageAction(label='不選擇', text='None')
            ])
        template_message_feature = TemplateSendMessage(
            alt_text='特色選擇', template=buttons_template_feature)
        line_bot_api.reply_message(event.reply_token, template_message_feature)
    elif user_input in ['high_cp', 'clean', 'None']:
        user_choices[user_id].append(user_input)

        # 在這裡處理使用者的選擇
        if len(user_choices[user_id]) == 3:
            category = user_choices[user_id][0]
            price = user_choices[user_id][1]
            feature = user_choices[user_id][2]
            # 在這裡添加基於 category、price 和 feature 的邏輯處理
            # 例如：回應相關的餐點資訊或執行查詢等操作

            reply_message = f"您選擇了類別：{category}，價格：{price}，特色：{feature}。正在處理您的請求..."
        else:
            reply_message = "發生錯誤：無法識別的選擇序列。"

        # 處理完畢後，清空使用者的選項
        user_choices[user_id] = []
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )


if __name__ == "__main__":
    app.run(debug=True)
