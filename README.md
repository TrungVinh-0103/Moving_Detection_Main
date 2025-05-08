Moving Object Detection
Phần mềm phát hiện chuyển động sử dụng OpenCV và YOLO với giao diện Tkinter, hỗ trợ camera thời gian thực và video định dạng .avi. Phần mềm hiển thị chuyển động bằng khung xanh, nhận diện đối tượng bằng YOLO (khung vàng), lưu video và ảnh chụp, đồng thời cho phép xem và xóa video đã ghi.
Yêu cầu

Python: 3.8 trở lên (khuyến nghị 3.13.2).
Thư viện: Cài đặt từ requirements.txt:
opencv-python, numpy, pyyaml, imutils, pillow, ultralytics.


Mô hình YOLOv8: Tải yolov8n.pt (tự động tải khi chạy lần đầu với ultralytics).
Icon (.png): Trong thư mục icons/ (kích thước 24x24 px, trừ security_camera.png 64x64 px):
camera.png: Icon camera.
upload.png: Icon upload.
reset.png: Icon reset/reload.
stop.png: Icon stop.
play.png: Icon play (cho nút View Video).
delete.png: Icon delete (cho nút Delete Video).
security_camera.png: Icon cửa sổ.


Webcam: Đảm bảo hoạt động nếu dùng camera.
Video: Định dạng .avi (codec mp4v) trong thư mục data/ hoặc data/output/.

Lưu ý: Không yêu cầu FFmpeg. Phần mềm sử dụng codec mp4v để ghi và đọc video .avi, tương thích với OpenCV mặc định.
Cài đặt

Clone repository:
git clone https://github.com/TrungVinh-0103/Moving_Detection_Main.git
cd Moving_Detection_Main


Cài đặt thư viện:
pip install -r requirements.txt


Tạo thư mục icons/ và tải icon:

Tải icon (24x24 px, trừ security_camera.png 64x64 px) từ IconArchive hoặc Flaticon.

Đặt vào Moving_Detection_Main/icons/:
icons/camera.png
icons/upload.png
icons/reset.png
icons/stop.png
icons/play.png
icons/delete.png
icons/security_camera.png


Nếu thiếu icon, bỏ dòng tải icon trong src/main.py (liên quan self.icons và image=...).



Chuẩn bị video:

Đặt video .avi (codec mp4v) vào data/ hoặc data/output/.

Kiểm tra video:
python -c "import cv2; cap = cv2.VideoCapture('data/output/motion_*.avi'); print(cap.isOpened())"


Kết quả True: Video hợp lệ.
Kết quả False: Tạo video mới bằng tính năng Open Camera hoặc convert video (xem phần Lưu ý).




Đảm bảo webcam:

Kiểm tra webcam:
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened()); cap.release()"


Kết quả True: Webcam hoạt động.





Cách chạy
python src/main.py


Windows (PowerShell):
cd Moving_Detection_Main
python src\main.py


VSCode:

Mở thư mục Moving_Detection_Main.
Chọn Python 3.8+ (khuyến nghị 3.13.2) qua Ctrl + Shift + P > Python: Select Interpreter.
Mở src/main.py, nhấn F5.



Cấu hình
Chỉnh sửa config/settings.yaml:

video.source: "video" (từ file) hoặc "camera" (webcam).
video.input_path: Đường dẫn video mặc định (ví dụ: data/test.avi).
video.camera_id: ID camera (thường là 0 hoặc 1).
video.fps: FPS mặc định cho camera (ví dụ: 30); video dùng FPS gốc.
video.frame_width: Chiều rộng khung hình (mặc định 640).
video.output_dir: Thư mục lưu video và ảnh (mặc định data/output/).
detector.min_contour_area: Diện tích tối thiểu để phát hiện chuyển động (ví dụ: 500).
detector.motion_duration_threshold: Thời gian tối thiểu để lưu video (giây, ví dụ: 5).
yolo.model_path: Đường dẫn mô hình YOLO (mặc định yolov8n.pt).
log.log_dir: Thư mục lưu log (mặc định logs/).

Ví dụ:
video:
  source: camera
  camera_id: 0
  fps: 30
  frame_width: 640
  output_dir: data/output/
detector:
  min_contour_area: 500
  motion_duration_threshold: 5
yolo:
  model_path: yolov8n.pt
log:
  log_dir: logs/

Giao diện

