from Z21_sql_query import CommitQuery

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


if __name__ == "__main__":
    # 在這裡可以放入您想要執行的 SQL 查詢
    query = "SELECT TOP 1 * FROM google_commit"
    result = CommitQuery(query)

    # 印出結果
    for row in result:
        print(row)
