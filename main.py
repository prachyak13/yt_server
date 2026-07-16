import os
import requests
from flask import Flask, request, Response, stream_with_context
import yt_dlp

app = Flask(__name__)

def get_direct_url(video_id):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # ตั้งค่า yt-dlp ให้ปลอมตัวเป็นแอป Android/iOS เพื่อลดโอกาสโดน YouTube บล็อก IP
    ydl_opts = {
        'format': '18',  # เลือกไฟล์ MP4 360p เพื่อให้ Render ทำงานไหลลื่น ไม่กินแบนด์วิธสูง
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
    except Exception as e:
        # บันทึก Error จริงลงในระบบ Log ของ Render เพื่อไว้สำหรับตรวจสอบ
        print(f"❌ YouTube Blocked Error: {e}")
        return None

@app.route('/play/<video_id>')
def proxy_video(video_id):
    stream_url = get_direct_url(video_id)
    if not stream_url:
        return "Video Not Found or Blocked by YouTube", 404

    # 1. ดึง Header 'Range' จากแอป Wiseplay (ถ้ามี) เพื่อให้ระบบรองรับการกดกรอวิดีโอ
    headers = {}
    if 'Range' in request.headers:
        headers['Range'] = request.headers['Range']
    
    # ใส่ User-Agent เลียนแบบเบราว์เซอร์ทั่วไปเพื่อความเสถียรในการดึงข้อมูล
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    # 2. สั่งให้ Render วิ่งไปดึงข้อมูลสตรีมมาจาก YouTube ตรงๆ
    req = requests.get(stream_url, headers=headers, stream=True)

    # 3. ฟังก์ชันสำหรับส่งต่อข้อมูลดิบ (Chunk) ออกไปให้เครื่องเล่นทีละนิด ป้องกันปัญหาแรมเซิร์ฟเวอร์เต็ม
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

    # ส่งข้อมูลกลับไปในรูปแบบ HTTP 206 (Partial Content) หรือ 200 ตามที่ YouTube ส่งมา
    return Response(
        stream_with_context(generate()), 
        status=req.status_code, 
        headers=response_headers
    )

if __name__ == '__main__':
    # ระบบเลือกพอร์ตอัตโนมัติสำหรับรองรับโครงสร้างของ Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
