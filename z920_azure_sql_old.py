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
    type_list = food_query_dict["type"]
    # type = type_list[0]
    type = type_list
    user_coordinate = food_query_dict["user_coordinate"]
    distance = food_query_dict["distance"]
    # 建立地理點
    target_location = f"geography::Point({user_coordinate}, 4326)"
    latitude, longitude = map(float, user_coordinate.split(","))
    print(food_query_dict["type"][:6])
    if food_query_dict["type"] == "none":
        # match = re.search(r"\d+", food_query_dict["type"])
        # distance = int(match.group())
        print(f"distance={distance}")
        print(target_location)
        # 建立 SQL 查詢字串
        sql_query = f"""
            SELECT TOP 10
                food_name,
                GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) AS distance
            FROM store_data
            WHERE
                latitude IS NOT NULL AND
                GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) <= {distance}
            ORDER BY NEWID();
            """
    else:
        # 建立 SQL 查詢字串
        sql_query = f"""
            SELECT TOP 10
                name,
                GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) AS distance
            FROM store_data
            WHERE
                type IN ({type}) AND
                latitude IS NOT NULL AND
                GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) <= 1000
            ORDER BY distance;
        """
    return sql_query


def StoreInfoQueryBuild(store_query_dict):
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
