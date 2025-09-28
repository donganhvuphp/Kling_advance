#!/usr/bin/env python3
import sys
import os
import threading
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QLineEdit, QProgressBar,
    QCheckBox, QSpinBox, QGroupBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

from kling_engine import KlingEngine


class WorkerThread(QThread):
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal()
    browser_ready_signal = pyqtSignal()

    def __init__(self, engine, phase="BROWSER_ONLY"):
        super().__init__()
        self.engine = engine
        self.phase = phase  # "BROWSER_ONLY" or "PROCESSING"
        self.running = True
        self.start_processing_event = threading.Event()

    def run(self):
        try:
            # Phase 1: Launch browser
            self.emit_log("INFO", "Đang khởi động trình duyệt...")
            self.engine.launch_browser(
                log_callback=self.emit_log
            )
            self.emit_log("SUCCESS", "Trình duyệt đã sẵn sàng!")
            self.browser_ready_signal.emit()

            if self.phase == "BROWSER_ONLY":
                # Wait for signal to start processing
                self.emit_log("INFO", "Chờ lệnh bắt đầu xử lý...")
                while not self.start_processing_event.is_set() and self.running:
                    # Handle save session requests while waiting
                    self.engine._handle_save_session()
                    self.start_processing_event.wait(timeout=0.1)

            # Phase 2: Process folders (only if not stopped)
            if self.running and not self.engine.is_stopped():
                self.emit_log("INFO", "Bắt đầu xử lý video...")
                self.engine.run(
                    log_callback=self.emit_log,
                    progress_callback=self.emit_progress
                )
        except Exception as e:
            import traceback
            self.emit_log("ERROR", f"Exception: {e}")
            self.emit_log("ERROR", traceback.format_exc())
        finally:
            self.finished_signal.emit()

    def emit_log(self, level, message):
        self.log_signal.emit(level, message)

    def emit_progress(self, current, total):
        self.progress_signal.emit(current, total)

    def start_processing(self):
        """Signal the thread to start processing"""
        self.start_processing_event.set()

    def stop(self):
        self.running = False
        self.engine.stop()
        self.start_processing_event.set()  # Unblock if waiting


class KlingAdvanceUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = None
        self.worker = None
        self.folder_checkboxes = {}  # Dict[str, QCheckBox] - folder_name: checkbox
        self.init_ui()
        self.apply_dark_theme()

    def init_ui(self):
        self.setWindowTitle("Kling Video Generator - Giao diện nâng cao")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🎬 KLING VIDEO GENERATOR")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #00D9FF; padding: 10px;")
        main_layout.addWidget(header)

        # Two Column Layout
        columns_layout = QHBoxLayout()

        # ===== LEFT COLUMN =====
        left_column = QVBoxLayout()

        # Session Section
        session_group = QGroupBox("🔐 Phiên đăng nhập")
        session_layout = QHBoxLayout()

        self.session_status_label = QLabel("Chưa có phiên")
        self.session_status_label.setStyleSheet("color: #FFA500;")
        session_layout.addWidget(self.session_status_label)
        session_layout.addStretch()

        self.save_session_btn = QPushButton("💾")
        self.save_session_btn.clicked.connect(self.save_session)
        self.save_session_btn.setToolTip("Lưu phiên đăng nhập")
        self.save_session_btn.setMaximumWidth(50)
        session_layout.addWidget(self.save_session_btn)

        self.delete_session_btn = QPushButton("🗑️")
        self.delete_session_btn.clicked.connect(self.delete_session)
        self.delete_session_btn.setToolTip("Xóa phiên")
        self.delete_session_btn.setMaximumWidth(50)
        session_layout.addWidget(self.delete_session_btn)

        session_group.setLayout(session_layout)
        left_column.addWidget(session_group)
        self.update_session_status()

        # Settings Section
        settings_group = QGroupBox("⚙️ Cài đặt")
        settings_layout = QVBoxLayout()

        # Folder selection
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Thư mục:")
        folder_label.setMinimumWidth(80)
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Chọn thư mục gốc...")
        self.folder_input.setReadOnly(True)
        folder_btn = QPushButton("...")
        folder_btn.setMaximumWidth(40)
        folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(folder_btn)
        settings_layout.addLayout(folder_layout)

        # Options
        opt1_layout = QHBoxLayout()
        self.headless_check = QCheckBox("Ẩn trình duyệt")
        self.headless_check.setToolTip("Chạy trình duyệt nền")
        opt1_layout.addWidget(self.headless_check)
        opt1_layout.addStretch()
        settings_layout.addLayout(opt1_layout)

        opt2_layout = QHBoxLayout()
        concurrent_label = QLabel("Video đồng thời:")
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(10)
        self.concurrent_spin.setValue(2)
        opt2_layout.addWidget(concurrent_label)
        opt2_layout.addWidget(self.concurrent_spin)
        opt2_layout.addStretch()
        settings_layout.addLayout(opt2_layout)

        opt3_layout = QHBoxLayout()
        poll_label = QLabel("Khoảng kiểm tra (s):")
        self.poll_spin = QSpinBox()
        self.poll_spin.setMinimum(5)
        self.poll_spin.setMaximum(60)
        self.poll_spin.setValue(10)
        opt3_layout.addWidget(poll_label)
        opt3_layout.addWidget(self.poll_spin)
        opt3_layout.addStretch()
        settings_layout.addLayout(opt3_layout)

        settings_group.setLayout(settings_layout)
        left_column.addWidget(settings_group)

        # Progress Section
        progress_group = QGroupBox("📊 Tiến độ")
        progress_layout = QVBoxLayout()

        self.progress_label = QLabel("Sẵn sàng")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        progress_group.setLayout(progress_layout)
        left_column.addWidget(progress_group)

        left_column.addStretch()
        columns_layout.addLayout(left_column)

        # ===== RIGHT COLUMN =====
        right_column = QVBoxLayout()

        # Folder Selection Section
        folder_selection_group = QGroupBox("📁 Chọn thư mục xử lý")
        folder_selection_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)

        self.folder_checkboxes_widget = QWidget()
        self.folder_checkboxes_layout = QVBoxLayout(self.folder_checkboxes_widget)
        self.folder_checkboxes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.folder_checkboxes_widget)

        folder_selection_layout.addWidget(scroll_area)

        folder_control_layout = QHBoxLayout()
        select_all_btn = QPushButton("Chọn tất cả")
        select_all_btn.clicked.connect(self.select_all_folders)
        folder_control_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Bỏ chọn")
        deselect_all_btn.clicked.connect(self.deselect_all_folders)
        folder_control_layout.addWidget(deselect_all_btn)

        refresh_folders_btn = QPushButton("🔄")
        refresh_folders_btn.setMaximumWidth(50)
        refresh_folders_btn.clicked.connect(self.load_folders)
        folder_control_layout.addWidget(refresh_folders_btn)

        folder_selection_layout.addLayout(folder_control_layout)
        folder_selection_group.setLayout(folder_selection_layout)
        right_column.addWidget(folder_selection_group)

        columns_layout.addLayout(right_column)
        main_layout.addLayout(columns_layout)

        # Control Buttons
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.open_browser_btn = QPushButton("🌐 Mở trình duyệt")
        self.open_browser_btn.setMinimumHeight(50)
        self.open_browser_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.open_browser_btn.clicked.connect(self.open_browser)
        self.open_browser_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
        """)

        self.start_btn = QPushButton("▶ Bắt đầu")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.start_btn.clicked.connect(self.start_process)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #00D9FF;
                color: #0A0E27;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #00B8D4;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
        """)

        self.pause_btn = QPushButton("⏸ Tạm dừng")
        self.pause_btn.setMinimumHeight(50)
        self.pause_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.pause_btn.clicked.connect(self.pause_process)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFA500;
                color: #0A0E27;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #FF8C00;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
        """)

        self.stop_btn = QPushButton("⏹ Dừng lại")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.stop_btn.clicked.connect(self.stop_process)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #CC0000;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
        """)

        control_layout.addWidget(self.open_browser_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.stop_btn)
        main_layout.addLayout(control_layout)

        # Initially disable Start button until browser is opened
        self.start_btn.setEnabled(False)

        # Log Section
        log_group = QGroupBox("📝 Nhật ký")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setMinimumHeight(300)
        log_layout.addWidget(self.log_text)

        log_control_layout = QHBoxLayout()
        clear_log_btn = QPushButton("Xóa nhật ký")
        clear_log_btn.clicked.connect(self.clear_logs)
        export_log_btn = QPushButton("Xuất nhật ký")
        export_log_btn.clicked.connect(self.export_logs)
        log_control_layout.addWidget(clear_log_btn)
        log_control_layout.addWidget(export_log_btn)
        log_control_layout.addStretch()
        log_layout.addLayout(log_control_layout)

        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Status Bar
        self.statusBar().showMessage("Sẵn sàng")

    def apply_dark_theme(self):
        dark_palette = QPalette()

        # Base colors
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(10, 14, 39))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(15, 20, 50))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 25, 55))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(25, 30, 60))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(0, 217, 255))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 217, 255))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(10, 14, 39))

        self.setPalette(dark_palette)

        # Additional styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0A0E27;
            }
            QGroupBox {
                border: 2px solid #00D9FF;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 20px;
                font-weight: bold;
                color: #00D9FF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
            QLabel {
                color: #DCDCDC;
            }
            QLineEdit, QSpinBox {
                background-color: #0F1432;
                border: 1px solid #00D9FF;
                border-radius: 4px;
                padding: 8px;
                color: #DCDCDC;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 2px solid #00D9FF;
            }
            QPushButton {
                background-color: #192041;
                color: #DCDCDC;
                border: 1px solid #00D9FF;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #253052;
                border: 2px solid #00D9FF;
            }
            QPushButton:disabled {
                background-color: #1a1a2e;
                color: #555;
                border: 1px solid #333;
            }
            QTextEdit {
                background-color: #0F1432;
                border: 1px solid #00D9FF;
                border-radius: 4px;
                color: #DCDCDC;
                padding: 5px;
            }
            QProgressBar {
                border: 2px solid #00D9FF;
                border-radius: 5px;
                text-align: center;
                background-color: #0F1432;
                color: #DCDCDC;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00D9FF, stop:1 #0099CC);
                border-radius: 3px;
            }
            QCheckBox {
                color: #000000;
                spacing: 8px;
                font-weight: normal;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #888888;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #00D9FF;
            }
            QCheckBox::indicator:checked {
                background-color: #00CC66;
                border: 2px solid #00CC66;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjMzMzMgNC42NjY2N0w2IDEyTDIuNjY2NjcgOC42NjY2NyIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
        """)

    def update_session_status(self):
        """Update session status label based on state.json existence"""
        session_file = Path("state.json")
        if session_file.exists():
            self.session_status_label.setText("✓ Đã có phiên đăng nhập")
            self.session_status_label.setStyleSheet("color: #00FF88;")
            self.save_session_btn.setEnabled(False)
            self.delete_session_btn.setEnabled(True)
        else:
            self.session_status_label.setText("Chưa có phiên đăng nhập")
            self.session_status_label.setStyleSheet("color: #FFA500;")
            self.save_session_btn.setEnabled(True)
            self.delete_session_btn.setEnabled(False)

    def save_session(self):
        """Trigger manual session save from running engine"""
        if self.engine and hasattr(self.engine, 'request_save_session'):
            success, message = self.engine.request_save_session()
            if success:
                self.log_message("SUCCESS", "Đã lưu phiên đăng nhập thành công!")
                self.update_session_status()
            else:
                self.log_message("ERROR", f"Lỗi khi lưu phiên: {message}")
        else:
            self.log_message("WARNING", "Vui lòng mở trình duyệt trước khi lưu phiên")

    def delete_session(self):
        """Delete saved session file"""
        session_file = Path("state.json")
        if session_file.exists():
            try:
                session_file.unlink()
                self.log_message("SUCCESS", "Đã xóa phiên đăng nhập. Lần chạy tiếp theo sẽ yêu cầu đăng nhập lại.")
                self.update_session_status()
            except Exception as e:
                self.log_message("ERROR", f"Lỗi khi xóa phiên: {e}")
        else:
            self.log_message("INFO", "Không có phiên đăng nhập nào để xóa")

    def open_browser(self):
        """Open browser and wait for user to login"""
        root_folder = self.folder_input.text()
        if not root_folder or not Path(root_folder).exists():
            self.log_message("ERROR", "Vui lòng chọn thư mục gốc trước")
            return

        # Get selected folders
        selected_folders = self.get_selected_folders()
        if not selected_folders:
            self.log_message("ERROR", "Vui lòng chọn ít nhất một thư mục để xử lý")
            return

        self.log_message("INFO", "Đang chuẩn bị mở trình duyệt...")

        # Create engine with selected folders
        self.engine = KlingEngine(
            root_folder=root_folder,
            headless=self.headless_check.isChecked(),
            max_concurrent=self.concurrent_spin.value(),
            poll_interval=self.poll_spin.value(),
            selected_folders=selected_folders
        )

        # Start worker thread in BROWSER_ONLY mode
        self.worker = WorkerThread(self.engine, phase="BROWSER_ONLY")
        self.worker.log_signal.connect(self.log_message)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.browser_ready_signal.connect(self.on_browser_ready)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

        self.open_browser_btn.setEnabled(False)
        self.statusBar().showMessage("Đang mở trình duyệt...")

    def on_browser_ready(self):
        """Called when browser is ready"""
        self.start_btn.setEnabled(True)
        self.save_session_btn.setEnabled(True)
        self.statusBar().showMessage("Trình duyệt đã sẵn sàng - Hãy đăng nhập nếu cần, sau đó nhấn 'Bắt đầu'")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục gốc")
        if folder:
            self.folder_input.setText(folder)
            self.log_message("INFO", f"Đã chọn thư mục: {folder}")
            self.load_folders()

    def load_folders(self):
        """Load and display folders from root directory"""
        root_folder = self.folder_input.text()
        if not root_folder or not Path(root_folder).exists():
            return

        # Clear existing checkboxes
        for checkbox in self.folder_checkboxes.values():
            self.folder_checkboxes_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.folder_checkboxes.clear()

        # Load folders
        root_path = Path(root_folder)
        folders = sorted([f for f in root_path.iterdir() if f.is_dir()])

        if not folders:
            no_folder_label = QLabel("Không tìm thấy thư mục con nào")
            no_folder_label.setStyleSheet("color: #FFA500; font-style: italic;")
            self.folder_checkboxes_layout.addWidget(no_folder_label)
            return

        # Create checkbox for each folder
        for folder in folders:
            # Count images in folder
            image_count = len(list(folder.glob('*.jpg'))) + len(list(folder.glob('*.png'))) + \
                         len(list(folder.glob('*.jpeg'))) + len(list(folder.glob('*.webp')))

            checkbox = QCheckBox(f"{folder.name} ({image_count} images)")
            checkbox.setChecked(True)  # Default: select all
            self.folder_checkboxes[folder.name] = checkbox
            self.folder_checkboxes_layout.addWidget(checkbox)

        self.log_message("INFO", f"Đã tải {len(folders)} thư mục")

    def select_all_folders(self):
        """Check all folder checkboxes"""
        for checkbox in self.folder_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all_folders(self):
        """Uncheck all folder checkboxes"""
        for checkbox in self.folder_checkboxes.values():
            checkbox.setChecked(False)

    def get_selected_folders(self):
        """Get list of selected folder names"""
        return [folder_name for folder_name, checkbox in self.folder_checkboxes.items() if checkbox.isChecked()]

    def start_process(self):
        if not self.worker or not self.worker.isRunning():
            self.log_message("ERROR", "Vui lòng mở trình duyệt trước khi bắt đầu")
            return

        if not self.engine or not self.engine.browser or not self.engine.page:
            self.log_message("ERROR", "Trình duyệt chưa sẵn sàng. Vui lòng mở trình duyệt trước.")
            return

        self.log_message("INFO", "Gửi lệnh bắt đầu xử lý...")

        # Signal the worker thread to start processing
        self.worker.start_processing()

        self.open_browser_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage("Đang chạy...")

    def pause_process(self):
        if self.engine:
            if self.engine.is_paused():
                self.engine.resume()
                self.pause_btn.setText("⏸ Tạm dừng")
                self.log_message("INFO", "Đã tiếp tục")
                self.statusBar().showMessage("Đang chạy...")
            else:
                self.engine.pause()
                self.pause_btn.setText("▶ Tiếp tục")
                self.log_message("INFO", "Đã tạm dừng")
                self.statusBar().showMessage("Đã tạm dừng")

    def stop_process(self):
        if self.worker:
            self.log_message("WARNING", "Đang dừng tiến trình...")
            self.worker.stop()
            self.worker.wait()
            self.on_finished()

    def on_finished(self):
        self.log_message("INFO", "Tiến trình đã hoàn thành")
        self.open_browser_btn.setEnabled(True)
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("⏸ Tạm dừng")
        self.update_session_status()
        self.statusBar().showMessage("Hoàn thành")

    def update_progress(self, current, total):
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_label.setText(f"Đã tải: {current}/{total} videos")
        else:
            self.progress_bar.setValue(0)

    def log_message(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")

        color_map = {
            "INFO": "#00D9FF",
            "DEBUG": "#888888",
            "WARNING": "#FFA500",
            "ERROR": "#FF4444",
            "SUCCESS": "#00FF88"
        }

        color = color_map.get(level, "#DCDCDC")
        formatted = f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">[{level}]</span> <span style="color: #DCDCDC;">{message}</span>'

        self.log_text.append(formatted)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def clear_logs(self):
        self.log_text.clear()
        self.log_message("INFO", "Đã xóa nhật ký")

    def export_logs(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Xuất nhật ký", f"kling_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            self.log_message("SUCCESS", f"Đã xuất nhật ký ra {filename}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = KlingAdvanceUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()