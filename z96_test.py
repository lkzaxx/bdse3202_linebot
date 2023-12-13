import pyodbc


class SqlDatabase:
    def __init__(
        self,
        server,
        database,
        username,
        password,
        driver="{ODBC Driver 17 for SQL Server}",
    ):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.connection_string = f"""DRIVER={self.driver};
            SERVER={self.server};
            PORT=1433;DATABASE={self.database};
            UID={self.username};
            PWD={self.password};
            Encrypt=yes;TrustServerCertificate=no"""

    def execute_query(self, query):
        with pyodbc.connect(self.connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return rows


if __name__ == "__main__":
    # 創建SqlDatabase實例
    db = SqlDatabase(
        server="linebot.database.windows.net",
        database="data",
        username="bdse32",
        password="{Bigdata32!}",
    )

    # 定義SQL查詢
    query = "SELECT TOP 1 * FROM google_commit"

    # 使用SqlDatabase類別執行查詢
    result = db.execute_query(query)

    # 印出結果
    for row in result:
        print(row)
