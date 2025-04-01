import pyodbc


def run():
    try:
        conn = pyodbc.connect(
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=s26.winhost.com;"
            "Database=DB_164462_kdsisdlo291;"
            "UID=DB_164462_kdsisdlo291_user;"
            "PWD=ksdh1o1KSDY;"
        )
        print("✅ Successfully connected to the database.")

        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 * FROM Quote")
        row = cursor.fetchone()
        if row:
            print("📦 Sample row:", row)
        else:
            print("⚠️ No data found in Quote table.")
        conn.close()

    except Exception as e:
        print("❌ Error during execution:")
        print(str(e))


if __name__ == "__main__":
    run()
