# # # Speed_Violation_Detector.py

# # import streamlit as st
# # import cv2
# # import tempfile
# # import numpy as np
# # import time
# # import pandas as pd
# # from ultralytics import YOLO
# # import easyocr
# # import os
# # import smtplib
# # from email.mime.multipart import MIMEMultipart
# # from email.mime.text import MIMEText
# # from email.mime.base import MIMEBase
# # from email import encoders
# # from PIL import Image
# # import torch

# # # Initialize EasyOCR reader
# # ocr_reader = easyocr.Reader(['en'], gpu=True)


# # def read_license_plate(frame, box):
# #     x1, y1, x2, y2 = box
# #     plate_img = frame[y1:y2, x1:x2]

# #     plate_img = cv2.resize(plate_img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
# #     plate_img = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
# #     results = ocr_reader.readtext(plate_img)
# #     if results:
# #         return results[0][1]
# #     return "Unclear"


# # def estimate_speed(prev_pos, curr_pos, time_elapsed, ppm):
# #     dx = curr_pos[0] - prev_pos[0]
# #     dy = curr_pos[1] - prev_pos[1]
# #     dist_pixels = np.sqrt(dx ** 2 + dy ** 2)
# #     dist_meters = dist_pixels / ppm
# #     speed_mps = dist_meters / time_elapsed
# #     speed_mph = speed_mps * 2.237
# #     return speed_mph


# # def send_email_with_attachment(to_email, df):
# #     try:
# #         sender_email = "your_email@example.com"
# #         sender_password = "your_email_password"
# #         smtp_server = "smtp.gmail.com"
# #         smtp_port = 587

# #         subject = "Speed Limit Violation Report"
# #         body = "Attached is the CSV file with the list of speed limit violations."
# #         msg = MIMEMultipart()
# #         msg['From'] = sender_email
# #         msg['To'] = to_email
# #         msg['Subject'] = subject
# #         msg.attach(MIMEText(body, 'plain'))

# #         attachment = MIMEBase('application', 'octet-stream')
# #         attachment.set_payload(df.to_csv(index=False).encode())
# #         encoders.encode_base64(attachment)
# #         attachment.add_header('Content-Disposition', "attachment; filename=violators.csv")
# #         msg.attach(attachment)

# #         server = smtplib.SMTP(smtp_server, smtp_port)
# #         server.starttls()
# #         server.login(sender_email, sender_password)
# #         server.sendmail(sender_email, to_email, msg.as_string())
# #         server.quit()
# #         st.success(f"Email sent successfully to {to_email}")
# #     except Exception as e:
# #         st.error(f"Error sending email: {str(e)}")


# # # --- Streamlit UI ---
# # st.set_page_config(layout="wide")
# # st.title("🚗 Speed Limit Violation Detection System")
# # st.markdown("""
# # Upload a video. The app will track cars, estimate their speeds, read their license plates, and highlight any vehicle that goes over the speed limit (default 20 mph). Red boxes = speeding. Green = under the limit.
# # """)

# # col1, col2 = st.columns([3, 2])

# # device = "cuda" if torch.cuda.is_available() else "cpu"
# # st.sidebar.markdown(f"**💻 Running on:** `{device.upper()}`")

# # model = YOLO('yolov8n.pt').to(device)
# # license_plate_detector = YOLO('yolov8n.pt').to(device)

# # ppm = 8
# # placeholder_chart = st.empty()
# # violators_data = []
# # stframe = st.empty()
# # prev_positions = {}
# # car_speeds = {}
# # speeding_car_images = []
# # speeding_cars = set()  # Track which cars are currently speeding


# # def process_frame_for_video(frame):
# #     global prev_positions, car_speeds, speeding_car_images, violators_data, speeding_cars
# #     results = model.track(frame, persist=True)
# #     license_plate_results = license_plate_detector(frame)[0]
# #     annotated_frame = frame.copy()
# #     curr_time = time.time()

# #     for lp_box in license_plate_results.boxes:
# #         x1, y1, x2, y2 = map(int, lp_box.xyxy[0])
# #         cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
# #         plate_text = read_license_plate(frame, (x1, y1, x2, y2))
# #         cv2.putText(annotated_frame, plate_text, (x1, y1 - 10),
# #                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

# #     for box in results[0].boxes:
# #         cls = int(box.cls[0])
# #         if model.names[cls] != 'car':
# #             continue

# #         x1, y1, x2, y2 = map(int, box.xyxy[0])
# #         car_id = int(box.id[0]) if box.id is not None else None
# #         center_x = (x1 + x2) // 2
# #         center_y = (y1 + y2) // 2

# #         # Default color is green (not speeding)
# #         box_color = (0, 255, 0)
# #         label_text = ""

# #         if car_id in prev_positions:
# #             prev_pos, prev_time = prev_positions[car_id]
# #             time_diff = curr_time - prev_time
# #             if time_diff > 0:  # Only calculate speed if time has passed
# #                 speed = estimate_speed(prev_pos, (center_x, center_y), time_diff, ppm)
# #                 car_speeds[car_id] = speed

# #                 if speed > speed_limit:
# #                     speeding_cars.add(car_id)  # Add to speeding cars set
# #                     box_color = (0, 0, 255)  # Red for speeding
# #                     label_text = f"Speeding: {round(speed, 1)} mph"

# #                     if car_id not in [v["Car ID"] for v in violators_data]:
# #                         plate_number = read_license_plate(frame, (x1, y1, x2, y2))
# #                         timestamp = time.strftime("%H:%M:%S", time.localtime(curr_time))

# #                         violators_data.append({
# #                             "Car ID": car_id,
# #                             "Speed (mph)": round(speed, 2),
# #                             "License Plate": plate_number,
# #                             "Timestamp": timestamp
# #                         })

