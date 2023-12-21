import configparser
import json
import os

import openai
import tiktoken
from flask import Flask, request

# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage  # 載入 TextSendMessage 模組
from openai import APIError, OpenAI
from transformers import AutoTokenizer

# model_name = "gpt-3.5-turbo-instruct"
model_name = "text-davinci-003"
max_tokens = 2500
encoding = tiktoken.encoding_for_model(model_name)


def ChatGptCommitQuery(msg):
    # 讀取API
    config = configparser.ConfigParser()
    config.read("../LINEBOT_API_KEY/openai_api.ini")
    key = config.get("openai", "key")
    try:
        # 取出文字的前五個字元，轉換成小寫
        # 將第六個字元之後的訊息發送給 OpenAI
        ai_msg = msg[:6].lower()
        reply_msg = ""
        # 取出文字的前五個字元是 hi ai:
        if ai_msg == "hi ai:":
            msg = msg[6:]
            print(f"減少token前={len(encoding.encode(msg))}")
            # 設定token上限
            if len(encoding.encode(msg)) > max_tokens:
                msg_token = encoding.encode(msg)[:max_tokens]
                print(f"減少token後={len(msg_token)}")
                msg = encoding.decode(msg_token)
                # msg = [encoding.decode_single_token_bytes(token) for token in msg_token]
            print(msg)
            # # 設定 OpenAI API 金鑰
            client = OpenAI(api_key=key)
            response = client.completions.create(
                # model="gpt-3.5-turbo-instruct",
                # model="text-davinci-003",
                model="gpt-3.5-turbo-instruct-0914",
                # 將第六個字元之後的訊息發送給 OpenAI
                # prompt=msg[6:],
                prompt=msg
                + "\n以上是店家的評價,請依餐點名稱來整合評價,並'使用約150字'客觀介紹店家。\n回覆的最後請加上 '推薦度='(用評論內容給1~5顆星,用★符號代表一顆星及☆符號代表無星)。",
                max_tokens=500,
                temperature=0.9,
                frequency_penalty=0.5,
                presence_penalty=0.5,
            )
            # 接收到回覆訊息後，移除換行符號
            msg = response.choices[0].text.replace("\n", "")
            print(msg)
            return msg
        else:
            msg = "失敗了"
        return msg
    except Exception as e:
        print(f"Error with vendor_id : {e}")
    return "OK"


def ChatGptQuery(msg):
    config = configparser.ConfigParser()
    config.read("../LINEBOT_API_KEY/openai_api.ini")
    key = config.get("openai", "key")
    try:
        # 取出文字的前五個字元，轉換成小寫
        # 將第六個字元之後的訊息發送給 OpenAI
        ai_msg = msg[:6].lower()
        reply_msg = ""
        # 取出文字的前五個字元是 hi ai:
        if ai_msg == "hi ai:":
            msg = msg[6:]
            print(len(encoding.encode(msg)))
            if len(encoding.encode(msg)) > max_tokens:
                msg_token = encoding.encode(msg)[:max_tokens]
                print(len(msg_token))
                msg = encoding.decode(msg_token)
                # msg = [encoding.decode_single_token_bytes(token) for token in msg_token]
            print(msg)
            # # 設定 OpenAI API 金鑰
            client = OpenAI(api_key=key)
            response = client.completions.create(
                # model="gpt-3.5-turbo-instruct",
                model="text-davinci-003",
                # 將第六個字元之後的訊息發送給 OpenAI
                # prompt=msg[6:],
                prompt=msg + "\n請使用繁體中文，不要超過150字說明。",
                max_tokens=500,
                temperature=0.8,
                frequency_penalty=0.5,
                presence_penalty=0.3,
            )
            # 接收到回覆訊息後，移除換行符號
            msg = response.choices[0].text.replace("\n", "")
            print(msg)
            return msg
        else:
            msg = "失敗了"
        return msg
    except Exception as e:
        print(f"Error with vendor_id : {e}")
    return "OK"


if __name__ == "__main__":
    result = ChatGptCommitQuery(
        "hi ai:'名:La 法包,地址:台北市大安區延吉街137巷25號1樓,餐點名稱:法式越南麵包含飲料banh mi+drink,店家評價:買了雞腿口味的麵包，麵包酥脆，可以切對半香料雞腿好吃😋份量中等，食慾比較好的中午可能要吃兩份比較飽 吃了脆皮燒肉口味+奶茶"
    )
