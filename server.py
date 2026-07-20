import os
from flask import Flask, Response, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

@app.route('/')
def home():
    return "Stream Proxy Server is Running! Use /stream?url=YOUR_TARGET_URL"

@app.route('/stream')
def stream():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    m3u8_url = None

    try:
        with sync_playwright() as p:
            # รันเบราว์เซอร์แบบ Headless พร้อมตั้งค่าสำหรับ Linux/Render
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page()

            # ดักจับ Network Request เพื่อหาไฟล์ .m3u8
            def intercept_request(route, request):
                nonlocal m3u8_url
                if ".m3u8" in request.url and not m3u8_url:
                    m3u8_url = request.url
                route.continue_()

            page.route("**/*", intercept_request)

            # เข้าหน้าเว็บเป้าหมายและรอโหลด
            page.goto(target_url, timeout=60000)
            
            # เผื่อหน้าเว็บต้องกดเล่นวิดีโอ จำลองการคลิกหน้าจอ
            try:
                page.click("body", timeout=5000)
            except:
                pass

            # รอให้ Playwright จับลิงก์ .m3u8 (สูงสุด 15 วินาที)
            import time
            start_time = time.time()
            while not m3u8_url and (time.time() - start_time) < 15:
                time.sleep(0.5)

            browser.close()

        if m3u8_url:
            # ส่งพิกัดลิงก์ .m3u8 กลับไปให้ตัวเล่น (Redirect)
            return Response(f"Redirecting to stream: {m3u8_url}", status=302, headers={"Location": m3u8_url})
        else:
            return jsonify({"error": "Could not capture .m3u8 stream URL"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # ดึงพอร์ตจาก Render หรือกำหนดค่าเริ่มต้นเป็น 10000
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