# #                         car_img = frame[y1:y2, x1:x2]
# #                         if car_img.size > 0:
# #                             car_img = cv2.cvtColor(car_img, cv2.COLOR_BGR2RGB)
# #                             car_img_resized = cv2.resize(car_img, (600, 400))
# #                             speeding_car_images.append((car_id, car_img_resized, speed, timestamp))
# #                 else:
# #                     # Only remove from speeding set if speed is below threshold with some buffer
# #                     if car_id in speeding_cars and speed < speed_limit * 0.9:  # 10% buffer to avoid flickering
# #                         speeding_cars.discard(car_id)

# #             prev_positions[car_id] = ((center_x, center_y), curr_time)
# #         else:
# #             prev_positions[car_id] = ((center_x, center_y), curr_time)

# #         # If car was previously detected as speeding, keep it red
# #         if car_id in speeding_cars:
# #             box_color = (0, 0, 255)
# #             if not label_text:  # If we don't have a current speed reading, use the last known speed
# #                 last_speed = car_speeds.get(car_id, 0)
# #                 label_text = f"Speeding: {round(last_speed, 1)} mph"

# #         # Draw the bounding box and label
# #         cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)
# #         if label_text:
# #             cv2.putText(annotated_frame, label_text, (x1, y1 - 10),
# #                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

# #     if violators_data:
# #         df = pd.DataFrame(violators_data).drop_duplicates(subset='Car ID', keep='last')
# #         placeholder_chart.dataframe(df)

# #     return annotated_frame


# # # Sidebar
# # with st.sidebar:
# #     st.header("📋 Settings")
# #     use_live_cam = st.checkbox("📷 Use Live Camera")
# #     uploaded_video = None
# #     if not use_live_cam:
# #         uploaded_video = st.file_uploader("Upload a video", type=["mp4", "mov", "avi"])
# #     speed_limit = st.slider("Set Speed Limit (mph)", min_value=1, max_value=100, value=20)

# #     show_gallery = st.checkbox("📸 Show Speeding Cars Gallery")

# #     st.markdown("---")
# #     st.subheader("🛠️ Calibration Tips")
# #     st.info("""
# #     **For best OCR results, ensure plates are:**
# #     - Well-lit  
# #     - At least 100px wide  
# #     - Facing the camera
# #     """)

# #     st.markdown("---")
# #     st.subheader("📧 Send Violator Data via Email")
# #     recipient_email = st.text_input("Recipient's Email", placeholder="Enter recipient email")
# #     send_email_button = st.button("📤 Send Violator Data via Email")

# #     st.markdown("---")
# #     if st.button("🔄 Reset System"):
# #         prev_positions.clear()
# #         car_speeds.clear()
# #         speeding_car_images.clear()
# #         violators_data.clear()
# #         speeding_cars.clear()
# #         placeholder_chart.empty()
# #         stframe.empty()
# #         st.success("System reset! All data cleared.")

# # # Video Upload Mode
# # if uploaded_video is not None:
# #     tfile = tempfile.NamedTemporaryFile(delete=False)
# #     tfile.write(uploaded_video.read())
# #     cap = cv2.VideoCapture(tfile.name)

# #     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# #     output_path = os.path.join(tempfile.gettempdir(), "processed_output.mp4")
# #     fps = cap.get(cv2.CAP_PROP_FPS)
# #     width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# #     height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# #     out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# #     while cap.isOpened():
# #         ret, frame = cap.read()
# #         if not ret:
# #             break

# #         # Process the frame and get the annotated frame
# #         annotated_frame = process_frame_for_video(frame)

# #         # Write the annotated frame to the output video
# #         out.write(annotated_frame)

# #         # Display the frame in Streamlit
# #         with col1:
# #             stframe.image(annotated_frame, channels="BGR", width=800)

# #     cap.release()
# #     out.release()

# # # Live Camera Mode
# # elif use_live_cam:
# #     cam = cv2.VideoCapture(0)
# #     stop_button = st.button("❌ Stop Camera")
# #     while cam.isOpened():
# #         ret, frame = cam.read()
# #         if not ret or stop_button:
# #             break

# #         # Process the frame and get the annotated frame
# #         annotated_frame = process_frame_for_video(frame)

# #         # Display the frame in Streamlit
# #         with col1:
# #             stframe.image(annotated_frame, channels="BGR", width=800)
# #     cam.release()

# # # Summary
# # if violators_data:
# #     st.subheader("Speed Limit Violations Summary")
# #     final_df = pd.DataFrame(violators_data).drop_duplicates(subset='Car ID', keep='last')
# #     st.dataframe(final_df)

# #     csv = final_df.to_csv(index=False).encode('utf-8')
# #     st.download_button("⬇️ Download Violator Data as CSV", data=csv, file_name="violators.csv", mime="text/csv")

# #     if not use_live_cam and uploaded_video:
# #         with open(output_path, "rb") as f:
# #             video_bytes = f.read()
# #         st.download_button("⬇️ Download Processed Video", data=video_bytes,
# #                            file_name="processed_output.mp4", mime="video/mp4")

# #     if recipient_email and send_email_button:
# #         send_email_with_attachment(recipient_email, final_df)
# # else:
# #     st.success("No speed limit violations detected yet!")

# # if show_gallery:
# #     st.subheader("🚨 Speeding Cars Gallery")

# #     # Get the unique car IDs from the violators data
# #     if violators_data:
# #         # Create a dictionary to map car IDs to their latest image and info
# #         car_gallery_data = {}
# #         final_df_ids = set(final_df['Car ID'].unique())

