import os
from flask import Flask, Response
import yt_dlp
import requests

app = Flask(__name__)

def get_direct_url(video_id):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    # กำหนด format เป็น itag 18 (MP4 360p) ซึ่งมีทั้งภาพและเสียง 
    # ขนาดไฟล์ไม่ใหญ่เกินไป ช่วยให้สตรีมผ่านคลาวด์ฟรีได้ลื่นไหลและเสถียรที่สุด
    ydl_opts = {
        'format': '18', 
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
    except Exception as e:
        return None

@app.route('/play/<video_id>')
def stream_proxy(video_id):
    stream_url = get_direct_url(video_id)
    if not stream_url:
        return "ไม่สามารถดึงข้อมูลจาก YouTube ได้", 500

    # สร้างท่อส่งข้อมูล (Proxy) ดึงสัญญาณจาก YouTube ผ่าน Render ส่งต่อไปที่แอปเครื่องเล่น
    req = requests.get(stream_url, stream=True)
    
    def generate():
        for chunk in req.iter_content(chunk_size=4096):
            yield chunk

    return Response(
        generate(),
        content_type=req.headers.get('Content-Type', 'video/mp4'),
        headers={"Accept-Ranges": "bytes"}
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
