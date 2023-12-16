from io import BytesIO

from azure.storage.blob import BlobServiceClient


def upload_image_to_azure_blob(image_name, image_content):  # Azure Blob Storage 設定
    connection_string = "DefaultEndpointsProtocol=https;AccountName=linebotblob;AccountKey=qHaeub7Trc8sj/9VGadrODLMEN4WmjZRv8+HMFZZzoks9b83MacRAnXCjvOd5xtpfYf704yfxXeC+AStMg4AwQ==;EndpointSuffix=core.windows.net"
    container_name = "upload-image"
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(image_name)

        # 將 bytes 資料轉換為 BytesIO 物件
        image_stream = BytesIO(image_content)

        # 使用 BytesIO 物件進行上傳
        blob_client.upload_blob(image_stream, overwrite=True)

        print(f"Image {image_name} uploaded to Azure Blob Storage.")
    except Exception as e:
        print(f"Error uploading image to Azure Blob Storage: {str(e)}")
