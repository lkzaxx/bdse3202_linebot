import csv

from azure.storage.blob import BlobServiceClient


def list_blobs(connection_string, container_name):
    # 建立 BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # 取得容器客戶端
    container_client = blob_service_client.get_container_client(container_name)

    # 列舉 Blob
    blob_list = container_client.list_blobs()

    # 將 Blob 資訊寫入 CSV 檔案
    with open("blob_list.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Blob Name", "Size (bytes)", "Last Modified"])

        for blob in blob_list:
            writer.writerow([blob.name, blob.size, blob.last_modified])


# 設定 Azure Blob Storage 連線字串
azure_storage_connection_string = "DefaultEndpointsProtocol=https;AccountName=linebotblob;AccountKey=qHaeub7Trc8sj/9VGadrODLMEN4WmjZRv8+HMFZZzoks9b83MacRAnXCjvOd5xtpfYf704yfxXeC+AStMg4AwQ==;EndpointSuffix=core.windows.net"

# 設定容器名稱
container_name = "upload-image"

# 列舉 Blob 並匯出成 CSV
list_blobs(azure_storage_connection_string, container_name)
