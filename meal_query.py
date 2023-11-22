import pymysql
from pymysql.constants import CLIENT


# 生成符合USER需求之附近餐點
class FoodDatabase:
    def __init__(self, db_config):
        self.db_config = db_config
        # 取得位置訊息(未完成)
        self.default_position = (23.7330, 120.5354)

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def query_meal(self, food_category=None, price=None, googleReviewFeatures=None):
        # 取得位置訊息(未完成)
        latitude, longitude = self.default_position

        # 价格设置为区间价格
        upPrice = lowPrice = None
        if price is not None:
            upPrice = price * 1.15
            lowPrice = price * 0.85

        # 开始构建 SQL 查询
        query = "SELECT * FROM food_list WHERE "
        query_conditions = []

        # 添加位置条件
        distance_condition = f"ST_Distance_Sphere(point(res_longitude, res_latitude), point({longitude}, {latitude})) <= 3000"
        query_conditions.append(distance_condition)

        # 添加食物类别条件
        if food_category is not None:
            category_condition = f"food_category = '{food_category}'"
            query_conditions.append(category_condition)

        # 添加价格范围条件
        if price is not None:
            price_condition = f"food_price BETWEEN {lowPrice} AND {upPrice}"
            query_conditions.append(price_condition)

        # 添加 Google 评论特征条件
        if googleReviewFeatures is not None:
            review_condition = googleReviewFeatures
            query_conditions.append(review_condition)

        # 组合查询条件
        query += ' AND '.join(query_conditions)

        # 隨機給三家
        query += " ORDER BY RAND() LIMIT 3"

        # 执行查询
        with self._get_connection().cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            if results:
                return results
            else:
                return None


# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'PasswOrd!',
    'port': 3306,
    'database': 'food',
    'charset': 'utf8mb4',
    'client_flag': CLIENT.MULTI_STATEMENTS
}

# 主程序


def main():
    food_db = FoodDatabase(db_config)

    try:
        meals = food_db.query_meal(food_category='Drinks', price=45)
        if meals:
            for meal in meals:
                print(meal)
        else:
            print("没有找到符合条件的餐点。")
    except Exception as e:
        print(f"发生错误：{e}")


if __name__ == "__main__":
    main()
