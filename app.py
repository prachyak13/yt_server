import requests
from flask import Flask, Response, request

app = Flask(__name__)


@app.route("/stream")
def proxy():
  # 1. รับรหัสช่องจาก URL ที่ส่งมา (เช่น ?id=tsp1)
  channel_id = request.args.get("id")

  if not channel_id:
    return "กรุณาระบุรหัสช่อง เช่น ?id=tsp1", 400

  # 2. กำหนด URL ปลายทางตามรหัสช่อง
  target_url = f"https://kicksball.com/player/{channel_id}"

  # 3. กำหนดค่า Headers จำลองเสมือนเปิดจากเบราว์เซอร์จริง
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/124.0.0.0 Safari/537.36"
      ),
      "Referer": "https://kicksball.com/",
      "Accept": (
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
      ),
      "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
  }

  try:
    # 4. ส่งคำขอไปยังเว็บต้นทาง (รองรับการติดตาม Redirect อัตโนมัติ)
    resp = requests.get(
        target_url, headers=headers, stream=True, timeout=15, allow_redirects=True
    )

    # 5. กรองและส่งต่อ Headers รวมถึงเนื้อหาไปยังแอปที่เรียกใช้งาน (Wiseplay)
    excluded_headers = [
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    ]
    response_headers = [
        (name, value)
        for name, value in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    return Response(
        resp.iter_content(chunk_size=4096),
        status=resp.status_code,
        headers=response_headers,
    )

  except requests.exceptions.Timeout:
    return "เกิดข้อผิดพลาด: การเชื่อมต่อใช้เวลานานเกินไป (Timeout)", 504
  except Exception as e:
    return f"เกิดข้อผิดพลาดระบบ: {str(e)}", 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
