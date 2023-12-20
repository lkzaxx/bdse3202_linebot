from io import BytesIO

import requests
from azure.storage.blob import BlobServiceClient, ContentSettings
from linebot import LineBotApi
from linebot.models import ImageMessage, MessageEvent, TextSendMessage

# Azure Blob Storage 連線字串
azure_storage_connection_string = "your_azure_storage_connection_string"

# Line Bot 相關設定
line_channel_access_token = "your_line_channel_access_token"
line_bot_api = LineBotApi(line_channel_access_token)


# 處理 Line Bot 收到的事件
def handle_message(event):
    message = event.message
    user_id = event.source.user_id

    # 如果收到的是圖片訊息
    if isinstance(message, ImageMessage):
        # 取得圖片訊息的內容
        image_content = line_bot_api.get_message_content(message.id)
        image_data = BytesIO(image_content.content)

        # 上傳到 Azure Blob Storage
        upload_to_azure_blob(image_data, user_id, "image.png")

        # 回覆訊息給使用者
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="圖片已成功上傳至 Azure Blob Storage")
        )


# 上傳到 Azure Blob Storage 函式
def upload_to_azure_blob(data, user_id, filename):
    blob_service_client = BlobServiceClient.from_connection_string(
        azure_storage_connection_string
    )

    # 假設你已經在 Azure Blob Storage 中建立了一個名為 "images" 的容器
    container_name = "images"
    container_client = blob_service_client.get_container_client(container_name)

    # 在 Blob Storage 中創建一個唯一的 Blob 名稱，例如使用使用者的 ID
    blob_name = f"{user_id}/{filename}"

    # 上傳到 Blob Storage
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(
        data, content_settings=ContentSettings(content_type="image/png")
    )


# Line Bot 接收事件的地方
# ...
# 設定 Line Bot 接收事件的處理函式
line_bot_api.set_message_event(handle_message)
# ...
