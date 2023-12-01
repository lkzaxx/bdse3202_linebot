import pyodbc

server = "linebot.database.windows.net"
database = "data"
username = "bdse32"
password = "{Bigdata32!}"
driver = "{ODBC Driver 17 for SQL Server}"

with pyodbc.connect(
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
) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT TOP 1 * FROM google_commit")
        row = cursor.fetchone()
        while row:
            print(row)  # 印出整行資料
            row = cursor.fetchone()
