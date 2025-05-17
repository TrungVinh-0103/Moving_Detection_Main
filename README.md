# Moving_Detection_Main

## Giới thiệu
Dự án Moving_Detection_Main là phần mềm phát hiện chuyển động và nhận diện đối tượng sử dụng OpenCV và YOLOv8. Ứng dụng có giao diện Tkinter thân thiện, hỗ trợ mở camera, tải video, ghi/xem/xóa video, chụp ảnh nhanh (snapshot), và reset nền. Các video được lưu dưới định dạng `.avi` (codec `mp4v`), ảnh snapshot lưu dưới dạng `.jpg`.

### Tính năng chính
- Phát hiện chuyển động: Vẽ khung xanh quanh vùng chuyển động (ngưỡng `min_contour_area: 500`).
- Nhận diện đối tượng: Sử dụng YOLOv8 để vẽ khung vàng và nhãn (ví dụ: "person").
- Giao diện Tkinter: Cửa sổ 800x600, nền `#1246b5`, canvas chính 640x480, snapshot 160x120.
- Nút điều khiển:
  - Open Camera (`#00cc00`): Mở camera, lật khung, ghi video/snapshot khi có chuyển động.
  - Upload Video (`#1e90ff`): Tải và phát video `.avi`.
  - Reset Background (`#ffaa00`): Đặt lại nền để cải thiện phát hiện.
  - Stop (`#ff3333`): Dừng camera/video.
  - View Video (`#4b0082`): Phát video từ thư mục `data/output/`.
  - Delete Video (`#dc143c`): Xóa video với xác nhận, đã sửa lỗi `NoneType`.
- Lưu trữ: Video `.avi` và ảnh `.jpg` lưu trong `data/output/`.
- Logging: Ghi log hoạt động/lỗi vào `logs/`.

## Cấu trúc dự án

Moving_Detection_Main/
├── config/
│   └── settings.yaml           # Cấu hình nguồn video, ngưỡng, thư mục
├── data/
│   └── output/                 # Lưu video `.avi` và ảnh `.jpg`
├── icons/
│   ├── camera.png              # Icon cho nút Open Camera
│   ├── delete.png              # Icon cho nút Delete Video
│   ├── play.png                # Icon cho nút View Video
│   ├── reset.png               # Icon cho nút Reset Background
│   ├── security_camera.png     # Icon cửa sổ ứng dụng
│   ├── stop.png                # Icon cho nút Stop
│   └── upload.png              # Icon cho nút Upload Video
├── logs/                       # Lưu file log
├── src/
│   ├── __init__.py             # Đánh dấu package
│   ├── detector.py             # Xử lý chuyển động và YOLOv8
│   ├── main.py                 # Giao diện Tkinter và điều phối
│   └── utils.py                # Hàm tiện ích (đọc config, ghi video, log)
├── requirements.txt            # Danh sách thư viện
├── README.txt                  # File này


## Yêu cầu
- Hệ điều hành: Windows/Linux/MacOS
- Python: 3.13.2 - 64bit
- Phần cứng: Webcam (cho camera) hoặc video `.avi` (codec `mp4v`)

## Cài đặt
1. Clone dự án:
   bash
   git clone https://github.com/TrungVinh-0103/Moving_Detection_Main.git
   cd Moving_Detection_Main
   

2. Tạo môi trường ảo (khuyến nghị):
   bash
   python -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate     # Windows
   

3. Cài thư viện:
   bash
   pip install -r requirements.txt
   

4. Kiểm tra icon:
   - Đảm bảo thư mục `icons/` có đầy đủ 7 file `.png`.

## Cách sử dụng
1. Chạy ứng dụng:
   bash
   python src/main.py
   

2. Hướng dẫn thao tác:
   - Open Camera: Mở webcam, ghi video/snapshot khi phát hiện chuyển động.
   - Upload Video: Tải video `.avi` từ `data/` để phát, lặp lại khi kết thúc.
   - Reset Background: Cải thiện phát hiện chuyển động bằng cách đặt lại nền.
   - Stop: Dừng camera/video, giải phóng tài nguyên.
   - View Video: Chọn video `.avi` từ `data/output/` để phát.
   - Delete Video: Xóa video đang xem, cần xác nhận.

3. Kiểm tra đầu ra:
   - Video: `data/output/motion_YYYYMMDD_HHMMSS.avi`
   - Snapshot: `data/output/snapshot_YYYYMMDD_HHMMSS.jpg`
   - Log: `logs/motion_log_YYYYMMDD_HHMMSS.txt`

## Lưu ý
- Lỗi `NoneType` trong Delete Video: Đã sửa bằng cách kiểm tra `current_video_path` trong `src/main.py`.
- Codec video: Sử dụng `mp4v` để đảm bảo tương thích, không cần FFmpeg.
- YOLOv8: Tải mô hình `yolov8n.pt` tự động khi chạy lần đầu.
- Gỡ lỗi: Xem log trong `logs/` để tìm nguyên nhân lỗi.

## Tác giả
- Trung Vinh (https://github.com/TrungVinh-0103)
- Liên hệ: trungvinh01032004@gmail.com

## Giấy phép
Dự án được phát hành dưới giấy phép MIT. Xem file `LICENSE` (nếu có) để biết thêm chi tiết.

Cảm ơn bạn đã sử dụng Moving_Detection_Main!