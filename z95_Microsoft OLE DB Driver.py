import pyodbc

# 連接到 SQL Server
connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=linebot.database.windows.net;DATABASE=data;UID=bdse32;PWD=Bigdata32!"
connection = pyodbc.connect(connection_string)

# 使用連接執行 SQL 查詢
cursor = connection.cursor()
cursor.execute("SELECT TOP 1 * FROM google_commit")
rows = cursor.fetchall()

# 關閉連接
connection.close()
