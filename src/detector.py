import cv2
import imutils
import datetime
import logging
from ultralytics import YOLO

class MotionDetector:
    def __init__(self, config):
        self.min_area = config['detector']['min_contour_area']
        self.blur_size = config['detector']['blur_size']
        self.threshold_value = config['detector']['threshold_value']
        self.dilate_iterations = config['detector']['dilate_iterations']
        self.first_frame = None
        self.prev_frame = None
        self.yolo_model = YOLO(config['yolo']['model_path'])
        self.motion_start_time = None
        self.motion_duration_threshold = config['detector']['motion_duration_threshold']
        self.logger = logging.getLogger()
        self.last_motion_log_time = None
        # Biến theo dõi hiệu suất
        self.total_frames = 0
        self.motion_detected_frames = 0
        self.object_detections = 0
        self.confidence_threshold = 0.8  # Ngưỡng confidence để coi là đúng
        self.confidence_scores = []  # Lưu trữ confidence của các đối tượng phát hiện

    def process_frame(self, frame, frame_width):
        """Xử lý khung hình để phát hiện chuyển động."""
        self.total_frames += 1
        frame = imutils.resize(frame, width=frame_width)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)

        if self.first_frame is None:
            self.first_frame = gray
            self.prev_frame = gray
            return frame, "Normal", False, 0, []

        frame_diff = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_diff, self.threshold_value, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=self.dilate_iterations)

        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        text = "Normal"
        motion_detected = False
        object_count = 0
        yolo_results = []

        # YOLO object detection
        results = self.yolo_model(frame, conf=0.5)
        for result in results:
            for box in result.boxes:
                x, y, w, h = map(int, box.xywh[0])
                class_id = int(box.cls[0])
                class_name = self.yolo_model.names[class_id]
                confidence = box.conf.item()
                self.confidence_scores.append(confidence)  # Lưu confidence để tính sau
                yolo_results.append((class_name, (x - w//2, y - h//2, w, h)))
                self.logger.info(f"Object detected: {class_name}, confidence: {confidence:.2f}")
                self.object_detections += 1
                cv2.rectangle(frame, (x - w//2, y - h//2), (x + w//2, y + h//2), (0, 255, 255), 2)
                cv2.putText(frame, f"{class_name} {confidence:.2f}", (x - w//2, y - h//2 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                object_count += 1
        # Debug: Ghi log realtime
        self.logger.debug(f"Frame {self.total_frames}: Objects detected = {self.object_detections}, Motion frames = {self.motion_detected_frames}")

        current_time = datetime.datetime.now().timestamp()
        for c in cnts:
            if cv2.contourArea(c) < self.min_area:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            motion_detected = True
            if self.motion_start_time is None:
                self.motion_start_time = current_time

        # Kiểm tra thời gian chuyển động
        if motion_detected and self.motion_start_time is not None:
            motion_duration = current_time - self.motion_start_time
            if motion_duration >= self.motion_duration_threshold:
                text = "Moving Object detected"
                self.motion_detected_frames += 1
                if self.last_motion_log_time is None or (current_time - self.last_motion_log_time) >= 1.0:
                    self.logger.info(f"Motion detected at timestamp {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    self.last_motion_log_time = current_time
            else:
                motion_detected = False
        else:
            self.motion_start_time = None
            self.last_motion_log_time = None

        self.prev_frame = gray.copy()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, text, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, f"Objects: {object_count}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return frame, text, motion_detected, object_count, yolo_results

    def reset_background(self):
        """Reset nền để update lại."""
        self.first_frame = None
        self.prev_frame = None
        self.logger.info("Background reset")

    def get_metrics(self):
        """Trả về các chỉ số hiệu suất dựa trên phát hiện."""
        tp = self.motion_detected_frames  # Số khung phát hiện chuyển động
        fp_fn = self.total_frames - tp  # Ước lượng số khung sai
        accuracy = tp / self.total_frames if self.total_frames > 0 else 0.0  # Accuracy dựa trên phát hiện
        object_correct = sum(1 for conf in self.confidence_scores if conf >= self.confidence_threshold)  # Tính dựa trên confidence đã lưu
        object_incorrect = self.object_detections - object_correct
        precision = object_correct / self.object_detections if self.object_detections > 0 else 0.0
        recall = object_correct / (object_correct + object_incorrect) if (object_correct + object_incorrect) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return {
            "total_frames": self.total_frames,
            "tp": tp,
            "fp_fn": fp_fn,
            "accuracy": accuracy,
            "object_correct": object_correct,
            "object_incorrect": object_incorrect,
            "f1_score": f1_score
        }
        