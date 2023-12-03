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


def QueryBuild(food_query_dict):
    # def QueryBuild():
    # food_query_dict = {
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

    # 建立 SQL 查詢字串
    sql_query = f"""
        SELECT TOP 5
            name,
            GEOGRAPHY::Point(latitude, longitude, 4326).STDistance({target_location}) AS distance
        FROM google_commit
        WHERE
            type = '{type}' AND
            GEOGRAPHY::Point(latitude, longitude, 4326).STDistance({target_location}) <= 1000
        ORDER BY distance;
    """

    return sql_query


if __name__ == "__main__":
    # 在這裡可以放入您想要執行的 SQL 查詢
    # query = "SELECT TOP 1 * FROM google_commit"
    query = QueryBuild()
    result = SqlQuery(query)

    # 印出結果
    for row in result:
        print(row)
