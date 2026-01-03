"""
Окно для просмотра изображений в полном размере
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QScrollArea, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from pathlib import Path


class ImageViewer(QDialog):
    """Окно для просмотра изображения в полном размере"""
    
    def __init__(self, image_path: str, parent=None):
        """
        Инициализация окна просмотра
        
        Args:
            image_path: Путь к изображению
            parent: Родительское окно
        """
        super().__init__(parent)
        self.image_path = image_path
        self.init_ui()
        self.load_image()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Просмотр изображения")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Область прокрутки для изображения
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)
        
        scroll_area.setWidget(self.image_label)
        layout.addWidget(scroll_area)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.zoom_in_btn = QPushButton("Увеличить")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        button_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("Уменьшить")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        button_layout.addWidget(self.zoom_out_btn)
        
        self.fit_btn = QPushButton("По размеру окна")
        self.fit_btn.clicked.connect(self.fit_to_window)
        button_layout.addWidget(self.fit_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.zoom_factor = 1.0
    
    def load_image(self):
        """Загрузка изображения"""
        try:
            pixmap = QPixmap(self.image_path)
            if pixmap.isNull():
                self.image_label.setText("Ошибка загрузки изображения")
                return
            
            self.original_pixmap = pixmap
            self.update_image()
        except Exception as e:
            self.image_label.setText(f"Ошибка: {str(e)}")
    
    def update_image(self):
        """Обновление отображения изображения"""
        if hasattr(self, 'original_pixmap'):
            scaled_pixmap = self.original_pixmap.scaled(
                int(self.original_pixmap.width() * self.zoom_factor),
                int(self.original_pixmap.height() * self.zoom_factor),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
    
    def zoom_in(self):
        """Увеличить изображение"""
        self.zoom_factor *= 1.2
        self.update_image()
    
    def zoom_out(self):
        """Уменьшить изображение"""
        self.zoom_factor *= 0.8
        if self.zoom_factor < 0.1:
            self.zoom_factor = 0.1
        self.update_image()
    
    def fit_to_window(self):
        """Подогнать изображение под размер окна"""
        if hasattr(self, 'original_pixmap'):
            scroll_area = self.image_label.parent().parent()
            available_size = scroll_area.size()
            
            pixmap_size = self.original_pixmap.size()
            scale_x = available_size.width() / pixmap_size.width()
            scale_y = available_size.height() / pixmap_size.height()
            
            self.zoom_factor = min(scale_x, scale_y) * 0.9  # Немного меньше для отступов
            self.update_image()





