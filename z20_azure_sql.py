from Z21_azure_sql_commit_query import commit_query

if __name__ == "__main__":
    # 在這裡可以放入您想要執行的 SQL 查詢
    query = "SELECT TOP 1 * FROM google_commit"
    result = commit_query(query)

    # 印出結果
    for row in result:
        print(row)
