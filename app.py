from flask import Flask, Response, render_template_string
import cv2
import atexit
import os
import datetime
import glob

app = Flask(__name__)

# --- Cấu hình ---
RTSP_URL = "rtsp://admin:123456@192.168.1.100:554/Streaming/Channels/101"
SAVE_DIR = r"C:\Users\Admin\Desktop\snapshot_demo\static"
MAX_IMAGES = 20  # 🔹 Giới hạn chỉ giữ 20 ảnh mới nhất

# --- Khởi tạo camera ---
cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
if not cap.isOpened():
    raise RuntimeError("Không mở được camera RTSP. Kiểm tra địa chỉ hoặc kết nối mạng!")

os.makedirs(SAVE_DIR, exist_ok=True)

def cleanup():
    print("Đóng kết nối camera...")
    cap.release()

atexit.register(cleanup)

def cleanup_old_images():
    """Xóa ảnh cũ, chỉ giữ lại MAX_IMAGES ảnh mới nhất."""
    images = sorted(glob.glob(os.path.join(SAVE_DIR, "*.jpg")), key=os.path.getmtime, reverse=True)
    if len(images) > MAX_IMAGES:
        for old_file in images[MAX_IMAGES:]:
            try:
                os.remove(old_file)
                print(f"🗑️ Đã xóa ảnh cũ: {old_file}")
            except Exception as e:
                print(f"Lỗi khi xóa {old_file}: {e}")

# --- HTML template ---
HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>📸 Snapshot Demo</title>
    <style>
        img { max-width: 100%; height: auto; }
        body { text-align: center; font-family: Arial; }
    </style>
</head>
<body>
    <h1>📸 Snapshot Demo (RTSP)</h1>
    <img id="snapshot" src="/snapshot" alt="Snapshot">
    <p>Mỗi 10 giây ảnh sẽ tự cập nhật và tự lưu vào thư mục <b>static</b>.</p>

    <script>
        setInterval(() => {
            const img = document.getElementById('snapshot');
            img.src = '/snapshot?time=' + new Date().getTime();
        }, 10000); // 10000ms = 10 giây
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/snapshot")
def snapshot():
    ret, frame = cap.read()
    if not ret:
        return "Không đọc được frame từ camera RTSP", 500

    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return "Không encode được frame", 500

    # --- Lưu ảnh ra file ---
    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
    filepath = os.path.join(SAVE_DIR, filename)
    cv2.imwrite(filepath, frame)
    print(f"💾 Đã lưu ảnh: {filepath}")

    # --- Xóa ảnh cũ ---
    cleanup_old_images()

    return Response(buffer.tobytes(), mimetype='image/jpeg')


if __name__ == "__main__":
    try:
        app.run(host="127.0.0.1", port=5000, debug=False)
    finally:
        cleanup()
