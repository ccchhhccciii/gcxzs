import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, \
    QMessageBox, QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import Qt
from utils.video import generate_video, parse_subtitles
from utils.midi import midi_to_wav, get_wav_duration, parse_midi_notes, adjust_and_generate_srt_lines, generate_srt

class MidiToSrtTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        # MIDI文件路径输入和选择按钮
        midi_file_layout = QHBoxLayout()
        self.midi_file_label = QLabel("MIDI文件路径:")
        self.midi_file_entry = QLineEdit()
        self.midi_file_entry.setReadOnly(True)
        self.midi_file_button = QPushButton("选择")
        self.midi_file_button.clicked.connect(self.choose_midi_file)
        midi_file_layout.addWidget(self.midi_file_label)
        midi_file_layout.addWidget(self.midi_file_entry)
        midi_file_layout.addWidget(self.midi_file_button)
        layout.addLayout(midi_file_layout)
        # 输出文件路径输入和选择按钮
        output_file_layout = QHBoxLayout()
        self.output_file_label = QLabel("输出SRT文件路径:")
        self.output_file_entry = QLineEdit()
        self.output_file_entry.setReadOnly(True)
        self.output_file_button = QPushButton("选择")
        self.output_file_button.clicked.connect(self.choose_output_directory)
        output_file_layout.addWidget(self.output_file_label)
        output_file_layout.addWidget(self.output_file_entry)
        output_file_layout.addWidget(self.output_file_button)
        layout.addLayout(output_file_layout)
        # 定义生成按钮
        self.generate_button = QPushButton("生成")
        self.generate_button.clicked.connect(self.generate_srt)
        self.generate_button.setEnabled(False)
        layout.addWidget(self.generate_button)
        self.setLayout(layout)

    def choose_midi_file(self):
        midi_file_path, _ = QFileDialog.getOpenFileName(self, "选择MIDI文件", "", "MIDI文件 (*.midi *.mid)")
        if midi_file_path:
            self.midi_file_entry.setText(midi_file_path)
            self.check_file_selection()

    def choose_output_directory(self):
        output_directory_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if output_directory_path:
            self.output_file_entry.setText(output_directory_path)
            self.check_file_selection()

    def check_file_selection(self):
        midi_file_path = self.midi_file_entry.text()
        output_directory_path = self.output_file_entry.text()
        self.generate_button.setEnabled(bool(midi_file_path and output_directory_path))

    def generate_srt(self):
        midi_file_path = self.midi_file_entry.text()
        output_directory_path = self.output_file_entry.text()
        if not midi_file_path or not output_directory_path:
            QMessageBox.warning(self, "错误", "请确保选择了MIDI文件和输出目录")
            return
        generate_srt(midi_file_path, output_directory_path)

class VideoCreationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        # 视频文件夹路径输入和选择按钮
        video_folder_layout = QHBoxLayout()
        self.video_folder_label = QLabel("视频文件夹路径:")
        self.video_folder_entry = QLineEdit()
        self.video_folder_entry.setReadOnly(True)
        self.video_folder_button = QPushButton("选择")
        self.video_folder_button.clicked.connect(self.choose_video_folder)
        video_folder_layout.addWidget(self.video_folder_label)
        video_folder_layout.addWidget(self.video_folder_entry)
        video_folder_layout.addWidget(self.video_folder_button)
        layout.addLayout(video_folder_layout)
        # 字幕文件路径输入和选择按钮
        subtitle_file_layout = QHBoxLayout()
        self.subtitle_file_label = QLabel("字幕文件路径:")
        self.subtitle_file_entry = QLineEdit()
        self.subtitle_file_entry.setReadOnly(True)
        self.subtitle_file_button = QPushButton("选择")
        self.subtitle_file_button.clicked.connect(self.choose_subtitle_file)
        subtitle_file_layout.addWidget(self.subtitle_file_label)
        subtitle_file_layout.addWidget(self.subtitle_file_entry)
        subtitle_file_layout.addWidget(self.subtitle_file_button)
        layout.addLayout(subtitle_file_layout)
        # 目标分辨率选择
        resolution_layout = QHBoxLayout()
        self.resolution_label = QLabel("目标分辨率:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1280x720", "1920x1080", "720x480"])
        resolution_layout.addWidget(self.resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        layout.addLayout(resolution_layout)
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        # 添加生成按钮
        self.generate_button = QPushButton("生成")
        self.generate_button.clicked.connect(self.generate_video)
        self.generate_button.setEnabled(False)
        layout.addWidget(self.generate_button)
        self.setLayout(layout)

    def choose_video_folder(self):
        video_folder_path = QFileDialog.getExistingDirectory(self, "选择视频文件夹")
        if video_folder_path:
            self.video_folder_entry.setText(video_folder_path)
            self.check_generation_ready()

    def choose_subtitle_file(self):
        subtitle_file_path, _ = QFileDialog.getOpenFileName(self, "选择字幕文件", "", "字幕文件 (*.srt)")
        if subtitle_file_path:
            self.subtitle_file_entry.setText(subtitle_file_path)
            self.check_generation_ready()

    def check_generation_ready(self):
        video_folder_path = self.video_folder_entry.text()
        subtitle_file_path = self.subtitle_file_entry.text()
        self.generate_button.setEnabled(bool(video_folder_path and subtitle_file_path))

    def generate_video(self):
        video_folder_path = self.video_folder_entry.text()
        subtitle_file_path = self.subtitle_file_entry.text()
        target_resolution = self.resolution_combo.currentText()
        output_dir = os.path.join(os.getcwd(), 'output')  # 设置输出路径为代码所在目录下的output文件夹
        os.makedirs(output_dir, exist_ok=True)  # 创建output文件夹(如果不存在)
        output_file_path = os.path.join(output_dir, 'output_video.mp4')

        if not video_folder_path or not subtitle_file_path:
            QMessageBox.warning(self, "错误", "请确保选择了视频文件夹和字幕文件")
            return
        try:
            # 解析字幕文件
            subtitles = parse_subtitles(subtitle_file_path)
            # 生成视频
            generate_video(subtitles, video_folder_path, output_file_path, target_resolution_str=target_resolution,
                           progress_callback=self.update_progress)
            QMessageBox.information(self, "完成", "视频生成完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"视频生成失败: {str(e)}")

    def update_progress(self, current, total):
        progress = (current / total) * 100
        self.progress_bar.setValue(int(progress))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('视频字幕生成工具')
        self.setGeometry(100, 100, 800, 600)
        # 创建选项卡小部件
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        # 添加"MIDI转字幕"选项卡
        self.midi_to_srt_tab = MidiToSrtTab()
        self.tabs.addTab(self.midi_to_srt_tab, "MIDI转字幕")
        # 添加"视频生成"选项卡
        self.video_creation_tab = VideoCreationTab()
        self.tabs.addTab(self.video_creation_tab, "视频生成")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())