import pyodbc


def commit_query(query):
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
