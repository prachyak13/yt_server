import os
from flask import Flask, Response, request
import yt_dlp
import requests

app = Flask(__name__)

def get_direct_url(video_id):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': '18',  # ดึงไฟล์ 360p MP4 ที่มีทั้งภาพและเสียงในตัว
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/play/<video_id>')
def stream_proxy(video_id):
    stream_url = get_direct_url(video_id)
    if not stream_url:
        return "Video Not Found", 404

    # 1. ดักจับคำขอ Range (ช่วงของไฟล์) ที่ Wiseplay ส่งมา แล้วส่งต่อไปให้ YouTube
    headers = {}
    if 'Range' in request.headers:
        headers['Range'] = request.headers['Range']

    # ดึงข้อมูลจาก YouTube ตามช่วงที่แอปขอมา
    req = requests.get(stream_url, headers=headers, stream=True)
    
    # 2. สร้างโครงสร้างการตอบกลับ โดยใช้ Status Code เดิมจาก YouTube (เช่น 206 Partial Content)
    def generate():
        for chunk in req.iter_content(chunk_size=8192):
            yield chunk

    response = Response(generate(), status=req.status_code)
    
    # 3. ส่ง Header สำคัญที่เกี่ยวกับช่วงข้อมูลกลับไปให้ Wiseplay ครบถ้วน
    for key in ['Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges']:
        if key in req.headers:
            response.headers[key] = req.headers[key]

    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