# #         # Filter and keep only the latest image for each car in the final_df
# #         for car_id, img, speed, timestamp in speeding_car_images:
# #             if car_id in final_df_ids:
# #                 # Only keep if this is a newer timestamp than what we have
# #                 if car_id not in car_gallery_data:
# #                     car_gallery_data[car_id] = (img, speed, timestamp)
# #                 else:
# #                     existing_timestamp = car_gallery_data[car_id][2]
# #                     if timestamp > existing_timestamp:
# #                         car_gallery_data[car_id] = (img, speed, timestamp)

# #         # Ensure we have exactly the same cars as in the summary
# #         if car_gallery_data:
# #             # Create list sorted by car ID to match the summary order
# #             gallery_items = sorted([(car_id, data[0], data[1], data[2])
# #                                     for car_id, data in car_gallery_data.items()],
# #                                    key=lambda x: x[0])

# #             cols = st.columns(3)
# #             for i, (car_id, img, speed, timestamp) in enumerate(gallery_items):
# #                 with cols[i % 3]:
# #                     st.image(img, caption=f"Car {car_id}\n{round(speed, 1)} mph @ {timestamp}", width=300)
# #         else:
# #             st.warning("No speeding cars images available for the violators in the summary.")
# #     else:
# #         st.warning("No speeding cars detected yet.")


# # Speed_Violation_Detector.py — Improved Version
# # Changes from original:
# #   1. Replaced estimate_speed() with PerspectiveSpeedEstimator (Kalman filter + multi-frame averaging + spike filter)
# #   2. Speed is now stable and consistent — no more jumping numbers
# #   3. Violation check uses confidence score — avoids false positives on first frame
# #   4. Cleanup of stale vehicles every 30 frames to free memory
# #   5. FPS now read from actual video instead of hardcoded

# import streamlit as st
# import cv2
# import tempfile
# import numpy as np
# import time
# import math
# import pandas as pd
# from collections import deque
# from dataclasses import dataclass, field
# from typing import Dict, Optional
# from ultralytics import YOLO
# import easyocr
# import os
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# from PIL import Image
# import torch


# # ===========================================================================
# # IMPROVED SPEED ESTIMATOR — replaces the old estimate_speed() function
# # ===========================================================================

# class KalmanFilter1D:
#     """Smooths noisy speed readings per vehicle using a Kalman filter."""
#     def __init__(self, process_noise=1.0, measurement_noise=10.0):
#         self.q = process_noise
#         self.r = measurement_noise
#         self.x = 0.0
#         self.p = 1.0
#         self.initialized = False

#     def update(self, measurement: float) -> float:
#         if not self.initialized:
#             self.x = measurement
#             self.initialized = True
#             return self.x
#         self.p = self.p + self.q
#         k = self.p / (self.p + self.r)
#         self.x = self.x + k * (measurement - self.x)
#         self.p = (1 - k) * self.p
#         return self.x


# @dataclass
# class VehicleState:
#     positions: deque = field(default_factory=lambda: deque(maxlen=30))
#     timestamps: deque = field(default_factory=lambda: deque(maxlen=30))
#     raw_speeds: deque = field(default_factory=lambda: deque(maxlen=10))
#     kalman: KalmanFilter1D = field(default_factory=KalmanFilter1D)
#     smoothed_speed: float = 0.0
#     confidence: float = 0.0
#     last_seen: float = field(default_factory=time.time)
#     frame_count: int = 0


# class PerspectiveSpeedEstimator:
#     """
#     Improved speed estimator with:
#     - Kalman filter per vehicle (smooth readings)
#     - Multi-frame averaging (no jumpy numbers)
#     - Spike filter (rejects impossible speeds)
#     - Perspective correction (accounts for camera angle)
#     - Confidence scoring (don't trust first few frames)
#     """
#     def __init__(
#         self,
#         fps: float = 30.0,
#         calibration_pixels: float = 200.0,
#         calibration_meters: float = 10.0,
#         speed_limit_mph: float = 20.0,
#         min_frames: int = 5,
#         smoothing_window: int = 8,
#         max_speed_mph: float = 150.0,
#         stale_seconds: float = 3.0,
#         frame_height: float = 720.0,
#         near_scale: float = 1.0,
#         far_scale: float = 2.5,
#     ):
#         self.fps = fps
#         self.pixels_per_meter = calibration_pixels / calibration_meters
#         self.speed_limit_mph = speed_limit_mph
#         self.min_frames = min_frames
#         self.smoothing_window = smoothing_window
#         self.max_speed_mph = max_speed_mph
#         self.stale_seconds = stale_seconds
#         self.frame_height = frame_height
#         self.near_scale = near_scale
#         self.far_scale = far_scale
#         self._vehicles: Dict[int, VehicleState] = {}

#     def update(self, track_id: int, cx: float, cy: float) -> Optional[float]:
#         now = time.time()
#         if track_id not in self._vehicles:
#             self._vehicles[track_id] = VehicleState()
#         state = self._vehicles[track_id]
#         state.last_seen = now
#         state.frame_count += 1
#         state.positions.append((cx, cy))
#         state.timestamps.append(now)

#         if len(state.positions) < 2 or state.frame_count < self.min_frames:
#             return None

#         raw_speed = self._calculate_raw_speed(state, cy)
#         if raw_speed is None or raw_speed > self.max_speed_mph:
#             return state.smoothed_speed if state.smoothed_speed > 0 else None

#         state.raw_speeds.append(raw_speed)
#         window = list(state.raw_speeds)[-self.smoothing_window:]
#         averaged = sum(window) / len(window)
#         smoothed = state.kalman.update(averaged)
#         state.smoothed_speed = round(smoothed, 1)
#         state.confidence = min(1.0, state.frame_count / 20.0)
#         return state.smoothed_speed

#     def is_violation(self, track_id: int) -> bool:
#         state = self._vehicles.get(track_id)
#         if state is None or state.confidence < 0.3:
#             return False
#         return state.smoothed_speed > self.speed_limit_mph

