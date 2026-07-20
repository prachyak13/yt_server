import requests
from flask import Flask, Response, request

app = Flask(__name__)

TARGET_URL = "https://kicksball.com/player/tsp1"  # ลิงก์เว็บต้นทางของคุณ


@app.route("/")
def proxy():
  # จำลอง Headers เสมือนเปิดจากเบราว์เซอร์จริง
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Referer": "https://kicksball.com/",
  }

  try:
    # ดึงข้อมูลจากเว็บต้นทาง
    resp = requests.get(TARGET_URL, headers=headers, stream=True, timeout=10)

    # ส่งข้อมูลต่อให้แอปที่เรียกใช้งาน (Wiseplay)
    return Response(
        resp.iter_content(chunk_size=1024),
        status=resp.status_code,
        content_type=resp.headers.get("content-type", "text/html"),
    )
  except Exception as e:
    return f"เกิดข้อผิดพลาด: {str(e)}", 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
