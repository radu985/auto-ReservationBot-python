from PyQt6 import QtCore, QtGui, QtWidgets
from typing import Optional
import os
import sys
import cv2
import numpy as np
import json
import mimetypes
from pathlib import Path

# Ensure import paths work both in source and PyInstaller executables
def _ensure_module_paths() -> None:
    try:
        # When frozen, use the bundle directory (MEIPASS or executable dir)
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            # app/main.py → project root is one level up
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            base_dir,
            os.path.join(base_dir, 'app'),
            os.path.join(base_dir, 'app', 'services'),
        ]
        for p in candidates:
            if p and p not in sys.path and os.path.exists(p):
                sys.path.insert(0, p)
    except Exception:
        pass

_ensure_module_paths()

# Handle both package and flat imports
try:
    from app.services.csv_io import ClientRecord, load_clients, save_clients  # type: ignore
    from app.services.country_codes import COUNTRY_CALLING_CODES  # type: ignore
    from app.services.vfs_automation import VFSBotWorker, AvailabilityStatus, BookingResult  # type: ignore
except Exception:
    from services.csv_io import ClientRecord, load_clients, save_clients  # type: ignore
    from services.country_codes import COUNTRY_CALLING_CODES  # type: ignore
    from services.vfs_automation import VFSBotWorker, AvailabilityStatus, BookingResult  # type: ignore


class StatusLight(QtWidgets.QLabel):
    """Round status indicator: green=ok, yellow=warning, gray=idle."""

    def __init__(self, diameter: int = 18, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._diameter = diameter
        self._color = QtGui.QColor("#9e9e9e")
        self.setFixedSize(diameter + 2, diameter + 2)

    def set_color(self, color_name: str) -> None:
        self._color = QtGui.QColor(color_name)
        self.update()

    def set_green(self) -> None:
        self.set_color("#15d10f")

    def set_yellow(self) -> None:
        self.set_color("#ffd54f")

    def set_gray(self) -> None:
        self.set_color("#9e9e9e")

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # type: ignore[override]
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        brush = QtGui.QBrush(self._color)
        painter.setBrush(brush)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, self._diameter, self._diameter)


