import cv2
import os
import datetime
import yaml
import logging

def load_config(config_path):
    """Đọc file cấu hình YAML."""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def setup_logger(log_dir):
    """Thiết lập logger để ghi log."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"motion_log_{datetime.datetime.now().strftime('%Y%m%d')}.txt")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(message)s"
    )
    return logging.getLogger()

def get_output_writer(config, frame_height, timestamp, fps):
    """Tạo VideoWriter để ghi video định dạng AVI với FPS động."""
    output_dir = config['video']['output_dir']
    if os.path.exists(output_dir) and not os.path.isdir(output_dir):
        raise ValueError(f"Đường dẫn '{output_dir}' tồn tại nhưng không phải thư mục. Vui lòng xóa hoặc đổi tên tệp.")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"motion_{timestamp}.avi")
    # Sử dụng codec XVID
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # Đảm bảo FPS hợp lệ
    if fps <= 0 or not fps:
        fps = config['video']['fps']
        logging.getLogger().warning(f"FPS không hợp lệ, dùng FPS mặc định: {fps}")
    return cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (config['video']['frame_width'], frame_height)
    ), output_path

def initialize_capture(config, video_path=None):
    """Khởi tạo nguồn video hoặc camera, trả về FPS."""
    logger = logging.getLogger()
    if config['video']['source'] == 'video' or video_path:
        path = video_path if video_path else config['video']['input_path']
        if not os.path.exists(path):
            raise ValueError(f"File video không tồn tại: {path}")
        for backend in [cv2.CAP_ANY, cv2.CAP_FFMPEG, cv2.CAP_DSHOW]:
            cap = cv2.VideoCapture(path, backend)
            if cap.isOpened():
                logger.info(f"Đã mở video {path} với backend {backend}")
                break
        else:
            raise ValueError(
                f"Không thể mở video: {path}. Kiểm tra định dạng (.mp4, .avi, .wmv, .mkv, .vob, .flv) hoặc cài FFmpeg. "
                "Hướng dẫn: https://ffmpeg.org/download.html"
            )
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or not fps:
            fps = config['video']['fps']
            logger.warning(f"Không lấy được FPS của video {path}, dùng FPS mặc định: {fps}")
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        logger.info(f"Video codec: {codec}")
        return cap, f"Video: {os.path.basename(path)}", fps
    else:
        cap = cv2.VideoCapture(config['video']['camera_id'])
        if not cap.isOpened():
            cap = cv2.VideoCapture(1)
            if not cap.isOpened():
                raise ValueError("Không thể mở camera với ID 0 hoặc 1")
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or not fps:
            fps = config['video']['fps']
            logger.warning(f"Không lấy được FPS của camera, dùng FPS mặc định: {fps}")
        return cap, f"Camera ID: {config['video']['camera_id']}", fps