#     def get_confidence(self, track_id: int) -> float:
#         state = self._vehicles.get(track_id)
#         return round(state.confidence, 2) if state else 0.0

#     def get_speed(self, track_id: int) -> float:
#         state = self._vehicles.get(track_id)
#         return state.smoothed_speed if state else 0.0

#     def cleanup_stale(self):
#         now = time.time()
#         stale = [tid for tid, st in self._vehicles.items()
#                  if now - st.last_seen > self.stale_seconds]
#         for tid in stale:
#             del self._vehicles[tid]

#     def _perspective_factor(self, cy: float) -> float:
#         ratio = max(0.0, min(1.0, cy / self.frame_height))
#         return self.far_scale + ratio * (self.near_scale - self.far_scale)

#     def _calculate_raw_speed(self, state: VehicleState, cy: float) -> Optional[float]:
#         if len(state.positions) < 2 or len(state.timestamps) < 2:
#             return None
#         x1, y1 = state.positions[-2]
#         x2, y2 = state.positions[-1]
#         t1 = state.timestamps[-2]
#         t2 = state.timestamps[-1]
#         dt = t2 - t1
#         if dt <= 0:
#             return None
#         pixel_dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
#         meters = pixel_dist / self.pixels_per_meter
#         speed_mps = meters / dt
#         speed_mph = speed_mps * 2.237  # m/s → mph (matches original units)
#         factor = self._perspective_factor(cy)
#         return speed_mph * factor


# # ===========================================================================
# # INIT
# # ===========================================================================

# # Initialize EasyOCR reader
# ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())


# def read_license_plate(frame, box):
#     x1, y1, x2, y2 = box
#     plate_img = frame[y1:y2, x1:x2]
#     if plate_img.size == 0:
#         return "Unclear"
#     plate_img = cv2.resize(plate_img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
#     plate_img = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
#     results = ocr_reader.readtext(plate_img)
#     if results:
#         return results[0][1]
#     return "Unclear"


# def send_email_with_attachment(to_email, df):
#     try:
#         sender_email = "your_email@example.com"
#         sender_password = "your_email_password"
#         smtp_server = "smtp.gmail.com"
#         smtp_port = 587

#         subject = "Speed Limit Violation Report"
#         body = "Attached is the CSV file with the list of speed limit violations."
#         msg = MIMEMultipart()
#         msg['From'] = sender_email
#         msg['To'] = to_email
#         msg['Subject'] = subject
#         msg.attach(MIMEText(body, 'plain'))

#         attachment = MIMEBase('application', 'octet-stream')
#         attachment.set_payload(df.to_csv(index=False).encode())
#         encoders.encode_base64(attachment)
#         attachment.add_header('Content-Disposition', "attachment; filename=violators.csv")
#         msg.attach(attachment)

#         server = smtplib.SMTP(smtp_server, smtp_port)
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, to_email, msg.as_string())
#         server.quit()
#         st.success(f"Email sent successfully to {to_email}")
#     except Exception as e:
#         st.error(f"Error sending email: {str(e)}")


# # ===========================================================================
# # STREAMLIT UI
# # ===========================================================================

# st.set_page_config(layout="wide")
# st.title("🚗 Speed Limit Violation Detection System")
# st.markdown("""
# Upload a video. The app will track cars, estimate their speeds, read their license plates,
# and highlight any vehicle that goes over the speed limit. 🔴 Red = speeding. 🟢 Green = under the limit.
# """)

# col1, col2 = st.columns([3, 2])

# device = "cuda" if torch.cuda.is_available() else "cpu"
# st.sidebar.markdown(f"**💻 Running on:** `{device.upper()}`")

# model = YOLO('yolov8n.pt').to(device)
# license_plate_detector = YOLO('yolov8n.pt').to(device)

# placeholder_chart = st.empty()
# violators_data = []
# stframe = st.empty()
# speeding_car_images = []
# speeding_cars = set()
# car_speeds = {}
# frame_counter = 0

# # ===========================================================================
# # SIDEBAR
# # ===========================================================================

# with st.sidebar:
#     st.header("📋 Settings")
#     use_live_cam = st.checkbox("📷 Use Live Camera")
#     uploaded_video = None
#     if not use_live_cam:
#         uploaded_video = st.file_uploader("Upload a video", type=["mp4", "mov", "avi"])
#     speed_limit = st.slider("Set Speed Limit (mph)", min_value=1, max_value=100, value=20)

#     st.markdown("---")
#     st.subheader("⚙️ Speed Estimator Calibration")
#     calibration_pixels = st.slider("Calibration pixels (reference distance in pixels)", 50, 500, 200)
#     calibration_meters = st.slider("Calibration meters (real-world distance in meters)", 1, 50, 10)
#     st.caption("Tip: Pick two points on the road in your video, count pixels between them, estimate real distance.")

#     show_gallery = st.checkbox("📸 Show Speeding Cars Gallery")

#     st.markdown("---")
#     st.subheader("📧 Send Violator Data via Email")
#     recipient_email = st.text_input("Recipient's Email", placeholder="Enter recipient email")
#     send_email_button = st.button("📤 Send Violator Data via Email")

#     st.markdown("---")
#     if st.button("🔄 Reset System"):
#         violators_data.clear()
#         speeding_car_images.clear()
#         speeding_cars.clear()
#         car_speeds.clear()
#         frame_counter = 0
#         placeholder_chart.empty()
#         stframe.empty()
#         st.success("System reset! All data cleared.")

#     st.markdown("---")
#     st.subheader("🛠️ OCR Tips")
#     st.info("""
#     **For best OCR results, ensure plates are:**
#     - Well-lit
#     - At least 100px wide
#     - Facing the camera
#     """)


# # ===========================================================================
# # MAIN PROCESSING FUNCTION
# # ===========================================================================

