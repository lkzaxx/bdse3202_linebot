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
max_tokens = 3000
encoding = tiktoken.encoding_for_model(model_name)


def ChatGptCommitQuery(msg):
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
            client = OpenAI(
                api_key="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"
            )
            # client = OpenAI(
            #     api_key="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"
            # )
            response = client.completions.create(
                # model="gpt-3.5-turbo-instruct",
                model="text-davinci-003",
                # 將第六個字元之後的訊息發送給 OpenAI
                # prompt=msg[6:],
                prompt=msg
                + "\n以上是店家的評價,請整合評價,使用150字簡單介紹店家優點。\n並用評論內容給1~5顆星,用★符號代表一顆星及☆符號代表無星。",
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
            client = OpenAI(
                api_key="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"
            )
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
    ChatGptCommitQuery()
