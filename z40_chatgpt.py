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
                model="text-davinci-003",
                # 將第六個字元之後的訊息發送給 OpenAI
                # prompt=msg[6:],
                prompt=msg
                + "\n以上是店家的評價,請依餐點名稱來整合評價,並使用160字客觀介紹店家。\n回覆結尾加上 '推薦度='(用評論內容給1~5顆星,用★符號代表一顆星及☆符號代表無星)",
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
        "hi ai:'林家炸雞 CHICKEN LIN', '第一次吃到三角骨，帶點肉，啃起來很香酥，蠻驚艷的。雞屁股也很好吃，沒有油膩感，調味適中，不會太鹹。會想再回購的炸雞店。"
    )