# def process_frame_for_video(frame, estimator: PerspectiveSpeedEstimator):
#     global speeding_car_images, violators_data, speeding_cars, car_speeds, frame_counter

#     frame_counter += 1
#     results = model.track(frame, persist=True)
#     license_plate_results = license_plate_detector(frame)[0]
#     annotated_frame = frame.copy()
#     curr_time = time.time()

#     # Draw license plate boxes
#     for lp_box in license_plate_results.boxes:
#         x1, y1, x2, y2 = map(int, lp_box.xyxy[0])
#         cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
#         plate_text = read_license_plate(frame, (x1, y1, x2, y2))
#         cv2.putText(annotated_frame, plate_text, (x1, y1 - 10),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

#     # Process each tracked vehicle
#     for box in results[0].boxes:
#         cls = int(box.cls[0])
#         if model.names[cls] != 'car':
#             continue

#         x1, y1, x2, y2 = map(int, box.xyxy[0])
#         car_id = int(box.id[0]) if box.id is not None else None
#         if car_id is None:
#             continue

#         center_x = (x1 + x2) // 2
#         center_y = (y1 + y2) // 2

#         # ---- IMPROVED SPEED ESTIMATION ----
#         speed = estimator.update(car_id, center_x, center_y)
#         confidence = estimator.get_confidence(car_id)

#         box_color = (0, 255, 0)  # green default
#         label_text = ""

#         if speed is not None and confidence > 0.3:
#             car_speeds[car_id] = speed

#             if speed > speed_limit:
#                 speeding_cars.add(car_id)
#                 box_color = (0, 0, 255)  # red
#                 label_text = f"Speeding: {speed} mph"

#                 if car_id not in [v["Car ID"] for v in violators_data]:
#                     plate_number = read_license_plate(frame, (x1, y1, x2, y2))
#                     timestamp = time.strftime("%H:%M:%S", time.localtime(curr_time))
#                     violators_data.append({
#                         "Car ID": car_id,
#                         "Speed (mph)": speed,
#                         "License Plate": plate_number,
#                         "Timestamp": timestamp
#                     })
#                     car_img = frame[y1:y2, x1:x2]
#                     if car_img.size > 0:
#                         car_img = cv2.cvtColor(car_img, cv2.COLOR_BGR2RGB)
#                         car_img_resized = cv2.resize(car_img, (600, 400))
#                         speeding_car_images.append((car_id, car_img_resized, speed, timestamp))
#             else:
#                 if car_id in speeding_cars and speed < speed_limit * 0.9:
#                     speeding_cars.discard(car_id)
#                 label_text = f"{speed} mph"

#         # Keep red if previously speeding
#         if car_id in speeding_cars:
#             box_color = (0, 0, 255)
#             if not label_text:
#                 last_speed = car_speeds.get(car_id, 0)
#                 label_text = f"Speeding: {last_speed} mph"

#         cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)
#         if label_text:
#             cv2.putText(annotated_frame, label_text, (x1, y1 - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

#     # Cleanup stale vehicles every 30 frames to save memory
#     if frame_counter % 30 == 0:
#         estimator.cleanup_stale()

#     if violators_data:
#         df = pd.DataFrame(violators_data).drop_duplicates(subset='Car ID', keep='last')
#         placeholder_chart.dataframe(df)

#     return annotated_frame


# # ===========================================================================
# # VIDEO / CAMERA MODE
# # ===========================================================================

# if uploaded_video is not None:
#     tfile = tempfile.NamedTemporaryFile(delete=False)
#     tfile.write(uploaded_video.read())
#     cap = cv2.VideoCapture(tfile.name)

#     # Read actual FPS from video
#     actual_fps = cap.get(cv2.CAP_PROP_FPS)
#     if actual_fps <= 0:
#         actual_fps = 30.0
#     frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

#     # Create estimator with actual video FPS and user calibration settings
#     estimator = PerspectiveSpeedEstimator(
#         fps=actual_fps,
#         calibration_pixels=calibration_pixels,
#         calibration_meters=calibration_meters,
#         speed_limit_mph=speed_limit,
#         frame_height=frame_height,
#     )

#     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#     output_path = os.path.join(tempfile.gettempdir(), "processed_output.mp4")
#     width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     out = cv2.VideoWriter(output_path, fourcc, actual_fps, (width, frame_height))

#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break
#         annotated_frame = process_frame_for_video(frame, estimator)
#         out.write(annotated_frame)
#         with col1:
#             stframe.image(annotated_frame, channels="BGR", width=800)

#     cap.release()
#     out.release()

# elif use_live_cam:
#     cap = cv2.VideoCapture(0)
#     actual_fps = cap.get(cv2.CAP_PROP_FPS)
#     if actual_fps <= 0:
#         actual_fps = 30.0
#     frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

#     estimator = PerspectiveSpeedEstimator(
#         fps=actual_fps,
#         calibration_pixels=calibration_pixels,
#         calibration_meters=calibration_meters,
#         speed_limit_mph=speed_limit,
#         frame_height=frame_height,
#     )

#     stop_button = st.button("❌ Stop Camera")
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret or stop_button:
#             break
#         annotated_frame = process_frame_for_video(frame, estimator)
#         with col1:
#             stframe.image(annotated_frame, channels="BGR", width=800)
#     cap.release()


# # ===========================================================================
# # SUMMARY & DOWNLOAD
# # ===========================================================================

# if violators_data:
#     st.subheader("Speed Limit Violations Summary")
#     final_df = pd.DataFrame(violators_data).drop_duplicates(subset='Car ID', keep='last')
#     st.dataframe(final_df)

#     csv = final_df.to_csv(index=False).encode('utf-8')
#     st.download_button("⬇️ Download Violator Data as CSV", data=csv,
#                        file_name="violators.csv", mime="text/csv")

