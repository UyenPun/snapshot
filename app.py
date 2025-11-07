from flask import Flask, Response, render_template_string
import cv2
import atexit
import os
import datetime
import glob
import time

app = Flask(__name__)

# --- Cấu hình ---
# RTSP_URL = "rtsp://admin:123456@192.168.1.100:554/Streaming/Channels/101"
SAVE_DIR = r"C:\Users\Admin\Desktop\snapshot_demo\static"
MAX_IMAGES = 20  # 🔹 Giữ tối đa 20 ảnh mới nhất

# --- Khởi tạo camera ---
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # Dùng webcam
if not cap.isOpened():
    raise RuntimeError("❌ Không mở được camera! Kiểm tra thiết bị hoặc kết nối mạng.")

# --- Tạo thư mục lưu ảnh nếu chưa có ---
os.makedirs(SAVE_DIR, exist_ok=True)

# --- Dọn tài nguyên khi thoát ---
def cleanup():
    print("🛑 Đóng kết nối camera...")
    cap.release()

atexit.register(cleanup)

# --- Hàm xóa ảnh cũ ---
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

# --- HTML Template ---
HTML_PAGE = """
<!doctype html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>📸 Snapshot + Playback</title>
    <style>
        body { text-align: center; font-family: Arial; background: #f5f5f5; margin: 20px; }
        img { max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.2); }
        h1 { color: #333; }
        .gallery { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-top: 20px; }
        .gallery img { width: 180px; height: auto; cursor: pointer; border: 2px solid transparent; transition: all 0.3s; }
        .gallery img:hover { border-color: #007bff; transform: scale(1.05); }
        .playback-title { margin-top: 40px; color: #555; }
    </style>
</head>
<body>
    <h1>📸 Snapshot Demo (Webcam / RTSP)</h1>
    <img id="snapshot" src="/snapshot" alt="Snapshot hiện tại">
    <p>Mỗi 10 giây ảnh sẽ tự cập nhật và lưu vào thư mục <b>static</b>.</p>

    <script>
        setInterval(() => {
            const img = document.getElementById('snapshot');
            img.src = '/snapshot?time=' + new Date().getTime();
            // 🔁 Reload lại toàn trang để cập nhật Playback gallery
            setTimeout(() => location.reload(), 500);
        }, 10000); // 10000ms = 10 giây
    </script>

    <h2 class="playback-title">🕓 Playback (xem lại ảnh đã lưu)</h2>
    <div class="gallery">
        {% if images %}
            {% for img in images %}
                <a href="/static/{{ img }}" target="_blank">
                    <img src="/static/{{ img }}" alt="{{ img }}">
                </a>
            {% endfor %}
        {% else %}
            <p>Chưa có ảnh nào được lưu.</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    """Trang chính hiển thị live snapshot và playback."""
    # Lấy danh sách ảnh thực sự tồn tại (tránh lỗi file chưa ghi xong)
    images = [
        os.path.basename(f)
        for f in glob.glob(os.path.join(SAVE_DIR, "*.jpg"))
        if os.path.exists(f) and os.path.getsize(f) > 0
    ]
    # Sắp xếp mới nhất lên đầu
    images.sort(key=lambda x: os.path.getmtime(os.path.join(SAVE_DIR, x)), reverse=True)
    return render_template_string(HTML_PAGE, images=images)

@app.route("/snapshot")
def snapshot():
    """Chụp ảnh từ camera, lưu, và trả về ảnh trực tiếp."""
    ret, frame = cap.read()
    if not ret:
        return "❌ Không đọc được frame từ camera", 500

    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return "❌ Không encode được frame", 500

    # --- Lưu ảnh ra file ---
    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
    filepath = os.path.join(SAVE_DIR, filename)
    cv2.imwrite(filepath, frame)
    time.sleep(0.2)  # ⏳ Chờ 200ms để chắc chắn file được ghi hoàn tất
    print(f"💾 Đã lưu ảnh: {filepath}")

    # --- Xóa ảnh cũ ---
    cleanup_old_images()

    # --- Trả ảnh về trình duyệt ---
    return Response(buffer.tobytes(), mimetype='image/jpeg')

if __name__ == "__main__":
    try:
        app.run(host="127.0.0.1", port=5000, debug=False)
    finally:
        cleanup()
