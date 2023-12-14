import os

from azure.storage.blob import BlobServiceClient, ContentSettings


def upload_to_azure_blob(local_file_path, container_name, blob_name, connection_string):
    # 建立 BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # 取得或創建容器
    container_client = blob_service_client.get_container_client(container_name)
    # container_client.create_container()

    # 取得檔案名稱
    file_name = os.path.basename(local_file_path)

    # 上傳 Blob
    blob_client = container_client.get_blob_client(os.path.join(blob_name, file_name))
    with open(local_file_path, "rb") as data:
        blob_client.upload_blob(
            data, content_settings=ContentSettings(content_type="image/png")
        )


# 設定 Azure Blob Storage 連線字串
azure_storage_connection_string = "DefaultEndpointsProtocol=https;AccountName=linebotblob;AccountKey=qHaeub7Trc8sj/9VGadrODLMEN4WmjZRv8+HMFZZzoks9b83MacRAnXCjvOd5xtpfYf704yfxXeC+AStMg4AwQ==;EndpointSuffix=core.windows.net"

# 設定本機圖片檔案路徑
local_file_path = f"./A1.png"

# 設定 Azure Blob Storage 容器名稱和 Blob 名稱
container_name = "upload-image"
blob_name = "test"

# 上傳圖片至 Azure Blob Storage
upload_to_azure_blob(
    local_file_path, container_name, blob_name, azure_storage_connection_string
)
