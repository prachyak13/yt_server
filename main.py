import os
import requests
from flask import Flask, request, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

def get_direct_url(video_id):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': '18',  # เลือกไฟล์ MP4 360p เพื่อให้ Render ประหยัดแบนด์วิธ และเพื่อนๆ โหลดไว
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
    except Exception as e:
        print(f"❌ Error yt_dlp: {e}")
        return None

@app.route('/play/<video_id>')
def proxy_video(video_id):
    stream_url = get_direct_url(video_id)
    if not stream_url:
        return "Video Not Found or Blocked by YouTube", 404

    # 1. ดึง Header 'Range' จากแอป Wiseplay ของผู้ใช้งาน (ถ้ามี) เพื่อให้กดกรอเดินหน้า-ถอยหลังได้
    headers = {}
    if 'Range' in request.headers:
        headers['Range'] = request.headers['Range']
    
    # ใส่ User-Agent เลียนแบบเบราว์เซอร์ทั่วไปเพื่อความเสถียร
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    # 2. ให้ Render วิ่งไปดึงข้อมูลสตรีมมาจาก YouTube
    req = requests.get(stream_url, headers=headers, stream=True)

    # 3. ฟังก์ชันสำหรับส่งต่อข้อมูลดิบ (Chunk) ออกไปให้เครื่องเล่นทีละนิด เพื่อไม่ให้แรมของ Render เต็ม
    def generate():
        try:
            for chunk in req.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        except Exception as e:
            print(f"Stream interrupted: {e}")

    # 4. คัดลอก Header ที่จำเป็นจาก YouTube ส่งกลับไปให้แอปเครื่องเล่นปลายทาง
    response_headers = {}
    for key, value in req.headers.items():
        if key.lower() in ['content-type', 'content-length', 'content-range', 'accept-ranges']:
            response_headers[key] = value

    # ส่งข้อมูลกลับไปแบบ HTTP 206 (Partial Content) หรือ 200 ตามที่รับมาจาก YouTube
    return Response(
        stream_with_context(generate()), 
        status=req.status_code, 
        headers=response_headers
    )

if __name__ == '__main__':
    # พอร์ตอัตโนมัติสำหรับรองรับระบบของ Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
