import pyodbc


def CommitQuery(query):
    server = "linebot.database.windows.net"
    database = "data"
    username = "bdse32"
    password = "{Bigdata32!}"
    driver = "{ODBC Driver 17 for SQL Server}"

    connection_string = (
        "DRIVER="
        + driver
        + ";SERVER="
        + server
        + ";PORT=1433;DATABASE="
        + database
        + ";UID="
        + username
        + ";PWD="
        + password
    )

    with pyodbc.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows


if __name__ == "__main__":
    # 在這裡可以放入您想要執行的 SQL 查詢
    query = "SELECT TOP 1 * FROM google_commit"
    result = CommitQuery(query)

    # 印出結果
    for row in result:
        print(row)
