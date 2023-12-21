import configparser

import pyodbc


def SqlQuery(query):
    config = configparser.ConfigParser()
    config.read("../LINEBOT_API_KEY/azure_sql_config.ini")

    server = config.get("Database", "server")
    database = config.get("Database", "database")
    username = config.get("Database", "username")
    password = config.get("Database", "password")
    driver = config.get("Database", "driver")

    connection_string = f"DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no"

    with pyodbc.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows


if __name__ == "__main__":
    # 在這裡可以放入您想要執行的 SQL 查詢
    query = "SELECT TOP 1 * FROM google_commit"
    result = SqlQuery(query)

    # 印出結果
    for row in result:
        print(row)
