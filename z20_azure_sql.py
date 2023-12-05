from Z21_sql_query import SqlQuery
import re

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


def StoreQueryBuild(food_query_dict):
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

    # 建立地理點
    target_location = f"geography::Point({user_coordinate}, 4326)"
    latitude, longitude = map(float, user_coordinate.split(","))
    print(food_query_dict["type"][:6])
    if food_query_dict["type"][:6] == "random":
        match = re.search(r"\d+", food_query_dict["type"])
        distance = int(match.group())
        print(f"distance={distance}")
        print(target_location)
        # 建立 SQL 查詢字串
        sql_query = f"""
            SELECT TOP 3
                name,
                GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) AS distance
            FROM google_commit
            WHERE
                latitude IS NOT NULL AND
                GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) <= {distance}
            ORDER BY NEWID();
            """
    else:
        # 建立 SQL 查詢字串
        sql_query = f"""
            SELECT TOP 3
                name,
                GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) AS distance
            FROM google_commit
            WHERE
                type IN ({type}) AND
                GEOGRAPHY::Point(latitude, longitude, 4326).STDistance(GEOGRAPHY::Point({latitude}, {longitude}, 4326)) <= 1000
            ORDER BY distance;
        """
    return sql_query


def CommitQueryBuild(store_query_dict):
    store_name = "N" + store_query_dict["name"]

    sql_query = f"""
        SELECT commit
        FROM google_commit
        WHERE name LIKE '%' + {store_name} + '%' AND commit IS NOT NULL;
        """

    return sql_query


if __name__ == "__main__":
    # 在這裡可以放入您想要執行的 SQL 查詢
    # query = "SELECT TOP 1 * FROM google_commit"
    query = StoreQueryBuild()
    result = SqlQuery(query)

    # 印出結果
    for row in result:
        print(row)
