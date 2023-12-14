import cv2
import numpy as np
import requests
import tensorflow as tf
from tensorflow.keras.models import load_model


class ImagePredictor:
    def __init__(self, model_path, default_image_folder="https://example.com/images"):
        self.model = load_model(model_path)
        self.image_folder = default_image_folder

    def predict_image(self, image_filename):
        # 轉成 224x224
        image_url = f"{self.image_folder}/{image_filename}"
        response = requests.get(image_url)
        image_array = cv2.imdecode(np.frombuffer(response.content, np.uint8), -1)
        image = cv2.resize(image_array, (224, 224))

        # 壓縮特徵
        image = image.astype("float32")
        image /= 255.0

        # 模型預測
        image = np.expand_dims(image, axis=0)
        prediction = self.model.predict(image)

        # 解析預測結果，返回對應的價格範圍
        predicted_class = np.argmax(prediction)
        if predicted_class == 0:
            return "0-50元"
        elif predicted_class == 1:
            return "50-100元"
        elif predicted_class == 2:
            return "100-150元"
        elif predicted_class == 3:
            return "150-200元"
        elif predicted_class == 4:
            return "200-300元"
        else:  # 假設為類別 5
            return "300元以上"


if __name__ == "__main__":
    # 使用方法
    # from image_predictor import ImagePredictor

    # 指定模型路徑和默認圖片網址
    # ImagePredictor(模型位置, 圖片網址)
    predictor = ImagePredictor(
        r"./CNN-ResNet-DenseNet-01_best_model.h5",
        r"https://linebotblob.blob.core.windows.net/upload-image/test",
    )

    # 圖片預測
    # predictor.predict_image('圖片名稱')
    result = predictor.predict_image("A1.png")
    print(result)
