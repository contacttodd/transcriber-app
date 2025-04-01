import pyodbc
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()
CONNECTION_STRING = os.getenv("CONNECTION_STRING")


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


def fetch_indexes():
    query = """
    SELECT TOP (1) [indexNoPk], [LockQ], [type], [username], [gComment], [produc], [CustName]
    FROM [DB_164462_kdsisdlo291].[dbo].[Quote]
    WHERE [produc] = 'Pending'
    """
    return execute_query(query)


def execute_query(query, params=()):
    conn = get_db_connection()
    if not conn:
        logging.error("Database connection failed.")
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            # logging.info(f"Executed query: {query} with params: {params}")
            return results
    except pyodbc.Error as e:
        logging.error(f"Error executing query: {e}")
        return []
    finally:
        conn.close()


def get_yt(index_no_pk):
    query = """
    SELECT TOP (1) [Address1], [City], [State]
    FROM [DB_164462_kdsisdlo291].[dbo].[ClientesRCHome]
    WHERE [indexNoPk] = ?
    """
    return execute_query(query, (index_no_pk,))


def get_db_connection():
    try:
        connection = pyodbc.connect(CONNECTION_STRING)
        logging.info("Successfully connected to the database.")
        return connection
    except pyodbc.Error as e:
        logging.error(f"Error connecting to SQL Server: {e}")
        return None


# Check to confirm there are pending records to process
# Check to see if the transcript already exists - Check webhost for file
# 1 - Check to see if the audio already exists - Check Google bucket
# 2 - If not, download the audio and upload to GCS - Part 2
#       Process the audio to transcript - Part 2
# Process the transcript to resource - Part 2
# Update the Quote table
# Process resources
#   FTP the resource

if __name__ == "__main__":
    # run()
    quote_indexes = fetch_indexes()
    if quote_indexes:
        logging.info("Step 3: Records found for processing.")
        for item in quote_indexes:
            quote_index_no = item[0]
            clientes_index_no = item[1]
            type_info = item[2]
            username = item[3]
            g_comment = item[4]
            produc_val = item[5]
            cust_name = item[6]

            print(f"Step 4: Processing Quote Index No: {quote_index_no}")
            logging.info(f"Step 4: Processing Quote Index No: {quote_index_no}")

            print(f"Step 5: Clientes Index No: {clientes_index_no}")
            logging.info(f"Step 5: Clientes Index No: {clientes_index_no}")

            # Step 5a: Check if the transcript already exists locally
            quote_records = get_yt(
                clientes_index_no
            )  # Fetch YouTube address from ClientesRCHome table

            if quote_records:
                yt_address = quote_records[0][
                    0
                ]  # Address1 field holds the YouTube video link
                start_mark = quote_records[0][
                    1
                ]  # City field holds the start time of the video segment
                end_mark = quote_records[0][
                    2
                ]  # State field holds the end time of the video segment
