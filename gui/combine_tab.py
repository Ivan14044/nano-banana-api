"""
Вкладка для комбинирования изображений
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QLabel, QComboBox, QGroupBox, QFileDialog,
                             QMessageBox, QProgressBar, QListWidget, QListWidgetItem, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon
from api.client import NanoBananaAPIClient
from api.models import CombineRequest
from utils.image_utils import url_to_image, base64_to_image
from utils.image_uploader import upload_image
from utils.config import Config
from database.db_manager import DatabaseManager
from pathlib import Path
from datetime import datetime


class CombineWorker(QThread):
    """Поток для комбинирования изображений"""
    finished = pyqtSignal(bool, str, str)  # success, message, image_path
    progress = pyqtSignal(str)  # Сообщение о прогрессе
    
    def __init__(self, client: NanoBananaAPIClient, request: CombineRequest):
        super().__init__()
        self.client = client
        self.request = request
    
    def run(self):
        """Выполнение комбинирования"""
        try:
            # Загружаем все изображения на публичные URL
            image_urls = []
            total = len(self.request.image_paths)
            
            for idx, img_path in enumerate(self.request.image_paths, 1):
                self.progress.emit(f"Загрузка изображения {idx}/{total}...")
                image_url = upload_image(img_path)
                if image_url:
                    image_urls.append(image_url)
                else:
                    error_msg = (
                        f"Не удалось загрузить изображение {idx} на публичный URL.\n\n"
                        "Возможные причины:\n"
                        "• Проблемы с интернет-соединением\n"
                        "• Временная недоступность сервисов загрузки\n"
                        "• Файл слишком большой\n\n"
                        "Попробуйте:\n"
                        "• Проверить интернет-соединение\n"
                        "• Уменьшить размер изображений\n"
                        "• Попробовать позже"
                    )
                    self.finished.emit(False, error_msg, "")
                    return
            
            if len(image_urls) != total:
                self.finished.emit(False, "Не все изображения удалось загрузить", "")
                return
            
            self.progress.emit("Все изображения загружены. Отправка запроса на комбинирование...")
            response = self.client.combine_images(self.request, image_urls)
            if response.success:
                # Сохраняем изображение
                config = Config()
                images_dir = Path(config.ensure_images_dir())
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = images_dir / f"combined_{timestamp}.png"
                
                if response.image_url:
                    success = url_to_image(
                        response.image_url, 
                        str(image_path),
                        aspect_ratio=self.request.aspect_ratio,
                        resolution=self.request.resolution,
                        crop_to_aspect=self.crop_to_aspect
                    )
                elif response.image_base64:
                    success = base64_to_image(
                        response.image_base64, 
                        str(image_path),
                        aspect_ratio=self.request.aspect_ratio,
                        resolution=self.request.resolution,
                        crop_to_aspect=self.crop_to_aspect
                    )
                else:
                    success = False
                
                if success:
                    self.finished.emit(True, "Изображения успешно объединены!", str(image_path))
                else:
                    self.finished.emit(False, "Ошибка сохранения изображения", "")
            else:
                self.finished.emit(False, response.error_message or "Неизвестная ошибка", "")
        except Exception as e:
            self.finished.emit(False, f"Ошибка: {str(e)}", "")


class CombineTab(QWidget):
    """Вкладка для комбинирования изображений"""
    
    def __init__(self, api_client: NanoBananaAPIClient = None, db_manager: DatabaseManager = None):
        super().__init__()
        self.api_client = api_client
        self.db_manager = db_manager
        self.config = Config()
        self.image_paths = []
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        
        # Загрузка изображений
        images_group = QGroupBox("Изображения для комбинирования (до 8)")
        images_layout = QVBoxLayout()
        
        image_controls = QHBoxLayout()
        self.add_image_btn = QPushButton("Добавить изображение")
        self.add_image_btn.clicked.connect(self.add_image)
        image_controls.addWidget(self.add_image_btn)
        
        self.remove_image_btn = QPushButton("Удалить выбранное")
        self.remove_image_btn.clicked.connect(self.remove_selected_image)
        self.remove_image_btn.setEnabled(False)
        image_controls.addWidget(self.remove_image_btn)
        
        self.clear_images_btn = QPushButton("Очистить все")
        self.clear_images_btn.clicked.connect(self.clear_images)
        image_controls.addWidget(self.clear_images_btn)
        
        image_controls.addStretch()
        self.image_count_label = QLabel("Изображений: 0/8")
        image_controls.addWidget(self.image_count_label)
        
        images_layout.addLayout(image_controls)
        
        self.images_list = QListWidget()
        self.images_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.images_list.setMaximumHeight(250)
        self.images_list.setIconSize(QSize(100, 100))  # Размер иконок
        self.images_list.setViewMode(QListWidget.IconMode)  # Режим иконок
        images_layout.addWidget(self.images_list)
        
        images_group.setLayout(images_layout)
        layout.addWidget(images_group)
        
        # Инструкции
        prompt_group = QGroupBox("Инструкции по комбинированию")
        prompt_layout = QVBoxLayout()
        self.combine_prompt_text = QTextEdit()
        self.combine_prompt_text.setPlaceholderText("Опишите, как нужно объединить изображения...")
        self.combine_prompt_text.setMinimumHeight(100)
        prompt_layout.addWidget(self.combine_prompt_text)
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        
        # Негативный промпт
        negative_group = QGroupBox("Негативный промпт (опционально)")
        negative_layout = QVBoxLayout()
        self.negative_prompt_text = QTextEdit()
        self.negative_prompt_text.setPlaceholderText("Что не должно быть на изображении...")
        self.negative_prompt_text.setMaximumHeight(60)
        negative_layout.addWidget(self.negative_prompt_text)
        negative_group.setLayout(negative_layout)
        layout.addWidget(negative_group)
        
        # Параметры
        params_group = QGroupBox("Параметры")
        params_layout = QVBoxLayout()
        
        # Модель (обычно Pro для комбинирования)
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Pro (рекомендуется для комбинирования)"])
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        params_layout.addLayout(model_layout)
        
        # Разрешение
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Разрешение:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1024x1024 (1K)", "2048x2048 (2K)", "4096x4096 (4K)"])
        self.resolution_combo.setCurrentIndex(1)  # По умолчанию 2K
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addStretch()
        params_layout.addLayout(resolution_layout)
        
        # Соотношение сторон
        aspect_layout = QHBoxLayout()
        aspect_layout.addWidget(QLabel("Соотношение сторон:"))
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems([
            "1:1 (Квадрат)",
            "16:9 (Широкоформатное)",
            "9:16 (Портретное)",
            "4:3 (Классическое)",
            "3:4 (Портретное классическое)",
            "3:2 (Фото широкое)",
            "2:3 (Фото портретное)",
            "21:9 (Ультраширокое)",
            "4:5 (Портретное близко к квадрату)",
            "5:4 (Портретное близко к квадрату)"
        ])
        self.aspect_combo.setCurrentIndex(0)  # По умолчанию 1:1
        aspect_layout.addWidget(self.aspect_combo)
        aspect_layout.addStretch()
        params_layout.addLayout(aspect_layout)
        
        # Обрезка до точного соотношения сторон
        crop_layout = QHBoxLayout()
        self.crop_to_aspect_checkbox = QCheckBox("Обрезать до точного соотношения сторон (может обрезать часть изображения)")
        self.crop_to_aspect_checkbox.setChecked(False)  # По умолчанию выключено
        crop_layout.addWidget(self.crop_to_aspect_checkbox)
        crop_layout.addStretch()
        params_layout.addLayout(crop_layout)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Кнопка комбинирования
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.combine_btn = QPushButton("Объединить изображения")
        self.combine_btn.clicked.connect(self.combine_images)
        self.combine_btn.setEnabled(False)
        self.combine_btn.setMinimumWidth(150)
        button_layout.addWidget(self.combine_btn)
        layout.addLayout(button_layout)
        
        layout.addStretch()
        self.setLayout(layout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
    
    def set_api_client(self, client: NanoBananaAPIClient):
        """Установить API клиент"""
        self.api_client = client
    
    def set_db_manager(self, db_manager: DatabaseManager):
        """Установить менеджер БД"""
        self.db_manager = db_manager
    
    def add_image(self):
        """Добавить изображение"""
        if len(self.image_paths) >= 8:
            QMessageBox.warning(self, "Ошибка", "Максимум 8 изображений!")
            return
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите изображения",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        for file_path in file_paths:
            if file_path not in self.image_paths and len(self.image_paths) < 8:
                self.image_paths.append(file_path)
                # Создаем миниатюру
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # Масштабируем до 100x100 с сохранением пропорций
                    scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item = QListWidgetItem(Path(file_path).name)
                    item.setIcon(QIcon(scaled_pixmap))
                    item.setData(Qt.UserRole, file_path)
                    item.setToolTip(file_path)  # Показываем полный путь при наведении
                    self.images_list.addItem(item)
                else:
                    # Если не удалось загрузить изображение, добавляем без иконки
                    item = QListWidgetItem(Path(file_path).name)
                    item.setData(Qt.UserRole, file_path)
                    self.images_list.addItem(item)
        
        self.update_image_count()
        self.combine_btn.setEnabled(len(self.image_paths) >= 2)
    
    def remove_selected_image(self):
        """Удалить выбранное изображение"""
        current_item = self.images_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.UserRole)
            if file_path in self.image_paths:
                self.image_paths.remove(file_path)
            self.images_list.takeItem(self.images_list.row(current_item))
            self.update_image_count()
            self.combine_btn.setEnabled(len(self.image_paths) >= 2)
    
    def clear_images(self):
        """Очистить все изображения"""
        self.image_paths.clear()
        self.images_list.clear()
        self.update_image_count()
        self.combine_btn.setEnabled(False)
    
    def update_image_count(self):
        """Обновить счетчик изображений"""
        self.image_count_label.setText(f"Изображений: {len(self.image_paths)}/8")
    
    def on_selection_changed(self):
        """Обработка изменения выбора"""
        self.remove_image_btn.setEnabled(self.images_list.currentItem() is not None)
    
    def combine_images(self):
        """Комбинирование изображений"""
        if not self.api_client:
            QMessageBox.warning(self, "Ошибка", "API ключ не установлен!")
            return
        
        if len(self.image_paths) < 2:
            QMessageBox.warning(self, "Ошибка", "Добавьте минимум 2 изображения!")
            return
        
        prompt = self.combine_prompt_text.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Ошибка", "Введите инструкции по комбинированию!")
            return
        
        # Получаем параметры
        resolution_map = {"1024x1024 (1K)": "1024", "2048x2048 (2K)": "2048", "4096x4096 (4K)": "4096"}
        resolution = resolution_map[self.resolution_combo.currentText()]
        negative_prompt = self.negative_prompt_text.toPlainText().strip() or None
        
        # Получаем соотношение сторон
        aspect_text = self.aspect_combo.currentText()
        aspect_map = {
            "1:1 (Квадрат)": "1:1",
            "16:9 (Широкоформатное)": "16:9",
            "9:16 (Портретное)": "9:16",
            "4:3 (Классическое)": "4:3",
            "3:4 (Портретное классическое)": "3:4",
            "3:2 (Фото широкое)": "3:2",
            "2:3 (Фото портретное)": "2:3",
            "21:9 (Ультраширокое)": "21:9",
            "4:5 (Портретное близко к квадрату)": "4:5",
            "5:4 (Портретное близко к квадрату)": "5:4"
        }
        aspect_ratio = aspect_map.get(aspect_text, "1:1")
        
        # Создаем запрос
        request = CombineRequest(
            image_paths=self.image_paths,
            prompt=prompt,
            model="pro",
            resolution=resolution,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio
        )
        
        # Получаем значение чекбокса обрезки
        crop_to_aspect = self.crop_to_aspect_checkbox.isChecked()
        
        # Блокируем кнопку
        self.combine_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Запускаем комбинирование в отдельном потоке
        self.worker = CombineWorker(self.api_client, request, crop_to_aspect)
        self.worker.progress.connect(self.on_combine_progress)
        self.worker.finished.connect(self.on_combine_finished)
        self.worker.start()
    
    def on_combine_progress(self, message: str):
        """Обработка прогресса комбинирования"""
        # Можно обновить статус, если нужно
        pass
    
    def on_combine_finished(self, success: bool, message: str, image_path: str):
        """Обработка завершения комбинирования"""
        self.combine_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            # Сохраняем в БД
            if self.db_manager:
                resolution = self.resolution_combo.currentText().split()[0]
                self.db_manager.add_generation(
                    gen_type="combine",
                    prompt=self.combine_prompt_text.toPlainText(),
                    model="pro",
                    image_path=image_path,
                    resolution=resolution,
                    negative_prompt=self.negative_prompt_text.toPlainText().strip() or None
                )
            
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.critical(self, "Ошибка", message)

