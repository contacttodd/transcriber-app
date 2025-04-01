import os
import pyodbc
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from pydub import AudioSegment
import yt_dlp
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv("CONNECTION_STRING")
GCS_BUCKET = "spchtotxt1stop"

def get_db_connection():
    try:
        return pyodbc.connect(CONNECTION_STRING)
    except pyodbc.Error as e:
        logging.error(f"DB connection error: {e}")
        return None

def fetch_pending_video():
    query = """
    SELECT TOP 1 [indexNoPk], [LockQ]
    FROM [DB_164462_kdsisdlo291].[dbo].[Quote]
    WHERE [produc] = 'Pending'
    """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()
        return result
    return None

def fetch_youtube_details(lock_q):
    query = """
    SELECT TOP 1 [Address1], [City], [State]
    FROM [DB_164462_kdsisdlo291].[dbo].[ClientesRCHome]
    WHERE [indexNoPk] = ?
    """
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(query, (lock_q,))
        result = cursor.fetchone()
        conn.close()
        return result
    return None

def extract_video_id(url):
    import re
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def upload_to_gcs(local_path, dest_blob_name):
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(dest_blob_name)
        blob.upload_from_filename(local_path)
        logging.info(f"Uploaded {local_path} to GCS as {dest_blob_name}")
        return True
    except Exception as e:
        logging.error(f"GCS upload failed: {e}")
        return False

def download_and_clip(video_id, start_min, end_min):
    output_folder = "downloads"
    os.makedirs(output_folder, exist_ok=True)
    filename_wav = f"{video_id}.wav"
    filepath = os.path.join(output_folder, filename_wav)

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "outtmpl": f"{output_folder}/{video_id}.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    if start_min != 0 or end_min != 0:
        audio = AudioSegment.from_file(filepath)
        clip = audio[start_min * 60000 : end_min * 60000]
        clip.export(filepath, format="wav")

    return filepath

def download_audio_for_pending_video():
    try:
        pending = fetch_pending_video()
        if not pending:
            return "No pending video found"

        quote_id, clientes_id = pending
        video_data = fetch_youtube_details(clientes_id)

        if not video_data:
            return "No video details found"

        address, start, end = video_data
        video_id = extract_video_id(address)
        start = int(start or 0)
        end = int(end or 0)

        local_path = download_and_clip(video_id, start, end)
        gcs_file_name = os.path.basename(local_path)

        success = upload_to_gcs(local_path, gcs_file_name)
        if success:
            return f"Audio for video {video_id} downloaded and uploaded to GCS as {gcs_file_name}"
        else:
            return "Audio download succeeded but GCS upload failed"

    except Exception as e:
        logging.error(f"Download error: {e}")
        return f"Error: {str(e)}"
