import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import time
from src.utils import load_config, setup_logger, get_output_writer, initialize_capture
from src.detector import MotionDetector

class MotionDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Moving Detection Software")
        self.root.configure(bg="#1246b5")  # Nền xanh dương đậm

        # Căn giữa cửa sổ trên màn hình
        window_width = 900  # Ước lượng chiều rộng cửa sổ
        window_height = 610  # Ước lượng chiều cao cửa sổ
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Khởi tạo logger trước
        self.config = load_config("config/settings.yaml")
        self.logger = setup_logger(self.config['log']['log_dir'])

        # Đặt icon cửa sổ
        try:
            self.root.iconphoto(True, tk.PhotoImage(file="icons/cctv-camera.png"))
        except Exception as e:
            print(f"Không thể tải icon cửa sổ: {str(e)}")
            self.logger.error(f"Không thể tải icon cửa sổ: {str(e)}")

        self.cap = None
        self.out = None
        self.detector = None
        self.running = False
        self.motion_detected = False
        self.frame_width = self.config['video']['frame_width']
        self.frame_height = None
        self.motion_start_time = None
        self.latest_snapshot = None
        self.source_fps = self.config['video']['fps']  # FPS mặc định
        self.frame_counter = 0  # Đếm số khung hình ghi

        # Tải icon nút
        self.icons = {
            "open_camera": self.load_icon("icons/camera.png", (24, 24)),
            "upload_video": self.load_icon("icons/upload.png", (24, 24)),
            "reset_background": self.load_icon("icons/reset.png", (24, 24)),
            "stop": self.load_icon("icons/stop.png", (24, 24))
        }

        # Style cho nút
        style = ttk.Style()
        style.configure("Rounded.TFrame", background="#1246b5")
        style.configure("Rounded.TLabel", background="#1246b5", foreground="white", font=("Arial", 12), borderwidth=2, relief="solid")
        style.configure("Camera.TButton", background="#00cc00", foreground="black", font=("Arial", 10, "bold"), borderwidth=3, relief="flat")
        style.map("Camera.TButton", background=[('active', '#00e600'), ('disabled', '#cccccc')], foreground=[('active', 'black')])
        style.configure("Upload.TButton", background="#1e90ff", foreground="black", font=("Arial", 10, "bold"), borderwidth=3, relief="flat")
        style.map("Upload.TButton", background=[('active', '#4aa8ff'), ('disabled', '#cccccc')], foreground=[('active', 'black')])
        style.configure("Reset.TButton", background="#ffaa00", foreground="black", font=("Arial", 10, "bold"), borderwidth=3, relief="flat")
        style.map("Reset.TButton", background=[('active', '#ffbb33'), ('disabled', '#cccccc')], foreground=[('active', 'black')])
        style.configure("Stop.TButton", background="#ff3333", foreground="black", font=("Arial", 10, "bold"), borderwidth=3, relief="flat")
        style.map("Stop.TButton", background=[('active', '#ff6666'), ('disabled', '#cccccc')], foreground=[('active', 'black')])

        # Main frame
        self.main_frame = ttk.Frame(root, style="Rounded.TFrame")
        self.main_frame.pack(padx=10, pady=10)

        # Video canvas
        self.canvas = tk.Canvas(self.main_frame, width=640, height=480, bg="black", highlightthickness=3, highlightbackground="#ffffff")
        self.canvas.pack(side=tk.LEFT, padx=5)

        # Snapshot frame
        self.snapshot_frame = ttk.Frame(self.main_frame, style="Rounded.TFrame")
        self.snapshot_frame.pack(side=tk.RIGHT, padx=10)
        self.snapshot_label = ttk.Label(self.snapshot_frame, text="Latest Snapshot", style="Rounded.TLabel")
        self.snapshot_label.pack()
        self.snapshot_canvas = tk.Canvas(self.snapshot_frame, width=160, height=120, bg="black", highlightthickness=3, highlightbackground="#ffffff")
        self.snapshot_canvas.pack()

        # Status and FPS labels
        self.status_label = ttk.Label(root, text="Status: Idle", style="Rounded.TLabel")
        self.status_label.pack(pady=5)
        self.fps_label = ttk.Label(root, text="FPS: 0.00", style="Rounded.TLabel")
        self.fps_label.pack()

        # Button frame
        self.button_frame = ttk.Frame(root, style="Rounded.TFrame")
        self.button_frame.pack(pady=10)

        # Buttons
        self.open_camera_btn = ttk.Button(
            self.button_frame, text=" Open Camera", image=self.icons["open_camera"], compound=tk.LEFT,
            command=self.open_camera, style="Camera.TButton"
        )
        self.open_camera_btn.pack(side=tk.LEFT, padx=5)

        self.upload_video_btn = ttk.Button(
            self.button_frame, text=" Upload Video", image=self.icons["upload_video"], compound=tk.LEFT,
            command=self.upload_video, style="Upload.TButton"
        )
        self.upload_video_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = ttk.Button(
            self.button_frame, text=" Reset Background", image=self.icons["reset_background"], compound=tk.LEFT,
            command=self.reset_background, style="Reset.TButton", state=tk.DISABLED
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            self.button_frame, text=" Stop", image=self.icons["stop"], compound=tk.LEFT,
            command=self.stop, style="Stop.TButton", state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.start_time = time.time()
        self.frame_count = 0
        self.last_frame_time = None

    def load_icon(self, path, size):
        """Tải và resize icon."""
        try:
            img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            self.logger.error(f"Không thể tải icon {path}: {str(e)}")
            return None

    def open_camera(self):
        if not self.running:
            self.config['video']['source'] = 'camera'
            self.start_processing()

    def upload_video(self):
        if not self.running:
            file_path = filedialog.askopenfilename(
                initialdir="data/",
                filetypes=[
                    ("Video files", "*.mp4 *.avi *.wmv *.mkv *.vob *.flv"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                self.config['video']['source'] = 'video'
                try:
                    self.logger.info(f"Đang thử upload video: {file_path}")
                    self.start_processing(video_path=file_path)
                    messagebox.showinfo("Success", f"Video {os.path.basename(file_path)} loaded successfully!")
                except ValueError as e:
                    error_msg = str(e)
                    self.logger.error(f"Lỗi khi upload video {file_path}: {error_msg}")
                    messagebox.showerror("Error", f"{error_msg}\nĐảm bảo video hợp lệ và FFmpeg được cài đặt.")
                except Exception as e:
                    error_msg = f"Lỗi không xác định: {str(e)}"
                    self.logger.error(f"Lỗi không xác định khi upload video {file_path}: {error_msg}")
                    messagebox.showerror("Error", f"{error_msg}\nVui lòng kiểm tra file video hoặc liên hệ hỗ trợ.")

    def reset_background(self):
        if self.detector:
            self.detector.reset_background()
            self.logger.info("Background reset")

    def start_processing(self, video_path=None):
        try:
            self.cap, source_info, self.source_fps = initialize_capture(self.config, video_path)
            if not self.cap.isOpened():
                raise ValueError("Không thể khởi tạo nguồn video: đối tượng VideoCapture không mở.")
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * self.frame_width / self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.detector = MotionDetector(self.config)
            self.running = True
            self.frame_counter = 0  # Reset bộ đếm khung hình
            self.open_camera_btn.config(state='disabled')
            self.upload_video_btn.config(state='disabled')
            self.reset_btn.config(state='normal')
            self.stop_btn.config(state='normal')
            self.logger.info("Started processing: %s, FPS: %.2f", source_info, self.source_fps)
            self.status_label.config(text=f"Status: {source_info}")

            # Khởi tạo VideoWriter cho camera
            if self.config['video']['source'] == 'camera':
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                self.out, output_path = get_output_writer(self.config, self.frame_height, timestamp, self.source_fps)
                self.logger.info("Bắt đầu ghi video camera: %s, FPS: %.2f", output_path, self.source_fps)

            self.last_frame_time = time.time()
            self.process_frames()
        except ValueError as e:
            self.logger.error(str(e))
            self.status_label.config(text=f"Error: {str(e)}")
            raise
        except Exception as e:
            error_msg = f"Lỗi khởi tạo video: {str(e)}"
            self.logger.error(error_msg)
            self.status_label.config(text=f"Error: {error_msg}")
            raise

    def process_frames(self):
        if not self.running or not self.cap or not self.cap.isOpened():
            self.logger.warning("Dừng xử lý khung hình: running=%s, cap=%s, cap.isOpened=%s",
                               self.running, self.cap is not None, self.cap.isOpened() if self.cap else False)
            return

        start_time = time.time()

        ret, frame = self.cap.read()
        if not ret or frame is None:
            if self.config['video']['source'] == 'video':
                self.logger.info("Video hết, quay lại đầu video")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.logger.error("Không thể quay lại đầu video")
                    return
            else:
                self.logger.warning("Không đọc được khung hình từ camera")
                return

        if self.config['video']['source'] == 'camera':
            frame = cv2.flip(frame, 1)

        try:
            processed_frame, text, motion_detected_now, object_count, yolo_results = self.detector.process_frame(frame, self.frame_width)
        except Exception as e:
            self.logger.error(f"Lỗi khi xử lý khung hình: {str(e)}")
            return

        # Ghi tất cả khung hình khi VideoWriter tồn tại
        if self.out is not None:
            self.out.write(processed_frame)
            self.frame_counter += 1

        # Lưu snapshot khi có chuyển động
        if motion_detected_now:
            if self.motion_start_time is None:
                self.motion_start_time = time.time()
            snapshot_path = os.path.join(self.config['video']['output_dir'], f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
            cv2.imwrite(snapshot_path, processed_frame)
            self.logger.info("Lưu ảnh chụp: %s", snapshot_path)
            self.update_snapshot(snapshot_path)
        else:
            self.motion_start_time = None

        try:
            frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.image = img
        except Exception as e:
            self.logger.error(f"Lỗi hiển thị khung hình lên canvas: {str(e)}")
            return

        yolo_text = ", ".join([name for name, _ in yolo_results]) if yolo_results else "None"
        self.status_label.config(text=f"Status: {text}, Objects: {object_count}, YOLO: {yolo_text}")
        self.frame_count += 1
        if self.frame_count % 10 == 0:
            elapsed = time.time() - self.start_time
            fps = self.frame_count / elapsed
            self.fps_label.config(text=f"FPS: {fps:.2f}")

        processing_time = (time.time() - start_time) * 1000
        target_delay = max(1, int(1000 / self.source_fps))
        adjusted_delay = max(1, int(target_delay - processing_time))
        self.logger.debug(f"Processing time: {processing_time:.2f}ms, Target delay: {target_delay:.2f}ms, Adjusted delay: {adjusted_delay:.2f}ms")

        if self.running:
            self.root.after(adjusted_delay, self.process_frames)

    def update_snapshot(self, snapshot_path):
        """Hiển thị ảnh chụp mới nhất."""
        try:
            img = Image.open(snapshot_path)
            img = img.resize((160, 120), Image.Resampling.LANCZOS)
            self.latest_snapshot = ImageTk.PhotoImage(img)
            self.snapshot_canvas.create_image(0, 0, anchor=tk.NW, image=self.latest_snapshot)
        except Exception as e:
            self.logger.error("Không thể hiển thị ảnh chụp: %s", str(e))

    def stop(self):
        self.running = False
        if self.out is not None:
            self.logger.info(f"Đã ghi {self.frame_counter} khung hình vào video")
            self.out.release()
            self.out = None
            self.frame_counter = 0
            self.logger.info("Đã dừng ghi video bởi người dùng")
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.canvas.delete("all")
        self.snapshot_canvas.delete("all")
        self.status_label.config(text="Status: Idle")
        self.fps_label.config(text="FPS: 0.00")
        self.open_camera_btn.config(state='normal')
        self.upload_video_btn.config(state='normal')
        self.reset_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        self.motion_start_time = None
        self.logger.info("Đã dừng xử lý bởi người dùng")

    def on_closing(self):
        self.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MotionDetectionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()