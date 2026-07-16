import os
from flask import Flask, redirect, abort
import yt_dlp

app = Flask(__name__)

def get_direct_url(video_id):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': '18',  # เลือกไฟล์ MP4 360p ที่มีภาพและเสียงในตัว
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
    except Exception as e:
        print(f"Error extracting URL: {e}")
        return None

@app.route('/play/<video_id>')
def play_video(video_id):
    stream_url = get_direct_url(video_id)
    if stream_url:
        # สั่งให้ Render ส่งลิงก์ตรง googlevideo.com กลับไปให้เครื่องเล่นทันที
        return redirect(stream_url)
    else:
        return "Video Not Found", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
