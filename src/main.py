import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import time
import tkinter.font as tkFont
from src.utils import load_config, setup_logger, get_output_writer, initialize_capture
from src.detector import MotionDetector

class MotionDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Moving Detection Software")
        self.root.configure(bg="#1246b5")

        bold_font = tkFont.Font(family="Arial", size=16, weight="bold")
        self.root.option_add("*Toplevel*TitleFont", bold_font)

        window_width = 900
        window_height = 615
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.config = load_config("config/settings.yaml")
        self.logger = setup_logger(self.config['log']['log_dir'])

        try:
            icon = tk.PhotoImage(file="icons/cctv-camera.png")
            self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"Không thể tải icon cửa sổ: {str(e)}")
            self.logger.error(f"Không thể tải icon cửa sổ: {str(e)}")

        self.cap = None
        self.out = None
        self.detector = None
        self.running = False
        self.viewing_video = False
        self.motion_detected = False
        self.frame_width = self.config['video']['frame_width']
        self.frame_height = None
        self.motion_start_time = None
        self.latest_snapshot = None
        self.source_fps = self.config['video']['fps']
        self.frame_counter = 0
        self.current_video_path = None
        self.start_time = time.time()
        self.frame_count = 0

        self.icons = {
            "open_camera": self.load_icon("icons/camera.png", (24, 24)),
            "upload_video": self.load_icon("icons/upload.png", (24, 24)),
            "reset_background": self.load_icon("icons/reset.png", (24, 24)),
            "stop": self.load_icon("icons/stop.png", (24, 24)),
            "view_video": self.load_icon("icons/play.png", (24, 24)),
        }

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
        style.configure("View.TButton", background="#4b0082", foreground="black", font=("Arial", 10, "bold"), borderwidth=3, relief="flat")
        style.map("View.TButton", background=[('active', '#6a0dad'), ('disabled', '#cccccc')], foreground=[('active', 'black')])

        self.main_frame = ttk.Frame(root, style="Rounded.TFrame")
        self.main_frame.pack(padx=10, pady=10)

        self.canvas = tk.Canvas(self.main_frame, width=640, height=480, bg="black", highlightthickness=3, highlightbackground="#ffffff")
        self.canvas.pack(side=tk.LEFT, padx=5)

        self.snapshot_frame = ttk.Frame(self.main_frame, style="Rounded.TFrame")
        self.snapshot_frame.pack(side=tk.RIGHT, padx=10)
        self.snapshot_label = ttk.Label(self.snapshot_frame, text="Latest Snapshot", style="Rounded.TLabel")
        self.snapshot_label.pack()
        self.snapshot_canvas = tk.Canvas(self.snapshot_frame, width=160, height=120, bg="black", highlightthickness=3, highlightbackground="#ffffff")
        self.snapshot_canvas.pack()

        self.status_label = ttk.Label(root, text="Status: Idle", style="Rounded.TLabel")
        self.status_label.pack(pady=5)
        self.fps_label = ttk.Label(root, text="FPS: 0.00", style="Rounded.TLabel")
        self.fps_label.pack()

        self.button_frame = ttk.Frame(root, style="Rounded.TFrame")
        self.button_frame.pack(pady=10)

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

        self.view_btn = ttk.Button(
            self.button_frame, text=" View Video", image=self.icons["view_video"], compound=tk.LEFT,
            command=self.view_video, style="View.TButton"
        )
        self.view_btn.pack(side=tk.LEFT, padx=5)

    def load_icon(self, path, size):
        try:
            # Sử dụng named expression để tối ưu (Sourcery: dòng 145-146)
            if not (img := Image.open(path).resize(size, Image.Resampling.LANCZOS)):
                return None
            return ImageTk.PhotoImage(img)
        except Exception as e:
            self.logger.error(f"Không thể tải icon {path}: {str(e)}")
            return None

    def view_video(self):
        if self.running or self.viewing_video:
            messagebox.showwarning("Warning", "Đang xử lý hoặc xem video khác. Vui lòng dừng trước!")
            return

        file_path = filedialog.askopenfilename(
            initialdir="data/output",
            filetypes=[("Video files", "*.avi"), ("All files", "*.*")]
        )
        if not file_path:  # Hoist điều kiện ra ngoài (Sourcery: dòng 195-196)
            return

        try:
            if not os.path.exists(file_path):
                raise ValueError("File video không tồn tại.")
            self.cap = cv2.VideoCapture(file_path)
            if not self.cap.isOpened():
                raise ValueError("Không thể mở video. Đảm bảo file .avi dùng codec mp4v.")
            ret, frame = self.cap.read()
            if not ret or frame is None:
                raise ValueError("Không thể đọc khung hình từ video.")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_video_path = file_path
            self.source_fps = self.cap.get(cv2.CAP_PROP_FPS) or self.config['video']['fps']
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * self.frame_width / self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.viewing_video = True
            self.open_camera_btn.config(state='disabled')
            self.upload_video_btn.config(state='disabled')
            self.view_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text=f"Status: Viewing {os.path.basename(file_path)}")
            self.logger.info(f"Đang phát video: {file_path}, FPS: {self.source_fps}")
            self.play_video()
        except Exception as e:
            self.logger.error(f"Lỗi khi phát video {file_path}: {str(e)}")
            messagebox.showerror("Error", f"Không thể phát video: {str(e)}")
            if self.cap:
                self.cap.release()
            self.cap = None
            self.current_video_path = None
            self.viewing_video = False
            self.stop_btn.config(state='disabled')
            self.status_label.config(text="Status: Idle")

    def play_video(self):
        # Sử dụng guard clause và named expression (Sourcery: dòng 229-230)
        if not (self.viewing_video and self.cap and self.cap.isOpened()):
            self.logger.warning("Dừng phát video: viewing=%s, cap=%s, cap.isOpened=%s",
                               self.viewing_video, self.cap is not None, self.cap.isOpened() if self.cap else False)
            self.stop()
            return

        start_time = time.time()
        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.logger.info("Video kết thúc, quay lại đầu")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.logger.error("Không thể quay lại đầu video")
                self.stop()
                return

        try:
            frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.image = img
        except Exception as e:
            self.logger.error(f"Lỗi hiển thị khung hình video: {str(e)}")
            self.stop()
            return

        self.frame_count += 1
        if self.frame_count % 10 == 0:
            elapsed = time.time() - self.start_time
            fps = self.frame_count / elapsed
            self.fps_label.config(text=f"FPS: {fps:.2f}")

        processing_time = (time.time() - start_time) * 1000
        target_delay = max(1, int(1000 / self.source_fps))
        adjusted_delay = max(1, int(target_delay - processing_time))
        if self.viewing_video:
            self.root.after(adjusted_delay, self.play_video)

    def open_camera(self):
        if not self.running and not self.viewing_video:
            self.config['video']['source'] = 'camera'
            self.start_processing()

    def upload_video(self):
        if not self.running and not self.viewing_video:
            file_path = filedialog.askopenfilename(
                initialdir="data/",
                filetypes=[("Video files", "*.avi"), ("All files", "*.*")]
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
                    messagebox.showerror("Error", f"{error_msg}\nĐảm bảo video .avi dùng codec mp4v.")
                except Exception as e:
                    error_msg = f"Lỗi không xác định: {str(e)}"
                    self.logger.error(f"Lỗi không xác định khi upload video {file_path}: {error_msg}")
                    messagebox.showerror("Error", f"{error_msg}\nVui lòng kiểm tra file video.")

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
            self.frame_counter = 0
            self.open_camera_btn.config(state='disabled')
            self.upload_video_btn.config(state='disabled')
            self.view_btn.config(state='disabled')
            self.reset_btn.config(state='normal')
            self.stop_btn.config(state='normal')
            self.logger.info("Started processing: %s, FPS: %.2f", source_info, self.source_fps)
            self.status_label.config(text=f"Status: {source_info}")

            if self.config['video']['source'] == 'camera':
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                self.out, output_path = get_output_writer(self.config, self.frame_height, timestamp, self.source_fps)
                self.logger.info("Bắt đầu ghi video camera: %s, FPS: %.2f", output_path, self.source_fps)

            self.start_time = time.time()
            self.frame_count = 0
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

        if self.out is not None:
            self.out.write(processed_frame)
            self.frame_counter += 1

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
        try:
            img = Image.open(snapshot_path)
            img = img.resize((160, 120), Image.Resampling.LANCZOS)
            self.latest_snapshot = ImageTk.PhotoImage(img)
            self.snapshot_canvas.create_image(0, 0, anchor=tk.NW, image=self.latest_snapshot)
        except Exception as e:
            self.logger.error("Không thể hiển thị ảnh chụp: %s", str(e))

    def stop(self):
        self.running = False
        self.viewing_video = False
        if self.out is not None:
            self.logger.info(f"Đã ghi {self.frame_counter} khung hình vào video")
            self.out.release()
            self.out = None
            self.frame_counter = 0
            self.logger.info("Đã dừng ghi video bởi người dùng")
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        # Tính và ghi FPS trung bình cùng các chỉ số hiệu suất
        if self.frame_count > 0:
            elapsed = time.time() - self.start_time
            fps = self.frame_count / elapsed
            self.logger.info(f"Average FPS: {fps:.2f}")
            if self.detector:
                metrics = self.detector.get_metrics()
                self.logger.info(f"Total frames processed: {metrics['total_frames']}")
                self.logger.info(f"Motion detection - TP: {metrics['tp']}, FP+FN: {metrics['fp_fn']}, Accuracy: {metrics['accuracy']:.2f}")
                self.logger.info(f"Object detection - Correct: {metrics['object_correct']}, Incorrect: {metrics['object_incorrect']}, F1-score: {metrics['f1_score']:.2f}")
        self.status_label.config(text="Status: Idle")
        self.fps_label.config(text="FPS: 0.00")
        self.open_camera_btn.config(state='normal')
        self.upload_video_btn.config(state='normal')
        self.view_btn.config(state='normal')
        self.reset_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')
        self.motion_start_time = None
        self.current_video_path = None
        self.logger.info("Đã dừng xử lý bởi người dùng")

    def on_closing(self):
        self.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MotionDetectionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
