import re

from Z21_sql_query import SqlQuery

"""
NULL
American
Brunch
Desserts
Drinks
International
J&K
TW
Vegetarian
"""


def FoodQueryBuild(food_query_dict):
    # def QueryBuild():
    # food_dict = {
    #     "type": [
    #         "Brunch",
    #         "Desserts、Drinks",
    #         "American、International",
    #         "J&K",
    #         "TW",
    #         "Vegetarian",
    #         "random100m",
    #         "random500m",
    #         "random1000m",
    #     ],
    #     "price": ["100", "200", "None"],
    #     "feature": ["high_cp", "clean", "None"],
    #     "user_coordinate": "25.03413655927905, 121.54343435506429",
    # }

    # 透過字典取得相應的值
    distance = food_query_dict["distance"][:-1]  # 切片去掉最後一個字符
    price = food_query_dict["price"]
    type = "N'" + food_query_dict["type"] + "'"
    sort = "N'" + food_query_dict["sort"] + "'"

    # 分割字串，並取得下限和上限值
    if price == "300up":
        price_lower = "300"
        price_upper = "5000"
    else:
        price_lower, price_upper = map(int, price.split("~"))

    user_coordinate = food_query_dict["user_coordinate"]
    # 建立地理點
    target_location = f"geography::Point({user_coordinate}, 4326)"
    latitude, longitude = map(float, user_coordinate.split(","))
    print(target_location)
    print(f"distance={distance}")

    # 建立 SQL 查詢字串

    sql_query = f"""
        SELECT TOP 10
            sd.food_name,
            sd.price,
            sd.address,
            sd.pic_id,
            gc.name,
            GEOGRAPHY::Point(sd.latitude, sd.longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) AS distance
        FROM (
            SELECT TOP 100 PERCENT
                ID,
                food_name,
                price,
                address,
                pic_id,
                latitude,
                longitude
            FROM store_data
            WHERE
                latitude IS NOT NULL AND
                sort IS NOT NULL AND
                GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) <= {distance} AND
                (type = ({type}) OR ({type}) IS NULL) AND
                (price >= {price_lower} OR {price_lower} IS NULL) AND 
                (price <= {price_upper} OR {price_upper} IS NULL) AND
                sort = {sort}
            ORDER BY NEWID() -- 隨機排序
        ) sd
        LEFT JOIN google_commit gc ON sd.ID = gc.ID
        ORDER BY gc.name; -- 使用 name 進行排序
        """

    # sql_query = f"""
    #     SELECT TOP 10
    #         sd.food_name,
    #         sd.price,
    #         sd.address,
    #         sd.pic_id,
    #         gc.name,
    #         GEOGRAPHY::Point(sd.latitude, sd.longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) AS distance
    #     FROM (
    #         SELECT TOP 100 PERCENT -- 是一種用於指定返回所有行的方法
    #             ID,
    #             food_name,
    #             price,
    #             address,
    #             pic_id,
    #             latitude,
    #             longitude
    #         FROM store_data
    #         WHERE
    #             latitude IS NOT NULL AND
    #             sort IS NOT NULL AND
    #             GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) <= {distance} AND
    #             (type = ({type}) OR ({type}) IS NULL) AND
    #             (price >= {price_lower} OR {price_lower} IS NULL) AND
    #             (price <= {price_upper} OR {price_upper} IS NULL) AND
    #             sort = {sort}
    #         ORDER BY NEWID() -- 隨機排序
    #     ) sd
    #     LEFT JOIN google_commit gc ON sd.ID = gc.ID
    #     ORDER BY food_name; -- 以 distance 排序
    #     """

    return sql_query


def RandomFood():
    sql_query = f"""
        SELECT TOP 1
            sd.food_name,
            sd.price,
            sd.address,
            sd.pic_id,
            gc.name,
            sd.type,
            sd.sort
        FROM store_data sd
        INNER JOIN google_commit gc ON sd.ID = gc.ID
        WHERE
            sd.latitude IS NOT NULL AND
            sd.sort IS NOT NULL AND
            sd.sort <> 'none' AND
            (gc.name IS NOT NULL AND gc.name <> 'none')
        ORDER BY NEWID();
        """

    return sql_query


def StoreInfoQueryBuild(store_query_dict):
    store_query_dict["name"] = store_query_dict["name"].replace("'", "''")
    store_name = "N'" + store_query_dict["name"] + "'"
    store_info = store_query_dict["info"]

    sql_query = f"""
        SELECT TOP 1 SUBSTRING([{store_info}], 1, 3000) AS truncated_result
        FROM google_commit
        WHERE name LIKE '%' + {store_name} + '%';
        """

    return sql_query


def StoreFoodNameQueryBuild(store_query_dict):
    store_name = "N'" + store_query_dict["name"] + "'"
    store_info = store_query_dict["info"]

    sql_query = f"""
        -- 使用 name 查詢 google_commit 表格獲取對應的 id
        DECLARE @GoogleCommitId NVARCHAR(255);
        SELECT @GoogleCommitId = id
        FROM google_commit
        WHERE name like'%' + {store_name} + '%';

        -- 使用獲得的 id 查詢 store_data 表格獲取相應的 food_name 列表
        IF @GoogleCommitId IS NOT NULL
        BEGIN
            SELECT food_name
            FROM store_data
            WHERE id = @GoogleCommitId;
        END
        ELSE
        BEGIN
            PRINT '找不到對應的名稱。';
        END
        """

    return sql_query


if __name__ == "__main__":
    # 在這裡可以放入您想要執行的 SQL 查詢
    # query = "SELECT TOP 1 * FROM google_commit"
    query = FoodQueryBuild()
    result = SqlQuery(query)

    # 印出結果
    for row in result:
        print(row)