class AccountTab(QtWidgets.QWidget):
    """Account tab layout per provided screenshot."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)

        self.first_name = QtWidgets.QLineEdit()
        self.first_name.setPlaceholderText("Please enter first name.")
        self.last_name = QtWidgets.QLineEdit()
        self.last_name.setPlaceholderText("Please enter last name.")
        self.dob = QtWidgets.QDateEdit(calendarPopup=True)
        self.dob.setDisplayFormat("dd/MM/yyyy")
        self.dob.setDate(QtCore.QDate.currentDate())
        self.email = QtWidgets.QLineEdit()
        self.email.setPlaceholderText("jane.doe@email.com")
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.confirm_password = QtWidgets.QLineEdit()
        self.confirm_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        mobile_layout = QtWidgets.QHBoxLayout()
        self.country_code = QtWidgets.QComboBox()
        self.country_code.setFixedWidth(160)
        # Populate with "Country(code)" but store numeric code as userData
        for country, code in COUNTRY_CALLING_CODES:
            self.country_code.addItem(f"{country}({code})", code)
        self.mobile_number = QtWidgets.QLineEdit()
        self.mobile_number.setPlaceholderText("1234567890")
        mobile_layout.addWidget(self.country_code)
        mobile_layout.addWidget(self.mobile_number)
        mobile_container = QtWidgets.QWidget()
        mobile_container.setLayout(mobile_layout)

        form.addRow(self._required_label("First Name"), self.first_name)
        form.addRow(self._required_label("Last Name"), self.last_name)
        form.addRow(self._required_label("Date Of Birth"), self.dob)
        form.addRow(self._required_label("Email"), self.email)
        form.addRow(self._required_label("Password"), self.password)
        form.addRow(self._required_label("Confirm Password"), self.confirm_password)
        form.addRow(self._required_label("Mobile Number"), mobile_container)

        container = QtWidgets.QWidget()
        container.setLayout(form)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(scroll)

        # Register button row at the bottom
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        self.register_btn = QtWidgets.QPushButton("Register")
        btn_row.addWidget(self.register_btn)
        root.addLayout(btn_row)

    def _required_label(self, text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(f"{text} *")
        return label


class OrderTab(QtWidgets.QWidget):
    """Order tab with Application Center, Service Center, and Trip Reason dropdowns."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)

        # Application Center dropdown
        self.application_center = QtWidgets.QComboBox()
        self.application_center.setPlaceholderText("Select Application Center")
        self.application_center.addItem("Portugal Visa Center", "portugal_center")
        self.application_center.addItem("France Visa Center", "france_center")
        self.application_center.addItem("Spain Visa Center", "spain_center")

        # Service Center dropdown
        self.service_center = QtWidgets.QComboBox()
        self.service_center.setPlaceholderText("Select the category of your nomination")
        self.service_center.addItem("Tourist Visa", "tourist")
        self.service_center.addItem("Business Visa", "business")
        self.service_center.addItem("Transit Visa", "transit")
        self.service_center.addItem("Student Visa", "student")
        self.service_center.addItem("Work Visa", "work")
        self.service_center.addItem("Family Visit", "family")
        self.service_center.addItem("Medical Treatment", "medical")
        self.service_center.addItem("Official Visit", "official")

        # Trip Reason dropdown
        self.trip_reason = QtWidgets.QComboBox()
        self.trip_reason.setPlaceholderText("Select your subcategory")
        self.trip_reason.addItem("Leisure/Tourism", "leisure")
        self.trip_reason.addItem("Business Meeting", "business_meeting")
        self.trip_reason.addItem("Conference/Seminar", "conference")
        self.trip_reason.addItem("Family Visit", "family_visit")
        self.trip_reason.addItem("Medical Treatment", "medical_treatment")
        self.trip_reason.addItem("Education/Study", "education")
        self.trip_reason.addItem("Work Assignment", "work_assignment")
        self.trip_reason.addItem("Transit", "transit")
        self.trip_reason.addItem("Other", "other")

        form.addRow(self._required_label("Application Center"), self.application_center)
        form.addRow(self._required_label("Choose your Service Center"), self.service_center)
        form.addRow(self._required_label("Choose the reason for your trip"), self.trip_reason)

        container = QtWidgets.QWidget()
        container.setLayout(form)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(scroll)

        # Save button row
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        self.save_btn = QtWidgets.QPushButton("Save")
        btn_row.addWidget(self.save_btn)
        root.addLayout(btn_row)

    def _required_label(self, text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(f"{text} *")
        return label


class ApplicationTab(QtWidgets.QWidget):
    """Application tab with personal details form."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)

        # Auto-populated fields (read-only)
        self.first_name = QtWidgets.QLineEdit()
        self.first_name.setPlaceholderText("DOCA")
        self.first_name.setReadOnly(True)
        self.first_name.setStyleSheet("background-color: #f5f5f5; color: #666;")

        self.last_name = QtWidgets.QLineEdit()
        self.last_name.setPlaceholderText("CO")
        self.last_name.setReadOnly(True)
        self.last_name.setStyleSheet("background-color: #f5f5f5; color: #666;")

        # Contact number (country code + number) - auto-populated
        contact_layout = QtWidgets.QHBoxLayout()
        self.contact_country_code = QtWidgets.QLineEdit()
        self.contact_country_code.setFixedWidth(60)
        self.contact_country_code.setPlaceholderText("245")
        self.contact_country_code.setReadOnly(True)
        self.contact_country_code.setStyleSheet("background-color: #f5f5f5; color: #666;")
        self.contact_number = QtWidgets.QLineEdit()
        self.contact_number.setPlaceholderText("906620784")
        self.contact_number.setReadOnly(True)
        self.contact_number.setStyleSheet("background-color: #f5f5f5; color: #666;")
        contact_layout.addWidget(self.contact_country_code)
        contact_layout.addWidget(self.contact_number)
        contact_container = QtWidgets.QWidget()
        contact_container.setLayout(contact_layout)

        self.email = QtWidgets.QLineEdit()
        self.email.setPlaceholderText("DOCACO54@GMAIL.COM")
        self.email.setReadOnly(True)
        self.email.setStyleSheet("background-color: #f5f5f5; color: #666;")

        # Add auto-populated fields section
        form.addRow(self._required_label("First Name"), self.first_name)
        form.addRow(self._required_label("Last Name"), self.last_name)
        form.addRow(self._required_label("Contact number"), contact_container)
        form.addRow(self._required_label("Email"), self.email)

        # Add separator line
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #ccc; margin: 10px 0;")
        form.addRow(separator)

        # Editable fields section
        self.gender = QtWidgets.QComboBox()
        self.gender.addItem("Select")
        self.gender.addItem("Male", "male")
        self.gender.addItem("Female", "female")
        self.gender.addItem("Other", "other")

        self.date_of_birth = QtWidgets.QDateEdit(calendarPopup=True)
        self.date_of_birth.setDisplayFormat("dd/MM/yyyy")
        self.date_of_birth.setDate(QtCore.QDate(2004, 3, 18))  # Default as shown in image

        self.current_nationality = QtWidgets.QComboBox()
        self.current_nationality.addItem("Select")
        # Populate with country names from country_codes.py
        for country, _ in COUNTRY_CALLING_CODES:
            self.current_nationality.addItem(country, country)

        self.passport_number = QtWidgets.QLineEdit()
        self.passport_number.setPlaceholderText("ENTER PASSPORT NUMBER")

        self.passport_expiry = QtWidgets.QDateEdit(calendarPopup=True)
        self.passport_expiry.setDisplayFormat("dd/MM/yyyy")
        self.passport_expiry.setDate(QtCore.QDate.currentDate())

        # Add editable fields
        form.addRow(self._required_label("Gender"), self.gender)
        form.addRow(self._required_label("Date Of Birth"), self.date_of_birth)
        form.addRow(self._required_label("Current Nationality"), self.current_nationality)
        form.addRow(self._required_label("Passport Number"), self.passport_number)
        form.addRow(self._required_label("Passport Expiry Date"), self.passport_expiry)

        container = QtWidgets.QWidget()
        container.setLayout(form)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(scroll)

        # Save button row
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        self.save_btn = QtWidgets.QPushButton("Save")
        btn_row.addWidget(self.save_btn)
        root.addLayout(btn_row)

    def _required_label(self, text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(f"{text} *")
        return label

    def populate_from_account(self, account_tab) -> None:
        """Auto-populate fields from Account tab values."""
        self.first_name.setText(account_tab.first_name.text())
        self.last_name.setText(account_tab.last_name.text())
        self.email.setText(account_tab.email.text())
        
        # Extract country code and number from mobile field
        country_code = account_tab.country_code.currentData() or ""
        mobile_number = account_tab.mobile_number.text()
        self.contact_country_code.setText(country_code)
        self.contact_number.setText(mobile_number)


class ImageTab(QtWidgets.QWidget):
    """Image tab with facial recognition for passport photos and videos."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.camera = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.face_locations = []
        # Use proper data directory for both source and EXE
        if getattr(sys, 'frozen', False):
            # In EXE, use the directory where the executable is located
            self.info_dir = Path(os.path.dirname(sys.executable)) / "info"
        else:
            # In source, use the project root
            self.info_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "info"
        self.info_dir.mkdir(exist_ok=True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QtWidgets.QLabel("Passport Photo & Video Capture")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Camera preview area
        self.camera_label = QtWidgets.QLabel()
        self.camera_label.setMinimumSize(427, 320)  # About 2/3 of original size (640x480)
        self.camera_label.setStyleSheet("border: 2px solid #ccc; background-color: #f0f0f0;")
        self.camera_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setText("Camera Preview\nClick 'Start Camera' to begin")
        layout.addWidget(self.camera_label)

        # Control buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.start_camera_btn = QtWidgets.QPushButton("Start Camera")
        self.start_camera_btn.clicked.connect(self.start_camera)
        
        self.stop_camera_btn = QtWidgets.QPushButton("Stop Camera")
        self.stop_camera_btn.clicked.connect(self.stop_camera)
        self.stop_camera_btn.setEnabled(False)
        
        self.capture_photo_btn = QtWidgets.QPushButton("Capture Photo")
        self.capture_photo_btn.clicked.connect(self.capture_photo)
        self.capture_photo_btn.setEnabled(False)
        
        self.start_video_btn = QtWidgets.QPushButton("Start Video Recording")
        self.start_video_btn.clicked.connect(self.start_video_recording)
        self.start_video_btn.setEnabled(False)
        
        self.stop_video_btn = QtWidgets.QPushButton("Stop Video Recording")
        self.stop_video_btn.clicked.connect(self.stop_video_recording)
        self.stop_video_btn.setEnabled(False)

        button_layout.addWidget(self.start_camera_btn)
        button_layout.addWidget(self.stop_camera_btn)
        button_layout.addWidget(self.capture_photo_btn)
        button_layout.addWidget(self.start_video_btn)
        button_layout.addWidget(self.stop_video_btn)
        layout.addLayout(button_layout)

        # Status and face detection info
        self.status_label = QtWidgets.QLabel("Status: Camera not started")
        self.status_label.setStyleSheet("color: #666; margin: 5px 0;")
        layout.addWidget(self.status_label)

        self.face_info_label = QtWidgets.QLabel("Face Detection: No faces detected")
        self.face_info_label.setStyleSheet("color: #666; margin: 5px 0;")
        layout.addWidget(self.face_info_label)

        # Photo preview area
        photo_layout = QtWidgets.QHBoxLayout()
        
        self.photo_preview = QtWidgets.QLabel()
        self.photo_preview.setMinimumSize(200, 250)
        self.photo_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.photo_preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setText("Captured Photo\nWill appear here")
        photo_layout.addWidget(self.photo_preview)

        # Face recognition results
        self.recognition_results = QtWidgets.QTextEdit()
        self.recognition_results.setMaximumHeight(150)
        self.recognition_results.setPlaceholderText("Face recognition results will appear here...")
        photo_layout.addWidget(self.recognition_results)

        layout.addLayout(photo_layout)

        # Save button
        save_layout = QtWidgets.QHBoxLayout()
        save_layout.addStretch(1)
        self.save_image_btn = QtWidgets.QPushButton("Save Image Data")
        self.save_image_btn.clicked.connect(self.save_image_data)
        self.save_image_btn.setEnabled(False)
        save_layout.addWidget(self.save_image_btn)
        layout.addLayout(save_layout)

        # Video recording variables
        self.video_writer = None
        self.is_recording = False
        self.captured_photo = None

    def start_camera(self) -> None:
        """Start camera capture."""
        try:
            # Check if we're in an EXE environment
            if getattr(sys, 'frozen', False):
                # In EXE, try different camera indices and handle permissions
                camera_indices = [0, 1, 2]  # Try multiple camera indices
                self.camera = None
                
                for idx in camera_indices:
                    try:
                        self.camera = cv2.VideoCapture(idx)
                        if self.camera.isOpened():
                            # Test if we can actually read a frame
                            ret, frame = self.camera.read()
                            if ret and frame is not None:
                                break
                            else:
                                self.camera.release()
                                self.camera = None
                    except Exception:
                        if self.camera:
                            self.camera.release()
                            self.camera = None
                        continue
                
                if not self.camera or not self.camera.isOpened():
                    self.status_label.setText("Status: Error - No camera found or access denied")
                    QtWidgets.QMessageBox.warning(self, "Camera Error", 
                        "Could not access camera. Please ensure:\n"
                        "1. Camera is connected and working\n"
                        "2. No other applications are using the camera\n"
                        "3. Camera permissions are granted")
                    return
            else:
                # In source environment, use standard approach
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    self.status_label.setText("Status: Error - Could not open camera")
                    return
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.timer.start(60)  # slightly slower to reduce CPU in EXE
            self.start_camera_btn.setEnabled(False)
            self.stop_camera_btn.setEnabled(True)
            self.capture_photo_btn.setEnabled(True)
            self.start_video_btn.setEnabled(True)
            self.status_label.setText("Status: Camera active")
            
        except Exception as e:
            self.status_label.setText(f"Status: Error - {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Camera Error", f"Failed to start camera: {str(e)}")

    def stop_camera(self) -> None:
        """Stop camera capture."""
        self.timer.stop()
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.start_camera_btn.setEnabled(True)
        self.stop_camera_btn.setEnabled(False)
        self.capture_photo_btn.setEnabled(False)
        self.start_video_btn.setEnabled(False)
        self.stop_video_btn.setEnabled(False)
        self.status_label.setText("Status: Camera stopped")
        self.camera_label.setText("Camera Preview\nClick 'Start Camera' to begin")

    def update_frame(self) -> None:
        """Update camera frame with face detection."""
        if not self.camera:
            return
            
        ret, frame = self.camera.read()
        if not ret or frame is None:
            return

        # Convert BGR to RGB for face recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Use OpenCV's built-in face detection with improved parameters
        try:
            # Try to load the cascade file
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            # Check if cascade loaded successfully
            if face_cascade.empty():
                # In EXE, the cascade file might not be found, try alternative paths
                if getattr(sys, 'frozen', False):
                    # Try to find cascade file in the bundle
                    exe_dir = os.path.dirname(sys.executable)
                    alt_paths = [
                        os.path.join(exe_dir, 'haarcascade_frontalface_default.xml'),
                        os.path.join(exe_dir, 'opencv', 'haarcascade_frontalface_default.xml'),
                    ]
                    for alt_path in alt_paths:
                        if os.path.exists(alt_path):
                            face_cascade = cv2.CascadeClassifier(alt_path)
                            if not face_cascade.empty():
                                break
                
                if face_cascade.empty():
                    # If still empty, skip face detection
                    self.face_locations = []
                    return
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.face_locations = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.05,  # More sensitive scaling
                minNeighbors=5,    # Better detection
                minSize=(50, 50),  # Minimum face size
                maxSize=(300, 300) # Maximum face size
            )
        except Exception as e:
            # If face detection fails, continue without it
            self.face_locations = []
            print(f"Face detection error: {e}")
        
        # Draw positioning guides
        self._draw_positioning_guides(frame)
        
        # Draw rectangles around faces with color coding
        for (x, y, w, h) in self.face_locations:
            # Calculate face metrics
            frame_height, frame_width = frame.shape[:2]
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            frame_center_x = frame_width // 2
            frame_center_y = frame_height // 2
            
            # Calculate offset and size
            offset_x = abs(face_center_x - frame_center_x)
            offset_y = abs(face_center_y - frame_center_y)
            total_offset = (offset_x + offset_y) // 2
            
            face_area = w * h
            frame_area = frame_width * frame_height
            face_percentage = (face_area / frame_area) * 100
            
            # Color code based on quality
            is_centered = total_offset < 50
            is_good_size = 15 <= face_percentage <= 35
            
            if is_centered and is_good_size:
                color = (0, 255, 0)  # Green - optimal
                thickness = 3
                status_text = "PERFECT"
            elif is_centered or is_good_size:
                color = (0, 255, 255)  # Yellow - needs adjustment
                thickness = 2
                status_text = "GOOD"
            else:
                color = (0, 0, 255)  # Red - needs major adjustment
                thickness = 2
                status_text = "ADJUST"
                
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
            cv2.putText(frame, status_text, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Add real-time face percentage
            percentage_text = f"{face_percentage:.1f}%"
            cv2.putText(frame, percentage_text, (x, y + h + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Add face center dot
            cv2.circle(frame, (face_center_x, face_center_y), 5, color, -1)
        
        # Add progress bar for face size (if faces detected)
        if len(self.face_locations) > 0:
            # Get the largest face for progress calculation
            largest_face = max(self.face_locations, key=lambda x: x[2] * x[3])
            x, y, w, h = largest_face
            face_area = w * h
            frame_area = frame.shape[0] * frame.shape[1]
            face_percentage = (face_area / frame_area) * 100
            self._draw_face_size_progress(frame, face_percentage, frame.shape[1], frame.shape[0])
        
        # Update face detection info
        face_count = len(self.face_locations)
        if face_count > 0:
            self.face_info_label.setText(f"Face Detection: {face_count} face(s) detected")
            self.face_info_label.setStyleSheet("color: green; margin: 5px 0;")
        else:
            self.face_info_label.setText("Face Detection: No faces detected")
            self.face_info_label.setStyleSheet("color: red; margin: 5px 0;")

        # Convert frame for display
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_RGB888).rgbSwapped()
        
        # Scale image to fit label
        pixmap = QtGui.QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.camera_label.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        self.camera_label.setPixmap(scaled_pixmap)

        # Record video if active
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)

    def capture_photo(self) -> None:
        """Capture a photo and perform face detection."""
        if not self.camera or len(self.face_locations) == 0:
            QtWidgets.QMessageBox.warning(self, "No Face", "No face detected. Please ensure your face is visible in the camera.")
            return

        ret, frame = self.camera.read()
        if not ret:
            return

        # Convert to QPixmap for display
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QtGui.QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.photo_preview.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        self.photo_preview.setPixmap(scaled_pixmap)
        
        # Store captured photo
        self.captured_photo = {
            'image': frame,
            'face_location': self.face_locations[0] if len(self.face_locations) > 0 else None
        }
        
        # Perform face analysis
        self.analyze_face()
        
        self.save_image_btn.setEnabled(True)
        self.status_label.setText("Status: Photo captured successfully")

    def analyze_face(self) -> None:
        """Analyze captured face and display results with actionable recommendations."""
        results = []
        results.append("=== Face Detection Analysis ===")
        
        # Basic face quality checks
        if len(self.face_locations) > 0:
            x, y, w, h = self.face_locations[0]
            results.append(f"Face location: x={x}, y={y}, width={w}, height={h}")
            results.append(f"Face size: {w}x{h} pixels")
            
            # Check if face is centered (using actual frame dimensions)
            frame_width = 640  # Current camera resolution
            frame_height = 480
            frame_center_x = frame_width // 2
            frame_center_y = frame_height // 2
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            
            # Calculate offset from center
            offset_x = abs(face_center_x - frame_center_x)
            offset_y = abs(face_center_y - frame_center_y)
            total_offset = (offset_x + offset_y) // 2
            
            results.append(f"Face center offset: {total_offset} pixels")
            
            # Enhanced centering analysis
            if total_offset < 30:
                results.append("✅ Face is perfectly centered")
            elif total_offset < 50:
                results.append("⚠️ Face is slightly off-center")
            else:
                results.append("❌ Face is significantly off-center")
                
            # Check face size relative to frame
            face_area = w * h
            frame_area = frame_width * frame_height
            face_percentage = (face_area / frame_area) * 100
            results.append(f"Face occupies {face_percentage:.1f}% of frame")
            
            # Enhanced size analysis
            if 20 <= face_percentage <= 30:
                results.append("✅ Face size is optimal for passport photo")
            elif 15 <= face_percentage < 20:
                results.append("⚠️ Face size is acceptable but could be larger")
            elif 30 < face_percentage <= 35:
                results.append("⚠️ Face size is acceptable but could be smaller")
            elif face_percentage < 15:
                results.append("❌ Face is too small - move closer to camera")
            else:
                results.append("❌ Face is too large - move away from camera")
                
            # Overall quality assessment
            is_centered = total_offset < 50
            is_good_size = 15 <= face_percentage <= 35
            is_optimal = is_centered and is_good_size
            
            results.append("")
            results.append("=== Overall Assessment ===")
            if is_optimal:
                results.append("🎉 EXCELLENT: Photo meets all passport requirements!")
            elif is_centered and not is_good_size:
                results.append("⚠️ GOOD: Face is centered but size needs adjustment")
            elif is_good_size and not is_centered:
                results.append("⚠️ GOOD: Face size is good but positioning needs adjustment")
            else:
                results.append("❌ NEEDS IMPROVEMENT: Multiple issues detected")
                
            # Actionable recommendations
            results.append("")
            results.append("=== Recommendations ===")
            if not is_centered:
                if offset_x > offset_y:
                    if face_center_x < frame_center_x:
                        results.append("📝 Move your face to the RIGHT")
                    else:
                        results.append("📝 Move your face to the LEFT")
                else:
                    if face_center_y < frame_center_y:
                        results.append("📝 Move your face DOWN")
                    else:
                        results.append("📝 Move your face UP")
                        
            if face_percentage < 15:
                results.append("📝 Move CLOSER to the camera (about 6-12 inches)")
            elif face_percentage > 35:
                results.append("📝 Move AWAY from the camera (about 2-3 feet)")
                
            if not is_optimal:
                results.append("📝 Ensure good lighting on your face")
                results.append("📝 Look directly at the camera")
                results.append("📝 Maintain a neutral expression")
                results.append("📝 Capture another photo after adjustments")
        else:
            results.append("❌ No face detected in captured image")
            results.append("")
            results.append("=== Troubleshooting ===")
            results.append("📝 Ensure your face is clearly visible")
            results.append("📝 Check that lighting is adequate")
            results.append("📝 Make sure you're looking at the camera")
            results.append("📝 Try adjusting your position")
        
        results.append("")
        results.append("=== Passport Photo Requirements ===")
        results.append("• Face should be centered and clearly visible")
        results.append("• Neutral expression recommended")
        results.append("• Good lighting without shadows")
        results.append("• Face should occupy 15-35% of photo")
        results.append("• Look directly at camera")
        
        self.recognition_results.setText("\n".join(results))
        
    def _draw_positioning_guides(self, frame) -> None:
        """Draw positioning guides on the camera frame."""
        height, width = frame.shape[:2]
        
        # Draw center crosshair
        center_x, center_y = width // 2, height // 2
        cv2.line(frame, (center_x - 30, center_y), (center_x + 30, center_y), (255, 255, 255), 2)
        cv2.line(frame, (center_x, center_y - 30), (center_x, center_y + 30), (255, 255, 255), 2)
        
        # Draw optimal face area rectangle (15-35% of frame)
        optimal_size = int(width * 0.25)  # 25% of width
        optimal_x = center_x - optimal_size // 2
        optimal_y = center_y - optimal_size // 2
        
        # Draw optimal area with dashed lines
        cv2.rectangle(frame, (optimal_x, optimal_y), 
                     (optimal_x + optimal_size, optimal_y + optimal_size), 
                     (0, 255, 255), 1)
        
        # Add text labels
        cv2.putText(frame, "CENTER HERE", (center_x - 50, center_y - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "OPTIMAL FACE AREA", (optimal_x, optimal_y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Add distance guidance
        cv2.putText(frame, "TARGET: 20-30% of frame", (10, height - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, "Move closer if face < 15%", (10, height - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                   
    def _draw_face_size_progress(self, frame, face_percentage, width, height) -> None:
        """Draw a progress bar showing face size relative to requirements."""
        # Progress bar dimensions
        bar_width = 200
        bar_height = 20
        bar_x = width - bar_width - 10
        bar_y = 10
        
        # Draw background
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Calculate progress (15-35% range)
        min_percent = 15
        max_percent = 35
        if face_percentage < min_percent:
            progress = 0
        elif face_percentage > max_percent:
            progress = 1
        else:
            progress = (face_percentage - min_percent) / (max_percent - min_percent)
            
        # Draw progress
        progress_width = int(bar_width * progress)
        if progress_width > 0:
            color = (0, 255, 0) if 0.3 <= progress <= 0.7 else (0, 255, 255)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), color, -1)
        
        # Add labels
        cv2.putText(frame, "Face Size", (bar_x, bar_y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"{face_percentage:.1f}%", (bar_x + bar_width + 10, bar_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    def start_video_recording(self) -> None:
        """Start video recording."""
        if not self.camera:
            return
            
        # Initialize video writer in info folder
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_filename = f"passport_video_{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.avi"
        video_path = self.info_dir / video_filename
        self.video_writer = cv2.VideoWriter(str(video_path), fourcc, 20.0, (640, 480))
        self.is_recording = True
        
        self.start_video_btn.setEnabled(False)
        self.stop_video_btn.setEnabled(True)
        self.status_label.setText("Status: Recording video...")

    def stop_video_recording(self) -> None:
        """Stop video recording."""
        self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            
        self.start_video_btn.setEnabled(True)
        self.stop_video_btn.setEnabled(False)
        self.status_label.setText("Status: Video recording stopped")

    def save_image_data(self) -> None:
        """Save captured image data to CSV."""
        if not self.captured_photo:
            QtWidgets.QMessageBox.warning(self, "No Photo", "No photo captured. Please capture a photo first.")
            return

        # Save image to file in info folder
        image_filename = f"passport_photo_{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.jpg"
        image_path = self.info_dir / image_filename
        cv2.imwrite(str(image_path), self.captured_photo['image'])
        
        # Save face detection data in info folder
        detection_filename = f"face_detection_{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.json"
        detection_path = self.info_dir / detection_filename
        detection_data = {
            'face_location': self.captured_photo['face_location'].tolist() if self.captured_photo['face_location'] is not None else None,
            'timestamp': QtCore.QDateTime.currentDateTime().toString(),
            'image_filename': image_filename
        }
        
        with open(detection_path, 'w') as f:
            json.dump(detection_data, f, indent=2)
        
        QtWidgets.QMessageBox.information(self, "Success", 
            f"Image data saved successfully to info folder!\n\n"
            f"Photo: {image_path}\n"
            f"Detection: {detection_path}")


class ServiceTab(QtWidgets.QWidget):
    """Service tab for document upload, management, and verification."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.uploaded_files = {}
        # Use proper data directory for both source and EXE
        if getattr(sys, 'frozen', False):
            # In EXE, use the directory where the executable is located
            self.documents_dir = Path(os.path.dirname(sys.executable)) / "documents"
        else:
            # In source, use the project root
            self.documents_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "documents"
        self.documents_dir.mkdir(exist_ok=True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QtWidgets.QLabel("Document Upload & Verification")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Document categories
        categories_layout = QtWidgets.QHBoxLayout()
        
        # Passport section
        passport_group = self._create_document_group("Passport", [
            "Passport (PDF/JPG/PNG)",
            "Passport Copy (PDF/JPG/PNG)",
            "Previous Passport (if applicable)"
        ])
        categories_layout.addWidget(passport_group)

        # Photograph section
        photo_group = self._create_document_group("Photograph", [
            "Passport Photo (JPG/PNG)",
            "Additional Photos (if required)"
        ])
        categories_layout.addWidget(photo_group)

        # Supporting documents section
        support_group = self._create_document_group("Supporting Documents", [
            "Visa Application Form (PDF)",
            "Travel Itinerary (PDF)",
            "Hotel Booking (PDF)",
            "Bank Statements (PDF)",
            "Employment Letter (PDF)",
            "Invitation Letter (PDF)",
            "Other Supporting Documents"
        ])
        categories_layout.addWidget(support_group)

        layout.addLayout(categories_layout)

        # File verification area
        verification_layout = QtWidgets.QVBoxLayout()
        
        verification_title = QtWidgets.QLabel("Document Verification")
        verification_title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
        verification_layout.addWidget(verification_title)

        # Verification results
        self.verification_results = QtWidgets.QTextEdit()
        self.verification_results.setMaximumHeight(150)
        self.verification_results.setPlaceholderText("Document verification results will appear here...")
        verification_layout.addWidget(self.verification_results)

        layout.addLayout(verification_layout)

        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.verify_all_btn = QtWidgets.QPushButton("Verify All Documents")
        self.verify_all_btn.clicked.connect(self.verify_all_documents)
        
        self.clear_all_btn = QtWidgets.QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_documents)
        
        self.save_docs_btn = QtWidgets.QPushButton("Save Document Data")
        self.save_docs_btn.clicked.connect(self.save_document_data)
        
        button_layout.addWidget(self.verify_all_btn)
        button_layout.addWidget(self.clear_all_btn)
        button_layout.addWidget(self.save_docs_btn)
        button_layout.addStretch(1)
        
        layout.addLayout(button_layout)

    def _create_document_group(self, title: str, document_types: list) -> QtWidgets.QGroupBox:
        """Create a document upload group for a specific category."""
        group = QtWidgets.QGroupBox(title)
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #ccc; border-radius: 5px; margin: 5px; padding-top: 10px; }")
        
        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(5)

        for doc_type in document_types:
            doc_layout = QtWidgets.QHBoxLayout()
            
            # Document type label
            label = QtWidgets.QLabel(doc_type)
            label.setStyleSheet("font-size: 10px; color: #666;")
            label.setWordWrap(True)
            doc_layout.addWidget(label, 1)
            
            # Upload button
            upload_btn = QtWidgets.QPushButton("Upload")
            upload_btn.setFixedSize(60, 25)
            upload_btn.setStyleSheet("font-size: 10px;")
            upload_btn.clicked.connect(lambda checked, dt=doc_type: self.upload_document(dt))
            doc_layout.addWidget(upload_btn)
            
            # Status indicator
            status_label = QtWidgets.QLabel("❌")
            status_label.setFixedSize(20, 20)
            status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            doc_layout.addWidget(status_label)
            
            layout.addLayout(doc_layout)
            
            # Store references for status updates
            if not hasattr(self, 'document_status'):
                self.document_status = {}
            self.document_status[doc_type] = status_label

        return group

    def upload_document(self, document_type: str) -> None:
        """Upload a document and perform verification."""
        try:
            # Check if client email is available
            client_email = self._get_current_client_email()
            if not client_email:
                QtWidgets.QMessageBox.warning(self, "No Client Email", 
                    "Please enter your email address in the Account tab before uploading documents.")
                return
            
            file_dialog = QtWidgets.QFileDialog(self)
            file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
            file_dialog.setNameFilter("All Supported (*.pdf *.jpg *.jpeg *.png);;PDF Files (*.pdf);;Image Files (*.jpg *.jpeg *.png)")
            file_dialog.setWindowTitle(f"Select {document_type}")
            
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    file_path = selected_files[0]
                    self.process_uploaded_file(file_path, document_type)
                else:
                    QtWidgets.QMessageBox.information(self, "No File Selected", "No file was selected.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Upload Error", f"Failed to open file dialog: {str(e)}")

    def process_uploaded_file(self, file_path: str, document_type: str) -> None:
        """Process uploaded file and perform verification."""
        try:
            # Validate input file path
            if not file_path or not file_path.strip():
                QtWidgets.QMessageBox.warning(self, "Invalid File", "No file selected.")
                return
                
            file_path = Path(file_path)
            
            # Check if source file exists
            if not file_path.exists():
                QtWidgets.QMessageBox.warning(self, "File Not Found", f"The selected file does not exist:\n{file_path}")
                return
                
            # Check if source file is readable
            if not file_path.is_file():
                QtWidgets.QMessageBox.warning(self, "Invalid File", f"The selected path is not a file:\n{file_path}")
                return
                
            # Copy file to documents directory
            client_email = self._get_current_client_email()
            if not client_email:
                QtWidgets.QMessageBox.warning(self, "No Client", "Please set email in Account tab first.")
                return
                
            # Ensure documents directory exists
            if not self.documents_dir.exists():
                self.documents_dir.mkdir(parents=True, exist_ok=True)
                
            # Create client-specific directory
            client_dir = self.documents_dir / client_email.replace("@", "_").replace(".", "_")
            client_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            timestamp = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
            file_extension = file_path.suffix
            new_filename = f"{document_type.replace(' ', '_')}_{timestamp}{file_extension}"
            destination = client_dir / new_filename
            
            # Copy file with proper error handling
            import shutil
            
            # Debug information
            print(f"Source file: {file_path}")
            print(f"Destination: {destination}")
            print(f"Client email: {client_email}")
            print(f"Client dir: {client_dir}")
            
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(str(file_path), str(destination))
            
            # Verify the copy was successful
            if not destination.exists():
                raise FileNotFoundError(f"Failed to copy file to {destination}")
            
            # Verify document
            verification_result = self.verify_document(destination, document_type)
            
            # Store file info
            self.uploaded_files[document_type] = {
                'original_path': str(file_path),
                'stored_path': str(destination),
                'filename': new_filename,
                'size': destination.stat().st_size,
                'verification': verification_result
            }
            
            # Update status indicator
            if verification_result['valid']:
                self.document_status[document_type].setText("✅")
                self.document_status[document_type].setStyleSheet("color: green;")
            else:
                self.document_status[document_type].setText("⚠️")
                self.document_status[document_type].setStyleSheet("color: orange;")
            
            # Update verification results
            self.update_verification_display()
            
        except FileNotFoundError as e:
            QtWidgets.QMessageBox.critical(self, "Upload Error", 
                f"File not found: {str(e)}\n\nPlease check that the file exists and you have permission to access it.")
        except PermissionError as e:
            QtWidgets.QMessageBox.critical(self, "Upload Error", 
                f"Permission denied: {str(e)}\n\nPlease check that you have permission to access the file and destination folder.")
        except OSError as e:
            QtWidgets.QMessageBox.critical(self, "Upload Error", 
                f"System error: {str(e)}\n\nPlease check the file path and try again.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Upload Error", 
                f"Unexpected error: {str(e)}\n\nPlease try again or contact support.")

    def verify_document(self, file_path: Path, document_type: str) -> dict:
        """Verify document format, size, and quality."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_size': file_path.stat().st_size,
            'file_type': file_path.suffix.lower()
        }
        
        # File size check (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if result['file_size'] > max_size:
            result['valid'] = False
            result['errors'].append(f"File size ({result['file_size'] / 1024 / 1024:.1f}MB) exceeds 10MB limit")
        
        # File format check
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        if result['file_type'] not in allowed_extensions:
            result['valid'] = False
            result['errors'].append(f"File format {result['file_type']} not supported. Allowed: {', '.join(allowed_extensions)}")
        
        # Document-specific checks
        if 'passport' in document_type.lower():
            if result['file_type'] not in ['.pdf', '.jpg', '.jpeg', '.png']:
                result['valid'] = False
                result['errors'].append("Passport documents must be PDF or image format")
        
        if 'photo' in document_type.lower():
            if result['file_type'] not in ['.jpg', '.jpeg', '.png']:
                result['valid'] = False
                result['errors'].append("Photos must be JPG or PNG format")
            
            # Image quality check
            if result['file_type'] in ['.jpg', '.jpeg', '.png']:
                try:
                    img = cv2.imread(str(file_path))
                    if img is not None:
                        height, width = img.shape[:2]
                        result['image_dimensions'] = f"{width}x{height}"
                        
                        # Check minimum resolution for passport photos
                        if width < 300 or height < 300:
                            result['warnings'].append("Image resolution may be too low for passport photo")
                        
                        # Check aspect ratio for passport photos
                        aspect_ratio = width / height
                        if not (0.7 <= aspect_ratio <= 1.3):
                            result['warnings'].append("Image aspect ratio may not be suitable for passport photo")
                    else:
                        result['warnings'].append("Could not read image file")
                except Exception as e:
                    result['warnings'].append(f"Image verification failed: {str(e)}")
        
        if 'pdf' in document_type.lower() and result['file_type'] != '.pdf':
            result['warnings'].append("PDF documents are recommended for official forms")
        
        return result

    def update_verification_display(self) -> None:
        """Update the verification results display."""
        results = []
        results.append("=== Document Verification Results ===")
        
        total_docs = len(self.uploaded_files)
        valid_docs = sum(1 for doc in self.uploaded_files.values() if doc['verification']['valid'])
        
        results.append(f"Total Documents: {total_docs}")
        results.append(f"Valid Documents: {valid_docs}")
        results.append(f"Invalid Documents: {total_docs - valid_docs}")
        results.append("")
        
        for doc_type, doc_info in self.uploaded_files.items():
            results.append(f"📄 {doc_type}:")
            results.append(f"   File: {doc_info['filename']}")
            results.append(f"   Size: {doc_info['size'] / 1024:.1f} KB")
            
            verification = doc_info['verification']
            if verification['valid']:
                results.append("   Status: ✅ Valid")
            else:
                results.append("   Status: ❌ Invalid")
                for error in verification['errors']:
                    results.append(f"   Error: {error}")
            
            for warning in verification.get('warnings', []):
                results.append(f"   Warning: {warning}")
            
            if 'image_dimensions' in verification:
                results.append(f"   Dimensions: {verification['image_dimensions']}")
            
            results.append("")
        
        # VFS Global requirements
        results.append("=== VFS Global Guinea-Bissau Requirements ===")
        results.append("• All documents must be clear and legible")
        results.append("• Passport photos: 35x45mm, white background")
        results.append("• File size limit: 10MB per document")
        results.append("• Supported formats: PDF, JPG, PNG")
        results.append("• Documents must be in English or Portuguese")
        
        self.verification_results.setText("\n".join(results))

    def verify_all_documents(self) -> None:
        """Verify all uploaded documents."""
        if not self.uploaded_files:
            QtWidgets.QMessageBox.information(self, "No Documents", "No documents uploaded to verify.")
            return
        
        self.update_verification_display()
        
        valid_count = sum(1 for doc in self.uploaded_files.values() if doc['verification']['valid'])
        total_count = len(self.uploaded_files)
        
        if valid_count == total_count:
            QtWidgets.QMessageBox.information(self, "Verification Complete", 
                f"All {total_count} documents are valid and ready for submission!")
        else:
            QtWidgets.QMessageBox.warning(self, "Verification Issues", 
                f"{total_count - valid_count} documents have issues. Please review the verification results.")

    def clear_all_documents(self) -> None:
        """Clear all uploaded documents."""
        reply = QtWidgets.QMessageBox.question(self, "Clear Documents", 
            "Are you sure you want to clear all uploaded documents?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.uploaded_files.clear()
            
            # Reset status indicators
            for status_label in self.document_status.values():
                status_label.setText("❌")
                status_label.setStyleSheet("color: red;")
            
            self.verification_results.clear()
            QtWidgets.QMessageBox.information(self, "Cleared", "All documents have been cleared.")

    def save_document_data(self) -> None:
        """Save document data to CSV."""
        if not self.uploaded_files:
            QtWidgets.QMessageBox.warning(self, "No Documents", "No documents to save.")
            return
        
        client_email = self._get_current_client_email()
        if not client_email:
            QtWidgets.QMessageBox.warning(self, "No Client", "Please set email in Account tab first.")
            return
        
        # Save document metadata
        doc_metadata = {
            'client_email': client_email,
            'upload_timestamp': QtCore.QDateTime.currentDateTime().toString(),
            'documents': self.uploaded_files
        }
        
        metadata_filename = f"document_metadata_{client_email.replace('@', '_').replace('.', '_')}_{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.json"
        
        try:
            with open(metadata_filename, 'w') as f:
                json.dump(doc_metadata, f, indent=2, default=str)
            
            QtWidgets.QMessageBox.information(self, "Success", 
                f"Document data saved successfully!\n\n"
                f"Metadata: {metadata_filename}\n"
                f"Documents: {len(self.uploaded_files)} files")
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save Error", f"Failed to save document data: {str(e)}")

    def _get_current_client_email(self) -> str:
        """Get current client email from Account tab."""
        # This will be connected to the main window to access account tab
        return getattr(self, '_main_window', None) and self._main_window.account_tab.email.text().strip() or ""
    
    def set_main_window(self, main_window) -> None:
        """Set reference to main window for accessing account data."""
        self._main_window = main_window


class ReviewPaymentTab(QtWidgets.QWidget):
    """Review & Payment tab for final booking confirmation and payment processing."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.booking_data = {}
        self.payment_status = "pending"
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QtWidgets.QLabel("Review & Payment")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Create scrollable content
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)

        # Reservation Summary Section
        summary_group = self._create_summary_section()
        scroll_layout.addWidget(summary_group)

        # Payment Section
        payment_group = self._create_payment_section()
        scroll_layout.addWidget(payment_group)

        # Confirmation Section
        confirmation_group = self._create_confirmation_section()
        scroll_layout.addWidget(confirmation_group)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.refresh_btn = QtWidgets.QPushButton("Refresh Summary")
        self.refresh_btn.clicked.connect(self.refresh_summary)
        
        self.process_payment_btn = QtWidgets.QPushButton("Process Payment")
        self.process_payment_btn.clicked.connect(self.process_payment)
        self.process_payment_btn.setEnabled(False)
        
        self.confirm_booking_btn = QtWidgets.QPushButton("Confirm Booking")
        self.confirm_booking_btn.clicked.connect(self.confirm_booking)
        self.confirm_booking_btn.setEnabled(False)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.process_payment_btn)
        button_layout.addWidget(self.confirm_booking_btn)
        button_layout.addStretch(1)
        
        layout.addLayout(button_layout)

    def _create_summary_section(self) -> QtWidgets.QGroupBox:
        """Create reservation summary section."""
        group = QtWidgets.QGroupBox("Reservation Summary")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #ccc; border-radius: 5px; margin: 5px; padding-top: 10px; }")
        
        layout = QtWidgets.QVBoxLayout(group)
        
        # Summary display
        self.summary_display = QtWidgets.QTextEdit()
        self.summary_display.setMaximumHeight(200)
        self.summary_display.setReadOnly(True)
        self.summary_display.setPlaceholderText("Click 'Refresh Summary' to load reservation details...")
        layout.addWidget(self.summary_display)
        
        return group

    def _create_payment_section(self) -> QtWidgets.QGroupBox:
        """Create payment processing section."""
        group = QtWidgets.QGroupBox("Payment Information")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #ccc; border-radius: 5px; margin: 5px; padding-top: 10px; }")
        
        layout = QtWidgets.QVBoxLayout(group)
        
        # Payment method selection
        payment_method_layout = QtWidgets.QHBoxLayout()
        payment_method_layout.addWidget(QtWidgets.QLabel("Payment Method:"))
        
        self.payment_method = QtWidgets.QComboBox()
        self.payment_method.addItems([
            "Credit Card (Visa/MasterCard)",
            "Debit Card",
            "Bank Transfer",
            "PayPal",
            "VFS Global Payment Gateway"
        ])
        payment_method_layout.addWidget(self.payment_method)
        layout.addLayout(payment_method_layout)
        
        # Payment amount
        amount_layout = QtWidgets.QHBoxLayout()
        amount_layout.addWidget(QtWidgets.QLabel("Total Amount:"))
        
        self.payment_amount = QtWidgets.QLabel("€85.00")  # VFS Guinea-Bissau visa fee
        self.payment_amount.setStyleSheet("font-weight: bold; color: #2c5aa0; font-size: 14px;")
        amount_layout.addWidget(self.payment_amount)
        amount_layout.addStretch(1)
        layout.addLayout(amount_layout)
        
        # Payment status
        status_layout = QtWidgets.QHBoxLayout()
        status_layout.addWidget(QtWidgets.QLabel("Payment Status:"))
        
        self.payment_status_label = QtWidgets.QLabel("Pending")
        self.payment_status_label.setStyleSheet("color: orange; font-weight: bold;")
        status_layout.addWidget(self.payment_status_label)
        status_layout.addStretch(1)
        layout.addLayout(status_layout)
        
        # Payment details (hidden initially)
        self.payment_details = QtWidgets.QWidget()
        payment_details_layout = QtWidgets.QFormLayout(self.payment_details)
        
        self.card_number = QtWidgets.QLineEdit()
        self.card_number.setPlaceholderText("1234 5678 9012 3456")
        self.card_number.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        
        self.expiry_date = QtWidgets.QLineEdit()
        self.expiry_date.setPlaceholderText("MM/YY")
        
        self.cvv = QtWidgets.QLineEdit()
        self.cvv.setPlaceholderText("123")
        self.cvv.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.cvv.setMaxLength(4)
        
        self.cardholder_name = QtWidgets.QLineEdit()
        self.cardholder_name.setPlaceholderText("Cardholder Name")
        
        payment_details_layout.addRow("Card Number:", self.card_number)
        payment_details_layout.addRow("Expiry Date:", self.expiry_date)
        payment_details_layout.addRow("CVV:", self.cvv)
        payment_details_layout.addRow("Cardholder Name:", self.cardholder_name)
        
        self.payment_details.setVisible(False)
        layout.addWidget(self.payment_details)
        
        # Show/hide payment details
        self.payment_method.currentTextChanged.connect(self._on_payment_method_changed)
        
        return group

    def _create_confirmation_section(self) -> QtWidgets.QGroupBox:
        """Create booking confirmation section."""
        group = QtWidgets.QGroupBox("Booking Confirmation")
        group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #ccc; border-radius: 5px; margin: 5px; padding-top: 10px; }")
        
        layout = QtWidgets.QVBoxLayout(group)
        
        # Confirmation details
        self.confirmation_display = QtWidgets.QTextEdit()
        self.confirmation_display.setMaximumHeight(150)
        self.confirmation_display.setReadOnly(True)
        self.confirmation_display.setPlaceholderText("Booking confirmation will appear here after successful payment...")
        layout.addWidget(self.confirmation_display)
        
        # Booking reference
        ref_layout = QtWidgets.QHBoxLayout()
        ref_layout.addWidget(QtWidgets.QLabel("Booking Reference:"))
        
        self.booking_reference = QtWidgets.QLabel("Not Generated")
        self.booking_reference.setStyleSheet("font-weight: bold; color: #2c5aa0;")
        ref_layout.addWidget(self.booking_reference)
        ref_layout.addStretch(1)
        layout.addLayout(ref_layout)
        
        return group

    def _on_payment_method_changed(self, method: str) -> None:
        """Show/hide payment details based on selected method."""
        if "Card" in method:
            self.payment_details.setVisible(True)
        else:
            self.payment_details.setVisible(False)

    def refresh_summary(self) -> None:
        """Refresh the reservation summary with current data."""
        try:
            # Get data from all tabs
            account_data = self._get_account_data()
            order_data = self._get_order_data()
            application_data = self._get_application_data()
            service_data = self._get_service_data()
            
            # Build summary
            summary = []
            summary.append("=== VFS GLOBAL GUINEA-BISSAU VISA APPLICATION ===")
            summary.append(f"Generated: {QtCore.QDateTime.currentDateTime().toString()}")
            summary.append("")
            
            # Account Information
            summary.append("📋 ACCOUNT INFORMATION:")
            summary.append(f"   Name: {account_data.get('first_name', 'N/A')} {account_data.get('last_name', 'N/A')}")
            summary.append(f"   Email: {account_data.get('email', 'N/A')}")
            summary.append(f"   Mobile: {account_data.get('mobile_country_code', 'N/A')} {account_data.get('mobile_number', 'N/A')}")
            summary.append("")
            
            # Order Information
            summary.append("🎫 VISA APPLICATION DETAILS:")
            summary.append(f"   Application Center: {order_data.get('application_center', 'N/A')}")
            summary.append(f"   Service Type: {order_data.get('service_center', 'N/A')}")
            summary.append(f"   Trip Purpose: {order_data.get('trip_reason', 'N/A')}")
            summary.append("")
            
            # Application Information
            summary.append("📄 PERSONAL DETAILS:")
            summary.append(f"   Gender: {application_data.get('gender', 'N/A')}")
            summary.append(f"   Date of Birth: {application_data.get('date_of_birth', 'N/A')}")
            summary.append(f"   Nationality: {application_data.get('current_nationality', 'N/A')}")
            summary.append(f"   Passport Number: {application_data.get('passport_number', 'N/A')}")
            summary.append(f"   Passport Expiry: {application_data.get('passport_expiry', 'N/A')}")
            summary.append("")
            
            # Document Status
            summary.append("📁 DOCUMENT STATUS:")
            doc_count = len(service_data.get('documents', {}))
            valid_docs = sum(1 for doc in service_data.get('documents', {}).values() if doc.get('verification', {}).get('valid', False))
            summary.append(f"   Total Documents: {doc_count}")
            summary.append(f"   Valid Documents: {valid_docs}")
            summary.append(f"   Document Status: {'✅ Complete' if doc_count > 0 and valid_docs == doc_count else '⚠️ Incomplete'}")
            summary.append("")
            
            # Payment Information
            summary.append("💳 PAYMENT INFORMATION:")
            summary.append(f"   Visa Fee: €85.00")
            summary.append(f"   Service Fee: €0.00")
            summary.append(f"   Total Amount: €85.00")
            summary.append(f"   Payment Status: {self.payment_status.title()}")
            summary.append("")
            
            # Requirements Checklist
            summary.append("✅ REQUIREMENTS CHECKLIST:")
            summary.append(f"   Account Information: {'✅' if account_data.get('email') else '❌'}")
            summary.append(f"   Visa Application: {'✅' if order_data.get('service_center') else '❌'}")
            summary.append(f"   Personal Details: {'✅' if application_data.get('passport_number') else '❌'}")
            summary.append(f"   Documents Uploaded: {'✅' if doc_count > 0 else '❌'}")
            summary.append(f"   Payment Ready: {'✅' if self.payment_status == 'completed' else '❌'}")
            
            self.summary_display.setText("\n".join(summary))
            
            # Enable payment button if all requirements met
            all_complete = (account_data.get('email') and 
                          order_data.get('service_center') and 
                          application_data.get('passport_number') and 
                          doc_count > 0)
            
            self.process_payment_btn.setEnabled(all_complete)
            
            if not all_complete:
                QtWidgets.QMessageBox.information(self, "Incomplete Application", 
                    "Please complete all required sections before proceeding to payment.")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to refresh summary: {str(e)}")

    def process_payment(self) -> None:
        """Process payment for the visa application."""
        # Validate payment details if card payment
        if "Card" in self.payment_method.currentText():
            if not self._validate_payment_details():
                return
        
        # Simulate payment processing
        self.payment_status_label.setText("Processing...")
        self.payment_status_label.setStyleSheet("color: blue; font-weight: bold;")
        self.process_payment_btn.setEnabled(False)
        
        # Simulate payment processing delay
        QtCore.QTimer.singleShot(3000, self._complete_payment)

    def _validate_payment_details(self) -> bool:
        """Validate payment form details."""
        if not self.card_number.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Please enter card number.")
            return False
        
        if not self.expiry_date.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Please enter expiry date.")
            return False
        
        if not self.cvv.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Please enter CVV.")
            return False
        
        if not self.cardholder_name.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Please enter cardholder name.")
            return False
        
        return True

    def _complete_payment(self) -> None:
        """Complete payment processing."""
        self.payment_status = "completed"
        self.payment_status_label.setText("Completed")
        self.payment_status_label.setStyleSheet("color: green; font-weight: bold;")
        
        self.confirm_booking_btn.setEnabled(True)
        
        QtWidgets.QMessageBox.information(self, "Payment Successful", 
            "Payment has been processed successfully!\n\nYou can now confirm your booking.")

    def confirm_booking(self) -> None:
        """Confirm the booking and generate confirmation."""
        if self.payment_status != "completed":
            QtWidgets.QMessageBox.warning(self, "Payment Required", "Please complete payment first.")
            return
        
        # Generate booking reference
        booking_ref = f"VFS-GNB-{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd')}-{QtCore.QDateTime.currentDateTime().toString('hhmmss')}"
        self.booking_reference.setText(booking_ref)
        
        # Generate confirmation
        confirmation = []
        confirmation.append("🎉 BOOKING CONFIRMED!")
        confirmation.append("")
        confirmation.append("Your Guinea-Bissau visa application has been successfully submitted.")
        confirmation.append("")
        confirmation.append("📋 BOOKING DETAILS:")
        confirmation.append(f"   Booking Reference: {booking_ref}")
        confirmation.append(f"   Application Date: {QtCore.QDateTime.currentDateTime().toString()}")
        confirmation.append(f"   Visa Type: {self._get_order_data().get('service_center', 'N/A')}")
        confirmation.append(f"   Total Paid: €85.00")
        confirmation.append("")
        confirmation.append("📧 NEXT STEPS:")
        confirmation.append("   1. You will receive a confirmation email shortly")
        confirmation.append("   2. Check your application status online")
        confirmation.append("   3. Prepare for your appointment (if required)")
        confirmation.append("   4. Keep this booking reference for your records")
        confirmation.append("")
        confirmation.append("📞 SUPPORT:")
        confirmation.append("   VFS Global Guinea-Bissau")
        confirmation.append("   Email: info@vfsglobal.com")
        confirmation.append("   Phone: +245 XXX XXX XXX")
        
        self.confirmation_display.setText("\n".join(confirmation))
        
        # Save booking data
        self._save_booking_data(booking_ref)
        
        QtWidgets.QMessageBox.information(self, "Booking Confirmed", 
            f"Your booking has been confirmed!\n\nBooking Reference: {booking_ref}\n\nPlease save this reference number.")

    def _get_account_data(self) -> dict:
        """Get account data from Account tab."""
        if hasattr(self, '_main_window'):
            return {
                'first_name': self._main_window.account_tab.first_name.text(),
                'last_name': self._main_window.account_tab.last_name.text(),
                'email': self._main_window.account_tab.email.text(),
                'mobile_country_code': self._main_window.account_tab.country_code.currentData(),
                'mobile_number': self._main_window.account_tab.mobile_number.text()
            }
        return {}

    def _get_order_data(self) -> dict:
        """Get order data from Order tab."""
        if hasattr(self, '_main_window'):
            return {
                'application_center': self._main_window.order_tab.application_center.currentText(),
                'service_center': self._main_window.order_tab.service_center.currentText(),
                'trip_reason': self._main_window.order_tab.trip_reason.currentText()
            }
        return {}

    def _get_application_data(self) -> dict:
        """Get application data from Application tab."""
        if hasattr(self, '_main_window'):
            return {
                'gender': self._main_window.application_tab.gender.currentText(),
                'date_of_birth': self._main_window.application_tab.date_of_birth.date().toString("dd/MM/yyyy"),
                'current_nationality': self._main_window.application_tab.current_nationality.currentText(),
                'passport_number': self._main_window.application_tab.passport_number.text(),
                'passport_expiry': self._main_window.application_tab.passport_expiry.date().toString("dd/MM/yyyy")
            }
        return {}

    def _get_service_data(self) -> dict:
        """Get service data from Service tab."""
        if hasattr(self, '_main_window'):
            return {
                'documents': self._main_window.service_tab.uploaded_files
            }
        return {}

    def _save_booking_data(self, booking_ref: str) -> None:
        """Save booking data to file."""
        booking_data = {
            'booking_reference': booking_ref,
            'booking_date': QtCore.QDateTime.currentDateTime().toString(),
            'account_data': self._get_account_data(),
            'order_data': self._get_order_data(),
            'application_data': self._get_application_data(),
            'service_data': self._get_service_data(),
            'payment_status': self.payment_status,
            'payment_amount': '€85.00'
        }
        
        filename = f"booking_confirmation_{booking_ref}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(booking_data, f, indent=2, default=str)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Save Warning", f"Could not save booking data: {str(e)}")

    def set_main_window(self, main_window) -> None:
        """Set reference to main window for accessing tab data."""
        self._main_window = main_window


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Guinea-Bissau VFS Booking Helper")
        self.resize(900, 640)
        self._worker_thread: Optional[QtCore.QThread] = None
        self._build_ui()
        # CSV target path - use proper data directory for both source and EXE
        if getattr(sys, 'frozen', False):
            # In EXE, use the directory where the executable is located
            self._csv_path = os.path.join(os.path.dirname(sys.executable), "clients.csv")
        else:
            # In source, use the project root
            self._csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "clients.csv")

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(central)
        vbox.setContentsMargins(16, 12, 16, 16)
        vbox.setSpacing(10)

        # Top controls: URL, Start button, status light
        top = QtWidgets.QHBoxLayout()
        url_label = QtWidgets.QLabel("URL")
        url_label.setFixedWidth(40)
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("https://visa.vfsglobal.com/gnb/pt/prt/login")
        
        # Bot settings
        self.headless_checkbox = QtWidgets.QCheckBox("Headless")
        self.headless_checkbox.setChecked(True)
        self.headless_checkbox.setToolTip("Run browser in background")
        
        self.playwright_checkbox = QtWidgets.QCheckBox("Playwright")
        self.playwright_checkbox.setChecked(True)
        self.playwright_checkbox.setToolTip("Use Playwright (better for Cloudflare)")
        
        self.start_btn = QtWidgets.QPushButton("Start Bot")
        self.start_btn.setFixedWidth(100)
        self.status_light = StatusLight()
        self.status_light.set_green()  # default in screenshot

        top.addWidget(url_label)
        top.addWidget(self.url_input, 1)
        top.addWidget(self.headless_checkbox)
        top.addWidget(self.playwright_checkbox)
        top.addWidget(self.start_btn)
        top.addSpacing(8)
        top.addWidget(self.status_light)

        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        self.account_tab = AccountTab()
        self.order_tab = OrderTab()
        self.application_tab = ApplicationTab()
        self.image_tab = ImageTab()
        self.service_tab = ServiceTab()
        self.review_payment_tab = ReviewPaymentTab()
        self.tabs.addTab(self.account_tab, "account")
        self.tabs.addTab(self.order_tab, "Order")
        self.tabs.addTab(self.application_tab, "Application")
        self.tabs.addTab(self.image_tab, "image")
        self.tabs.addTab(self.service_tab, "Service")
        self.tabs.addTab(self.review_payment_tab, "Review & Payment")

        # Large placeholder area resembling screenshot
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        frame_layout = QtWidgets.QVBoxLayout(frame)
        frame_layout.addWidget(self.tabs)

        vbox.addLayout(top)
        vbox.addWidget(frame, 1)

        self.setCentralWidget(central)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.account_tab.register_btn.clicked.connect(self._on_register_clicked)
        self.order_tab.save_btn.clicked.connect(self._on_order_save_clicked)
        self.application_tab.save_btn.clicked.connect(self._on_application_save_clicked)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Connect ServiceTab and ReviewPaymentTab to main window for data access
        self.service_tab.set_main_window(self)
        self.review_payment_tab.set_main_window(self)

    # --- Bot placeholder wiring ---
    def _on_start_clicked(self) -> None:
        if self._worker_thread is None:
            self._start_worker()
        else:
            self._stop_worker()

    def _start_worker(self) -> None:
        self.status_light.set_green()
        self.start_btn.setText("stop")

        class BotWorker(QtCore.QObject):
            started = QtCore.pyqtSignal()
            errored = QtCore.pyqtSignal(str)
            finished = QtCore.pyqtSignal()
            status_updated = QtCore.pyqtSignal(str)
            availability_found = QtCore.pyqtSignal(object)  # AvailabilityStatus
            booking_completed = QtCore.pyqtSignal(object)   # BookingResult
            progress_updated = QtCore.pyqtSignal(int, int)  # current, total

            def __init__(self, headless: bool = True, use_playwright: bool = True, start_url: str = "") -> None:
                super().__init__()
                self._stop = False
                self.headless = headless
                self.use_playwright = use_playwright
                self.vfs_worker = None
                self.start_url = start_url

            @QtCore.pyqtSlot()
            def run(self) -> None:
                self.started.emit()
                try:
                    self.status_updated.emit("Starting VFS automation...")
                    
                    # Initialize VFS automation worker
                    self.vfs_worker = VFSBotWorker(
                        headless=self.headless,
                        use_playwright=self.use_playwright,
                        start_url=(self.start_url or None)
                    )
                    
                    # Connect signals with error handling
                    try:
                        self.vfs_worker.status_updated.connect(self.status_updated.emit)
                        self.vfs_worker.availability_found.connect(self.availability_found.emit)
                        self.vfs_worker.booking_completed.connect(self.booking_completed.emit)
                        self.vfs_worker.error_occurred.connect(self.errored.emit)
                        self.vfs_worker.progress_updated.connect(self.progress_updated.emit)
                    except Exception as e:
                        self.errored.emit(f"Signal connection error: {str(e)}")
                        return
                    
                    # Start VFS automation
                    try:
                        self.vfs_worker.start()
                        self.vfs_worker.wait()
                    except Exception as e:
                        self.errored.emit(f"VFS automation error: {str(e)}")
                        return
                    
                    self.finished.emit()
                except Exception as exc:
                    self.errored.emit(f"Worker error: {str(exc)}")

            def request_stop(self) -> None:
                self._stop = True
                if self.vfs_worker:
                    try:
                        self.vfs_worker.stop()
                    except Exception:
                        pass

        self._worker_thread = QtCore.QThread(self)
        start_url = (self.url_input.text() or "").strip()
        self._worker = BotWorker(
            headless=self.headless_checkbox.isChecked(), 
            use_playwright=self.playwright_checkbox.isChecked(),
            start_url=start_url
        )
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.errored.connect(self._on_worker_errored)
        self._worker.started.connect(lambda: self.status_light.set_green())
        self._worker.status_updated.connect(self._on_status_updated)
        self._worker.availability_found.connect(self._on_availability_found)
        self._worker.booking_completed.connect(self._on_booking_completed)
        self._worker.progress_updated.connect(self._on_progress_updated)
        self._worker_thread.start()

    def _stop_worker(self) -> None:
        if self._worker_thread is None:
            return
        try:
            self._worker.request_stop()  # type: ignore[attr-defined]
        except Exception:
            pass
        self._worker_thread.quit()
        self._worker_thread.wait(2000)
        self._worker_thread = None
        self.start_btn.setText("start")
        self.status_light.set_gray()

    def _on_worker_finished(self) -> None:
        self._stop_worker()

    def _on_worker_errored(self, _msg: str) -> None:
        self.status_light.set_yellow()
        try:
            # Surface the actual error to the user
            QtWidgets.QMessageBox.critical(self, "Automation Error", str(_msg) if _msg else "Unknown error")
        except Exception:
            pass
        self._stop_worker()
        
    def _on_status_updated(self, status: str) -> None:
        """Handle status updates from VFS automation."""
        # Update status in the URL input field or create a status label
        if hasattr(self, 'url_input'):
            self.url_input.setPlaceholderText(f"Status: {status}")
            
    def _on_availability_found(self, availability: AvailabilityStatus) -> None:
        """Handle availability detection."""
        self.status_light.set_green()
        QtWidgets.QMessageBox.information(
            self, 
            "Availability Found!", 
            f"VFS Global has {availability.slots_count} appointment slots available!\n\n"
            f"Next available date: {availability.next_available_date or 'Immediate'}\n"
            f"Starting booking process..."
        )
        
    def _on_booking_completed(self, result: BookingResult) -> None:
        """Handle booking completion."""
        if result.success:
            QtWidgets.QMessageBox.information(
                self,
                "Booking Successful!",
                f"Successfully booked appointment for {result.client_email}\n\n"
                f"Booking Reference: {result.booking_reference}\n"
                f"Timestamp: {result.timestamp}"
            )
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Booking Failed",
                f"Failed to book appointment for {result.client_email}\n\n"
                f"Error: {result.error_message}"
            )
            
    def _on_progress_updated(self, current: int, total: int) -> None:
        """Handle progress updates."""
        progress_text = f"Processing {current}/{total} clients..."
        if hasattr(self, 'url_input'):
            self.url_input.setPlaceholderText(progress_text)

    # --- Register handling ---
    def _collect_account_form(self) -> ClientRecord:
        date_str = self.account_tab.dob.date().toString("dd/MM/yyyy")
        return ClientRecord(
            first_name=self.account_tab.first_name.text().strip(),
            last_name=self.account_tab.last_name.text().strip(),
            date_of_birth=date_str,
            email=self.account_tab.email.text().strip(),
            password=self.account_tab.password.text(),
            mobile_country_code=self.account_tab.country_code.currentData() or "",
            mobile_number=self.account_tab.mobile_number.text().strip(),
        )

    def _on_register_clicked(self) -> None:
        record = self._collect_account_form()
        # Ensure directory exists
        try:
            existing = load_clients(self._csv_path)
        except FileNotFoundError:
            existing = []

        # Duplicate email check (case-insensitive)
        email_lower = record.email.lower()
        if any(c.email.lower() == email_lower for c in existing):
            QtWidgets.QMessageBox.warning(self, "Duplicate", "This email address already exists.")
            return

        existing.append(record)
        os.makedirs(os.path.dirname(self._csv_path), exist_ok=True) if os.path.dirname(self._csv_path) else None
        save_clients(self._csv_path, existing)
        QtWidgets.QMessageBox.information(self, "Success", "Successfully registered.")

    # --- Order save handling ---
    def _on_order_save_clicked(self) -> None:
        email_text = self.account_tab.email.text().strip()
        if not email_text:
            QtWidgets.QMessageBox.warning(self, "Missing email", "Please set the email field in the account tip.")
            return
        try:
            existing = load_clients(self._csv_path)
        except FileNotFoundError:
            existing = []
        target = None
        for c in existing:
            if c.email.lower() == email_text.lower():
                target = c
                break
        if target is None:
            QtWidgets.QMessageBox.warning(self, "Missing email", "Please set the email field in the account tip.")
            return

        # Update order-related fields
        target.application_center = self.order_tab.application_center.currentText()
        target.service_center = self.order_tab.service_center.currentText()
        target.trip_reason = self.order_tab.trip_reason.currentText()

        save_clients(self._csv_path, existing)
        QtWidgets.QMessageBox.information(self, "Success", "Successfully save")

    # --- Application save handling ---
    def _on_application_save_clicked(self) -> None:
        # Validate all fields are filled
        fields_to_check = [
            ("Gender", self.application_tab.gender.currentText()),
            ("Date Of Birth", self.application_tab.date_of_birth.date().toString("dd/MM/yyyy")),
            ("Current Nationality", self.application_tab.current_nationality.currentText()),
            ("Passport Number", self.application_tab.passport_number.text().strip()),
            ("Passport Expiry Date", self.application_tab.passport_expiry.date().toString("dd/MM/yyyy")),
        ]
        
        for field_name, value in fields_to_check:
            if not value or value == "Select":
                QtWidgets.QMessageBox.warning(self, "Validation Error", f"Please enter the {field_name} field value.")
                return

        # Get email for record lookup
        email = self.application_tab.email.text().strip()
        if not email:
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Email field is required.")
            return

        try:
            existing = load_clients(self._csv_path)
        except FileNotFoundError:
            existing = []

        # Find existing record by email
        target_record = None
        for record in existing:
            if record.email.lower() == email.lower():
                target_record = record
                break

        if target_record:
            # Update existing record
            target_record.gender = self.application_tab.gender.currentData() or self.application_tab.gender.currentText()
            target_record.date_of_birth = self.application_tab.date_of_birth.date().toString("dd/MM/yyyy")
            target_record.current_nationality = self.application_tab.current_nationality.currentText()
            target_record.passport_number = self.application_tab.passport_number.text().strip()
            target_record.passport_expiry = self.application_tab.passport_expiry.date().toString("dd/MM/yyyy")
        else:
            # Create new record
            new_record = ClientRecord(
                first_name=self.application_tab.first_name.text().strip(),
                last_name=self.application_tab.last_name.text().strip(),
                date_of_birth=self.application_tab.date_of_birth.date().toString("dd/MM/yyyy"),
                email=email,
                password="",  # Not collected in Application tab
                mobile_country_code=self.application_tab.contact_country_code.text().strip(),
                mobile_number=self.application_tab.contact_number.text().strip(),
                passport_number=self.application_tab.passport_number.text().strip(),
                visa_type="",  # Not collected in Application tab
                application_center="",  # Not collected in Application tab
                service_center="",  # Not collected in Application tab
                trip_reason="",  # Not collected in Application tab
                gender=self.application_tab.gender.currentData() or self.application_tab.gender.currentText(),
                current_nationality=self.application_tab.current_nationality.currentText(),
                passport_expiry=self.application_tab.passport_expiry.date().toString("dd/MM/yyyy"),
            )
            existing.append(new_record)

        save_clients(self._csv_path, existing)
        QtWidgets.QMessageBox.information(self, "Success", "Successfully saved application data.")

    # --- Tab change handling ---
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab changes, auto-populate Application tab when selected."""
        if index == 2:  # Application tab index
            self.application_tab.populate_from_account(self.account_tab)


def run_app() -> None:
    import sys

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()


