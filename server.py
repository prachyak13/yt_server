import os
from flask import Flask, Response, redirect, request
from playwright.sync_api import sync_playwright

app = Flask(__name__)


def extract_m3u8(page_url):
  with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
    )
    page = browser.new_page()
    target_m3u8 = None

    def handle_request(route, request):
      nonlocal target_m3u8
      if ".m3u8" in request.url and not target_m3u8:
        target_m3u8 = request.url
      route.continue_()

    page.route("**/*", handle_request)

    try:
      page.goto(page_url, timeout=30000)
      page.wait_for_timeout(6000)
    except Exception as e:
      print(f"Error: {e}")

    browser.close()
    return target_m3u8


@app.route("/stream")
def stream():
  web_url = request.args.get("url")
  if not web_url:
    return (
        "กรุณาระบุลิงก์ เช่น /stream?url=https://kicksball.com/player/tsp1",
        400,
    )

  print(f"กำลังดึงลิงก์จาก: {web_url}")
  m3u8_url = extract_m3u8(web_url)

  if not m3u8_url:
    return "ไม่พบลิงก์ .m3u8 ในหน้าเว็บนี้", 404

  print(f"เจอลิงก์แล้ว: {m3u8_url}")
  return redirect(m3u8_url)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
