from flask import Flask, Response, render_template_string
import cv2
import time
import atexit
import os
import datetime

app = Flask(__name__)

# --- Khởi tạo camera 1 lần ---
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not cap.isOpened():
    raise RuntimeError("Không mở được camera. Kiểm tra kết nối webcam!")

# --- Đường dẫn lưu ảnh ---
SAVE_DIR = r"C:\Users\Admin\Desktop\snapshot_demo\static"
os.makedirs(SAVE_DIR, exist_ok=True)

def cleanup():
    print("Đóng kết nối camera...")
    cap.release()

atexit.register(cleanup)

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
    <h1>📸 Snapshot Demo</h1>
    <img id="snapshot" src="/snapshot" alt="Snapshot">
    <p>Mỗi 2 giây ảnh sẽ tự cập nhật và tự lưu vào thư mục <b>static</b>.</p>

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
        return "Không đọc được frame từ camera", 500

    # Encode ảnh thành JPEG
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return "Không encode được frame", 500

    # --- Lưu ảnh ra file ---
    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
    filepath = os.path.join(SAVE_DIR, filename)
    cv2.imwrite(filepath, frame)
    print(f"Đã lưu ảnh: {filepath}")

    return Response(buffer.tobytes(), mimetype='image/jpeg')


if __name__ == "__main__":
    try:
        app.run(host="127.0.0.1", port=5000, debug=False)
    finally:
        cleanup()