Tiêu đề: Icon security_camera.png (64x64 px), font Arial 16 bold.
Box hiển thị: Feed camera/video (640x480 px, border trắng 3px, nền đen).
Ảnh chụp: Snapshot mới nhất (160x120 px, border trắng 3px, nền đen).
Nút (bo góc, font Arial 10 bold, icon 24x24 px):
Open Camera: Mở webcam (xanh lá #00cc00, icon camera.png).
Upload Video: Chọn video .avi (xanh dương #1e90ff, icon upload.png).
Reset Background: Cập nhật nền phát hiện chuyển động (vàng #ffaa00, icon reset.png).
Stop: Dừng xử lý hoặc phát video (đỏ #ff3333, icon stop.png).
View Video: Xem video .avi từ data/output/ (tím #4b0082, icon play.png).
Delete Video: Xóa video đang xem (đỏ #dc143c, icon delete.png).


Trạng thái: Hiển thị trạng thái (Idle, Viewing, Processing), số đối tượng, kết quả YOLO (font Arial 12, border trắng, bo góc).
FPS: Hiển thị FPS thực tế (font Arial 12, border trắng, bo góc).
Màu nền: Xanh dương đậm (#1246b5).

Tính năng

Open Camera: Mở webcam, hiển thị feed thời gian thực, lật khung hình ngang, ghi video .avi (codec mp4v) khi phát hiện chuyển động (>5 giây).
Upload Video: Tải video .avi (codec mp4v) từ data/, hiển thị và xử lý liên tục đến khi nhấn Stop.
View Video: Phát video .avi từ data/output/ trong canvas (640x480 px), bật nút Delete Video khi video hợp lệ.
Delete Video: Xóa video đang xem, với xác nhận (Yes/No), dừng phát và xóa file khỏi data/output/.
Reset Background: Cập nhật nền để cải thiện phát hiện chuyển động.
Stop: Dừng camera, video upload, hoặc video đang xem; reset canvas và trạng thái.
Phát hiện chuyển động: Hiển thị khung xanh quanh vùng chuyển động (diện tích > min_contour_area).
Nhận diện YOLO: Hiển thị khung vàng và nhãn (như "person") cho đối tượng được YOLO nhận diện.
Lưu kết quả:
Video .avi (codec mp4v, FPS gốc) trong data/output/motion_YYYYMMDD_HHMMSS.avi.
Ảnh chụp .jpg khi phát hiện chuyển động, lưu trong data/output/snapshot_YYYYMMDD_HHMMSS.jpg.


Log: Ghi log hoạt động và lỗi vào logs/motion_log_YYYYMMDD_HHMMSS.txt.

Kết quả

Video đầu ra: data/output/motion_YYYYMMDD_HHMMSS.avi (codec mp4v, FPS gốc, ghi khi chuyển động >5 giây).
Ảnh chụp: data/output/snapshot_YYYYMMDD_HHMMSS.jpg (160x120 px, chụp khi phát hiện chuyển động).
Log: logs/motion_log_YYYYMMDD_HHMMSS.txt (chi tiết hoạt động, lỗi, FPS).

Lưu ý

Video không chạy:

Kiểm tra video .avi:
python -c "import cv2; cap = cv2.VideoCapture('data/output/motion_*.avi'); print(cap.isOpened())"


Nếu False, video có thể dùng codec không tương thích (như XVID). Tạo video mới:

Chạy Open Camera, chờ 10-20 giây, nhấn Stop để tạo motion_*.avi (codec mp4v).


Hoặc convert video (nếu có FFmpeg):
ffmpeg -i data/input.avi -c:v mp4v -c:a aac data/output/converted.avi




Đảm bảo OpenCV cài đúng:
pip show opencv-python




Lỗi "Không thể xóa video: remove: path should be string, bytes or os.PathLike, not NoneType":

Đã sửa trong src/main.py:
Đồng bộ trạng thái current_video_path và viewing_video.
Nút Delete Video chỉ bật khi video .avi được mở thành công.


Kiểm tra:
Nhấn View Video, chọn motion_*.avi.
Video phát, nút Delete Video bật.
Nhấn Delete Video, xác nhận Yes: Video xóa, canvas trống, thông báo "Video đã được xóa."
Nếu nhấn Delete Video khi chưa xem video, thấy cảnh báo: "Không có video nào đang được chọn để xóa."




Thiếu icon:

Nếu thiếu file trong icons/, bỏ dòng tải icon trong src/main.py:
self.icons = {...}
image=self.icons[...]


Hoặc tải icon từ Flaticon.



Kiểm tra FPS video:

Mở video bằng VLC, nhấn Ctrl+J để xem FPS.

Hoặc dùng Python:
python -c "import cv2; cap = cv2.VideoCapture('data/output/motion_*.avi'); print(cap.get(cv2.CAP_PROP_FPS)); cap.release()"




Quyền truy cập file:

Nếu lỗi xóa video (do quyền), kiểm tra:
icacls data\output


Cấp quyền:
icacls data\output /grant Users:F




Log lỗi:

Xem log trong logs/motion_log_*.txt:
cat logs/motion_log_*.txt


Tìm "Lỗi khi phát video" hoặc "Lỗi khi xóa video" để xử lý.