#     if not use_live_cam and uploaded_video:
#         with open(output_path, "rb") as f:
#             video_bytes = f.read()
#         st.download_button("⬇️ Download Processed Video", data=video_bytes,
#                            file_name="processed_output.mp4", mime="video/mp4")

#     if recipient_email and send_email_button:
#         send_email_with_attachment(recipient_email, final_df)
# else:
#     st.success("No speed limit violations detected yet!")


# # ===========================================================================
# # GALLERY
# # ===========================================================================

# if show_gallery:
#     st.subheader("🚨 Speeding Cars Gallery")
#     if violators_data:
#         car_gallery_data = {}
#         final_df_ids = set(final_df['Car ID'].unique())
#         for car_id, img, speed, timestamp in speeding_car_images:
#             if car_id in final_df_ids:
#                 if car_id not in car_gallery_data:
#                     car_gallery_data[car_id] = (img, speed, timestamp)
#                 else:
#                     if timestamp > car_gallery_data[car_id][2]:
#                         car_gallery_data[car_id] = (img, speed, timestamp)

#         if car_gallery_data:
#             gallery_items = sorted(
#                 [(cid, d[0], d[1], d[2]) for cid, d in car_gallery_data.items()],
#                 key=lambda x: x[0]
#             )
#             cols = st.columns(3)
#             for i, (car_id, img, speed, timestamp) in enumerate(gallery_items):
#                 with cols[i % 3]:
#                     st.image(img, caption=f"Car {car_id} | {speed} mph @ {timestamp}", width=300)
#         else:
#             st.warning("No speeding car images available yet.")
#     else:
#         st.warning("No speeding cars detected yet.")





# Speed_Violation_Detector.py — Enterprise UI Version
import streamlit as st
import cv2
import tempfile
import numpy as np
import time
import math
import pandas as pd
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Optional
from ultralytics import YOLO
import easyocr
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from PIL import Image
import torch

# ===========================================================================
# MATH BACKEND: PERSPECTIVE SPEED ESTIMATOR (Your Improved Logic)
# ===========================================================================

class KalmanFilter1D:
    def __init__(self, process_noise=1.0, measurement_noise=10.0):
        self.q = process_noise
        self.r = measurement_noise
        self.x = 0.0
        self.p = 1.0
        self.initialized = False

    def update(self, measurement: float) -> float:
        if not self.initialized:
            self.x = measurement
            self.initialized = True
            return self.x
        self.p = self.p + self.q
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * self.p
        return self.x

@dataclass
class VehicleState:
    positions: deque = field(default_factory=lambda: deque(maxlen=30))
    timestamps: deque = field(default_factory=lambda: deque(maxlen=30))
    raw_speeds: deque = field(default_factory=lambda: deque(maxlen=10))
    kalman: KalmanFilter1D = field(default_factory=KalmanFilter1D)
    smoothed_speed: float = 0.0
    confidence: float = 0.0
    last_seen: float = field(default_factory=time.time)
    frame_count: int = 0

class PerspectiveSpeedEstimator:
    def __init__(
        self, fps: float = 30.0, calibration_pixels: float = 200.0, calibration_meters: float = 10.0,
        speed_limit_mph: float = 20.0, min_frames: int = 5, smoothing_window: int = 8,
        max_speed_mph: float = 150.0, stale_seconds: float = 3.0, frame_height: float = 720.0,
        near_scale: float = 1.0, far_scale: float = 2.5
    ):
        self.fps = fps
        self.pixels_per_meter = calibration_pixels / calibration_meters
        self.speed_limit_mph = speed_limit_mph
        self.min_frames = min_frames
        self.smoothing_window = smoothing_window
        self.max_speed_mph = max_speed_mph
        self.stale_seconds = stale_seconds
        self.frame_height = frame_height
        self.near_scale = near_scale
        self.far_scale = far_scale
        self._vehicles: Dict[int, VehicleState] = {}

    def update(self, track_id: int, cx: float, cy: float) -> Optional[float]:
        now = time.time()
        if track_id not in self._vehicles:
            self._vehicles[track_id] = VehicleState()
        state = self._vehicles[track_id]
        state.last_seen = now
        state.frame_count += 1
        state.positions.append((cx, cy))
        state.timestamps.append(now)

        if len(state.positions) < 2 or state.frame_count < self.min_frames:
            return None

        raw_speed = self._calculate_raw_speed(state, cy)
        if raw_speed is None or raw_speed > self.max_speed_mph:
            return state.smoothed_speed if state.smoothed_speed > 0 else None

        state.raw_speeds.append(raw_speed)
        window = list(state.raw_speeds)[-self.smoothing_window:]
        averaged = sum(window) / len(window)
        smoothed = state.kalman.update(averaged)
        state.smoothed_speed = round(smoothed, 1)
        state.confidence = min(1.0, state.frame_count / 20.0)
        return state.smoothed_speed

    def is_violation(self, track_id: int) -> bool:
        state = self._vehicles.get(track_id)
        if state is None or state.confidence < 0.3:
            return False
        return state.smoothed_speed > self.speed_limit_mph

    def get_confidence(self, track_id: int) -> float:
        state = self._vehicles.get(track_id)
        return round(state.confidence, 2) if state else 0.0

    def cleanup_stale(self):
        now = time.time()
        stale = [tid for tid, st in self._vehicles.items() if now - st.last_seen > self.stale_seconds]
        for tid in stale:
            del self._vehicles[tid]

    def _perspective_factor(self, cy: float) -> float:
        ratio = max(0.0, min(1.0, cy / self.frame_height))
        return self.far_scale + ratio * (self.near_scale - self.far_scale)

    def _calculate_raw_speed(self, state: VehicleState, cy: float) -> Optional[float]:
        if len(state.positions) < 2 or len(state.timestamps) < 2:
            return None
        x1, y1 = state.positions[-2]
        x2, y2 = state.positions[-1]
        t1 = state.timestamps[-2]
        t2 = state.timestamps[-1]
        dt = t2 - t1
        if dt <= 0:
            return None
        pixel_dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        meters = pixel_dist / self.pixels_per_meter
        speed_mps = meters / dt
        speed_mph = speed_mps * 2.237
        factor = self._perspective_factor(cy)
        return speed_mph * factor

