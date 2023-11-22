import pandas as pd
import pymysql

# 數據庫連接配置
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "PasswOrd!",
    "port": 3306,
    "database": "food",
}

# CSV 檔案路徑
csv_file_path = r"C:\Users\Sariel\Documents\BDSE32\foodpanda\2\dishes_info.csv"

# 使用 Pandas 讀取 CSV 文件
df = pd.read_csv(csv_file_path, encoding="utf-8-sig", header=None)

# 裁剪 'food_describe' 列的內容（假定它是第 4 列）
df[3] = df[3].astype(str).str.slice(0, 255)

# 替換缺失值為空字符串
df.fillna("", inplace=True)

# 建立數據庫連接
connection = pymysql.connect(**db_config)

try:
    with connection.cursor() as cursor:
        # 對於 DataFrame 中的每一行
        for index, row in df.iterrows():
            # 檢查 id 是否已存在
            id_check_sql = "SELECT EXISTS(SELECT 1 FROM food_list WHERE id=%s)"
            cursor.execute(id_check_sql, (row[2],))
            if cursor.fetchone()[0] == 0:  # id 不存在
                # 構造 SQL 插入語句
                insert_sql = """
                INSERT INTO food_list
                (image_position, food_name, id, food_describe, food_price, res_address, res_latitude,res_longitude, food_category, res_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, tuple(row))

    # 提交事務
    connection.commit()

except Exception as e:
    print(f"發生錯誤: {e}")
    connection.rollback()

finally:
    # 關閉數據庫連接
    connection.close()
