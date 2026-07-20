import re
from flask import Flask, Response, redirect, request
import requests

app = Flask(__name__)


@app.route("/stream")
def proxy():
  channel_id = request.args.get("id")
  if not channel_id:
    return "กรุณาระบุรหัสช่อง เช่น ?id=tsp1", 400

  target_url = f"https://kicksball.com/player/{channel_id}"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/124.0.0.0 Safari/537.36"
      ),
      "Referer": "https://kicksball.com/",
  }

  try:
    # 1. ดึงหน้าเว็บต้นทางมาก่อน
    resp = requests.get(target_url, headers=headers, timeout=10)

    # 2. ค้นหาลิงก์ไฟล์สตรีม (.m3u8) ที่ซ่อนอยู่ในโค้ดหน้าเว็บ
    m3u8_match = re.search(r"https?://[^\s\"']+\.m3u8[^\s\"']*", resp.text)

    if m3u8_match:
      stream_url = m3u8_match.group(0)
      # ถ้าเจอลิงก์สตรีมจริง ให้ Redirect ไปที่ลิงก์นั้นทันทีเพื่อให้เล่นได้เลย
      return redirect(stream_url, code=302)
    else:
      # ถ้าไม่เจอลิงก์ อาจจะต้องตรวจสอบรหัสช่องอีกครั้ง
      return (
          "ไม่พบลิงก์สตรีมในหน้านี้ (รหัสช่องอาจจะไม่ถูกต้องหรือไม่มีการถ่ายทอดสด)",
          404,
      )

  except Exception as e:
    return f"เกิดข้อผิดพลาด: {str(e)}", 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