# ===========================================================================
# INIT MODEL UTILITIES
# ===========================================================================

ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

def read_license_plate(frame, box):
    x1, y1, x2, y2 = box
    plate_img = frame[y1:y2, x1:x2]
    if plate_img.size == 0:
        return "Unclear"
    plate_img = cv2.resize(plate_img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    plate_img = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    results = ocr_reader.readtext(plate_img)
    if results:
        return results[0][1]
    return "Unclear"

def send_email_with_attachment(to_email, df):
    try:
        sender_email = "your_email@example.com"
        sender_password = "your_email_password"
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = "Speed Limit Violation Report"
        msg.attach(MIMEText("Attached is the automated CSV report containing vehicle violations.", 'plain'))
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(df.to_csv(index=False).encode())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', "attachment; filename=violators.csv")
        msg.attach(attachment)
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        st.success(f"Report emailed successfully to {to_email}")
    except Exception as e:
        st.error(f"Mail delivery failed: {str(e)}")

# ===========================================================================
# HIGH-END MODERN UI SKIN INJECTION
# ===========================================================================

st.set_page_config(layout="wide", page_title="AI Speed Telemetry", page_icon="🚗")

# Inject Custom Professional Stylesheet
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    h1 { color: #f0f2f6 !important; font-weight: 800 !important; letter-spacing: -1px; }
    .stButton>button { background-color: #262730; color: #f0f2f6; border-radius: 6px; border: 1px solid #4a4b50; width: 100%; transition: 0.3s; }
    .stButton>button:hover { background-color: #ff4b4b; border-color: #ff4b4b; color: white; }
    .metric-card { background: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #00fff0; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .metric-card.danger { border-left-color: #ff4b4b; }
    .metric-card.neutral { border-left-color: #ffd166; }
    .metric-val { font-size: 2rem; font-weight: 700; color: #ffffff; margin: 0; }
    .metric-lbl { font-size: 0.85rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# Main Title Header Banner
st.title("⚡ AI Speed Limit Violation Detection System")
st.markdown("##### *Intelligent Edge Telemetry & Computer Vision Analysis Dashboard*")
st.markdown("---")

# Global Tracking Invariants
device = "cuda" if torch.cuda.is_available() else "cpu"
model = YOLO('yolov8n.pt').to(device)
license_plate_detector = YOLO('yolov8n.pt').to(device)

if 'violators_data' not in st.session_state:
    st.session_state.violators_data = []
if 'speeding_car_images' not in st.session_state:
    st.session_state.speeding_car_images = []
if 'speeding_cars' not in st.session_state:
    st.session_state.speeding_cars = set()
if 'car_speeds' not in st.session_state:
    st.session_state.car_speeds = {}
if 'frame_counter' not in st.session_state:
    st.session_state.frame_counter = 0

# ===========================================================================
# SIDEBAR CONTROL PANEL
# ===========================================================================

with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/speed.png", width=70)
    st.header("Control Station")
    st.markdown(f"**Compute Hardware:** `{device.upper()}`")
    st.markdown("---")
    
    use_live_cam = st.checkbox("📷 Engage Live Webcam Feed")
    uploaded_video = None
    if not use_live_cam:
        uploaded_video = st.file_uploader("Upload Traffic Stream Source", type=["mp4", "mov", "avi"])
        
    speed_limit = st.slider("Target Speed Threshold (mph)", min_value=5, max_value=90, value=20)

    with st.expander("🛠️ Advanced Calibration Matrix"):
        calibration_pixels = st.slider("Reference Envelope (Pixels)", 50, 500, 200)
        calibration_meters = st.slider("Physical Distance (Meters)", 1, 50, 10)
    
    show_gallery = st.checkbox("📸 Enable Real-time Capture Gallery", value=True)

    st.markdown("---")
    st.subheader("📬 Remote Reporting")
    recipient_email = st.text_input("Target Email Address", placeholder="officer@agency.gov")
    send_email_button = st.button("📤 Dispatch Violation Data")

    if st.button("🔄 System Master Reset"):
        st.session_state.violators_data.clear()
        st.session_state.speeding_car_images.clear()
        st.session_state.speeding_cars.clear()
        st.session_state.car_speeds.clear()
        st.session_state.frame_counter = 0
        st.rerun()

# ===========================================================================
# LIVE TELEMETRY METRICS CARDS
# ===========================================================================

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.markdown(f'<div class="metric-card"><p class="metric-lbl">Speed Limit Ceiling</p><p class="metric-val">{speed_limit} MPH</p></div>', unsafe_allow_html=True)
with m_col2:
    total_violators = len(st.session_state.violators_data)
    st.markdown(f'<div class="metric-card danger"><p class="metric-lbl">Logged Violations</p><p class="metric-val" style="color:#ff4b4b;">{total_violators} Vehicles</p></div>', unsafe_allow_html=True)
with m_col3:
    active_tracks = len(st.session_state.car_speeds)
    st.markdown(f'<div class="metric-card neutral"><p class="metric-lbl">Monitored Profiles</p><p class="metric-val" style="color:#ffd166;">{active_tracks} Active</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Grid Layout Split (Left: Video Frame Output, Right: Analytical Live Logging)
col1, col2 = st.columns([7, 5])
with col1:
    st.subheader("📺 Computer Vision Analytics Render")
    stframe = st.empty()
with col2:
    st.subheader("📊 Dynamic Violation Manifest")
    placeholder_chart = st.empty()

# ===========================================================================
# CORRECTIONS PIPELINE ENGINE
# ===========================================================================

def process_frame_for_video(frame, estimator: PerspectiveSpeedEstimator):
    st.session_state.frame_counter += 1
    results = model.track(frame, persist=True)
    license_plate_results = license_plate_detector(frame)[0]
    annotated_frame = frame.copy()
    curr_time = time.time()

    for lp_box in license_plate_results.boxes:
        x1, y1, x2, y2 = map(int, lp_box.xyxy[0])
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 165, 0), 2)
        plate_text = read_license_plate(frame, (x1, y1, x2, y2))
        cv2.putText(annotated_frame, f"PLATE: {plate_text}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 2)

    for box in results[0].boxes:
        cls = int(box.cls[0])
        if model.names[cls] != 'car':
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        car_id = int(box.id[0]) if box.id is not None else None
        if car_id is None:
            continue

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        speed = estimator.update(car_id, center_x, center_y)
        confidence = estimator.get_confidence(car_id)

        box_color = (0, 255, 0)
        label_text = ""

        if speed is not None and confidence > 0.3:
            st.session_state.car_speeds[car_id] = speed

            if speed > speed_limit:
                st.session_state.speeding_cars.add(car_id)
                box_color = (0, 0, 255)
                label_text = f"ALERT: {speed} MPH"

                if car_id not in [v["Car ID"] for v in st.session_state.violators_data]:
                    plate_number = read_license_plate(frame, (x1, y1, x2, y2))
                    timestamp = time.strftime("%H:%M:%S", time.localtime(curr_time))
                    st.session_state.violators_data.append({
                        "Car ID": car_id,
                        "Speed (mph)": speed,
                        "License Plate": plate_number,
                        "Timestamp": timestamp
                    })
                    car_img = frame[y1:y2, x1:x2]
                    if car_img.size > 0:
                        car_img = cv2.cvtColor(car_img, cv2.COLOR_BGR2RGB)
                        car_img_resized = cv2.resize(car_img, (300, 200))
                        st.session_state.speeding_car_images.append((car_id, car_img_resized, speed, timestamp))
            else:
                if car_id in st.session_state.speeding_cars and speed < speed_limit * 0.9:
                    st.session_state.speeding_cars.discard(car_id)
                label_text = f"{speed} MPH"

        if car_id in st.session_state.speeding_cars:
            box_color = (0, 0, 255)
            if not label_text:
                last_speed = st.session_state.car_speeds.get(car_id, 0)
                label_text = f"ALERT: {last_speed} MPH"

        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)
        cv2.putText(annotated_frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

    if st.session_state.frame_counter % 30 == 0:
        estimator.cleanup_stale()

    if st.session_state.violators_data:
        df = pd.DataFrame(st.session_state.violators_data).drop_duplicates(subset='Car ID', keep='last')
        placeholder_chart.dataframe(df, use_container_width=True)

    return annotated_frame

# ===========================================================================
# SOURCE EXECUTION LOOPS
# ===========================================================================

if uploaded_video is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_video.read())
    cap = cv2.VideoCapture(tfile.name)

    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    if actual_fps <= 0:
        actual_fps = 30.0
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    estimator = PerspectiveSpeedEstimator(
        fps=actual_fps, calibration_pixels=calibration_pixels,
        calibration_meters=calibration_meters, speed_limit_mph=speed_limit, frame_height=frame_height
    )

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        annotated_frame = process_frame_for_video(frame, estimator)
        stframe.image(annotated_frame, channels="BGR", use_container_width=True)
    cap.release()

elif use_live_cam:
    cap = cv2.VideoCapture(0)
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    estimator = PerspectiveSpeedEstimator(
        fps=30.0, calibration_pixels=calibration_pixels,
        calibration_meters=calibration_meters, speed_limit_mph=speed_limit, frame_height=frame_height
    )

    stop_button = st.button("🛑 Terminate Camera Pipeline")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or stop_button:
            break
        annotated_frame = process_frame_for_video(frame, estimator)
        stframe.image(annotated_frame, channels="BGR", use_container_width=True)
    cap.release()

# ===========================================================================
# EXTRACTION FOOTER DATA
# ===========================================================================

if st.session_state.violators_data:
    st.markdown("---")
    st.subheader("🗂️ Data Export Controls")
    final_df = pd.DataFrame(st.session_state.violators_data).drop_duplicates(subset='Car ID', keep='last')
    
    csv = final_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Violation Database (CSV)", data=csv, file_name="violators.csv", mime="text/csv")

    if recipient_email and send_email_button:
        send_email_with_attachment(recipient_email, final_df)

if show_gallery and st.session_state.violators_data:
    st.markdown("---")
    st.subheader("🚨 High-Speed Target Intercept Gallery")
    car_gallery_data = {}
    final_df_ids = set(pd.DataFrame(st.session_state.violators_data)['Car ID'].unique())
    
    for car_id, img, speed, timestamp in st.session_state.speeding_car_images:
        if car_id in final_df_ids:
            if car_id not in car_gallery_data or timestamp > car_gallery_data[car_id][2]:
                car_gallery_data[car_id] = (img, speed, timestamp)

    if car_gallery_data:
        gallery_items = sorted([(cid, d[0], d[1], d[2]) for cid, d in car_gallery_data.items()], key=lambda x: x[0])
        cols = st.columns(4)
        for i, (car_id, img, speed, timestamp) in enumerate(gallery_items):
            with cols[i % 4]:
                st.image(img, caption=f"ID: {car_id} | {speed} MPH | {timestamp}", use_container_width=True)