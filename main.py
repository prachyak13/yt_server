import os
from flask import Flask, redirect
import yt_dlp

app = Flask(__name__)

def get_live_url(video_id):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {'format': 'best', 'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
    except Exception as e:
        return None

@app.route('/play/<video_id>')
def play_video(video_id):
    stream_url = get_live_url(video_id)
    if stream_url:
        return redirect(stream_url)
    return "Error", 500

if __name__ == '__main__':
    # คลาวด์จะกำหนด Port มาให้เล่นอัตโนมัติผ่าน Environment Variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
