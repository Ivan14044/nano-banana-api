"""
Вкладка для генерации изображений
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QLabel, QComboBox, QGroupBox, QSpinBox,
                             QCheckBox, QLineEdit, QMessageBox, QProgressBar, QRadioButton,
                             QListWidget, QListWidgetItem, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon
from api.client import NanoBananaAPIClient
from api.models import GenerationRequest
from utils.image_utils import url_to_image, base64_to_image
from utils.image_uploader import upload_image
from utils.config import Config
from database.db_manager import DatabaseManager
from pathlib import Path
from datetime import datetime


class GenerationWorker(QThread):
    """Поток для генерации изображений"""
    finished = pyqtSignal(bool, str, str)  # success, message, image_path
    progress = pyqtSignal(int, int, str)  # current, total, prompt
    image_saved = pyqtSignal(str, str, str, str, str)  # image_path, prompt, model, resolution, negative_prompt
    
    def __init__(self, client: NanoBananaAPIClient, request: GenerationRequest, batch_mode=False, prompts_list=None, reference_urls=None, crop_to_aspect=False):
        super().__init__()
        self.client = client
        self.request = request
        self.batch_mode = batch_mode
        self.prompts_list = prompts_list or []
        self.reference_urls = reference_urls or []
        self.model = request.model
        self.resolution = request.resolution
        self.negative_prompt = request.negative_prompt
        self.crop_to_aspect = crop_to_aspect
    
    def run(self):
        """Выполнение генерации"""
        if self.batch_mode and self.prompts_list:
            # Пакетная генерация
            total = len(self.prompts_list)
            success_count = 0
            
            for idx, prompt in enumerate(self.prompts_list, 1):
                self.progress.emit(idx, total, prompt)
                
                # Обновляем промпт в запросе
                self.request.prompt = prompt.strip()
                
                try:
                    response = self.client.generate_image(self.request, self.reference_urls if self.reference_urls else None)
                    if response.success:
                        # Сохраняем изображение
                        config = Config()
                        images_dir = Path(config.ensure_images_dir())
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_path = images_dir / f"generated_batch_{idx}_{timestamp}.png"
                        
                        if response.image_url:
                            success = url_to_image(
                                response.image_url, 
                                str(image_path),
                                aspect_ratio=self.request.aspect_ratio,
                                resolution=self.request.resolution,
                                crop_to_aspect=False  # Не обрезаем автоматически
                            )
                        elif response.image_base64:
                            success = base64_to_image(
                                response.image_base64, 
                                str(image_path),
                                aspect_ratio=self.request.aspect_ratio,
                                resolution=self.request.resolution,
                                crop_to_aspect=False  # Не обрезаем автоматически
                            )
                        else:
                            success = False
                        
                        if success:
                            success_count += 1
                            # Отправляем сигнал для сохранения в БД
                            self.image_saved.emit(
                                str(image_path),
                                prompt.strip(),
                                self.model,
                                self.resolution,
                                self.negative_prompt or ""
                            )
                except Exception as e:
                    pass  # Продолжаем с следующим промптом
            
            message = f"Пакетная генерация завершена: {success_count}/{total} успешно"
            self.finished.emit(success_count > 0, message, "")
        else:
            # Одиночная генерация
            try:
                response = self.client.generate_image(self.request, self.reference_urls if self.reference_urls else None)
                if response.success:
                    # Сохраняем изображение
                    config = Config()
                    images_dir = Path(config.ensure_images_dir())
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_path = images_dir / f"generated_{timestamp}.png"
                    
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
                        self.finished.emit(True, "Изображение успешно сгенерировано!", str(image_path))
                    else:
                        self.finished.emit(False, "Ошибка сохранения изображения", "")
                else:
                    self.finished.emit(False, response.error_message or "Неизвестная ошибка", "")
            except Exception as e:
                self.finished.emit(False, f"Ошибка: {str(e)}", "")


class GenerationTab(QWidget):
    """Вкладка для генерации изображений"""
    
    def __init__(self, api_client: NanoBananaAPIClient = None, db_manager: DatabaseManager = None):
        super().__init__()
        self.api_client = api_client
        self.db_manager = db_manager
        self.config = Config()
        self.worker = None
        self.reference_images = []  # Список путей к референсным изображениям
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        
        # Режим работы
        mode_group = QGroupBox("Режим генерации")
        mode_layout = QHBoxLayout()
        self.single_mode_radio = QRadioButton("Одиночная генерация")
        self.single_mode_radio.setChecked(True)
        self.batch_mode_radio = QRadioButton("Пакетная генерация")
        mode_layout.addWidget(self.single_mode_radio)
        mode_layout.addWidget(self.batch_mode_radio)
        mode_layout.addStretch()
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Промпт
        prompt_group = QGroupBox("Текстовое описание")
        prompt_layout = QVBoxLayout()
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText(
            "Одиночная генерация: Введите описание изображения...\n\n"
            "Пакетная генерация: Введите несколько описаний, каждое с новой строки..."
        )
        self.prompt_text.setMinimumHeight(100)
        prompt_layout.addWidget(self.prompt_text)
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        
        # Референсные изображения (только для Pro)
        reference_group = QGroupBox("Референсные изображения (опционально, только для Pro, до 8)")
        reference_layout = QVBoxLayout()
        
        reference_controls = QHBoxLayout()
        self.add_reference_btn = QPushButton("Добавить референс")
        self.add_reference_btn.clicked.connect(self.add_reference_image)
        reference_controls.addWidget(self.add_reference_btn)
        
        self.remove_reference_btn = QPushButton("Удалить выбранное")
        self.remove_reference_btn.clicked.connect(self.remove_selected_reference)
        self.remove_reference_btn.setEnabled(False)
        reference_controls.addWidget(self.remove_reference_btn)
        
        self.clear_references_btn = QPushButton("Очистить все")
        self.clear_references_btn.clicked.connect(self.clear_references)
        reference_controls.addWidget(self.clear_references_btn)
        
        reference_controls.addStretch()
        self.reference_count_label = QLabel("Референсов: 0/8")
        reference_controls.addWidget(self.reference_count_label)
        
        reference_layout.addLayout(reference_controls)
        
        self.references_list = QListWidget()
        self.references_list.itemSelectionChanged.connect(self.on_reference_selection_changed)
        self.references_list.setMaximumHeight(200)
        self.references_list.setIconSize(QSize(80, 80))  # Размер иконок
        self.references_list.setViewMode(QListWidget.IconMode)  # Режим иконок
        reference_layout.addWidget(self.references_list)
        
        reference_group.setLayout(reference_layout)
        layout.addWidget(reference_group)
        
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
        params_group = QGroupBox("Параметры генерации")
        params_layout = QVBoxLayout()
        
        # Модель
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Flash (быстро, дешево)", "Pro (качественно, дороже)"])
        # Подключаем сигнал для обновления видимости референсов
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
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
        # Общие соотношения для обеих моделей
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
        
        # Количество изображений
        num_layout = QHBoxLayout()
        num_layout.addWidget(QLabel("Количество изображений:"))
        self.num_images_spin = QSpinBox()
        self.num_images_spin.setMinimum(1)
        self.num_images_spin.setMaximum(10)
        self.num_images_spin.setValue(1)
        num_layout.addWidget(self.num_images_spin)
        num_layout.addStretch()
        params_layout.addLayout(num_layout)
        
        # Seed (опционально)
        seed_layout = QHBoxLayout()
        self.seed_checkbox = QCheckBox("Использовать seed (для воспроизводимости)")
        seed_layout.addWidget(self.seed_checkbox)
        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("Число")
        self.seed_input.setEnabled(False)
        self.seed_checkbox.toggled.connect(self.seed_input.setEnabled)
        seed_layout.addWidget(self.seed_input)
        seed_layout.addStretch()
        params_layout.addLayout(seed_layout)
        
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
        
        # Статус пакетной генерации
        self.batch_status_label = QLabel("")
        self.batch_status_label.setVisible(False)
        layout.addWidget(self.batch_status_label)
        
        # Кнопка генерации
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.generate_btn = QPushButton("Сгенерировать")
        self.generate_btn.clicked.connect(self.generate_image)
        self.generate_btn.setMinimumWidth(150)
        button_layout.addWidget(self.generate_btn)
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
    
    def generate_image(self):
        """Генерация изображения"""
        if not self.api_client:
            QMessageBox.warning(self, "Ошибка", "API ключ не установлен!")
            return
        
        prompt_text = self.prompt_text.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите описание изображения!")
            return
        
        # Проверяем режим работы
        batch_mode = self.batch_mode_radio.isChecked()
        prompts_list = []
        
        if batch_mode:
            # Пакетная генерация - разбиваем по строкам
            prompts_list = [p.strip() for p in prompt_text.split('\n') if p.strip()]
            if not prompts_list:
                QMessageBox.warning(self, "Ошибка", "Введите хотя бы один промпт для пакетной генерации!")
                return
            if len(prompts_list) > 50:
                reply = QMessageBox.question(
                    self, "Подтверждение",
                    f"Вы собираетесь сгенерировать {len(prompts_list)} изображений. Продолжить?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            prompt = prompts_list[0]  # Для создания базового запроса
        else:
            prompt = prompt_text
        
        # Получаем параметры
        model = "pro" if self.model_combo.currentIndex() == 1 else "flash"
        resolution_map = {"1024x1024 (1K)": "1024", "2048x2048 (2K)": "2048", "4096x4096 (4K)": "4096"}
        resolution = resolution_map[self.resolution_combo.currentText()]
        num_images = self.num_images_spin.value()
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
        
        seed = None
        if self.seed_checkbox.isChecked():
            try:
                seed = int(self.seed_input.text())
            except:
                pass
        
        # Проверяем референсные изображения
        reference_images = self.reference_images.copy() if self.reference_images else []
        
        # Если выбрана Flash модель и есть референсы - предупреждаем
        if model == "flash" and reference_images:
            reply = QMessageBox.question(
                self, "Предупреждение",
                "Референсные изображения поддерживаются только в Pro модели.\n"
                "Переключиться на Pro модель?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.model_combo.setCurrentIndex(1)
                model = "pro"
            else:
                reference_images = []  # Убираем референсы для Flash
        
        # Создаем запрос
        request = GenerationRequest(
            prompt=prompt,
            model=model,
            resolution=resolution,
            negative_prompt=negative_prompt,
            num_images=1 if batch_mode else num_images,  # В пакетном режиме всегда 1
            seed=seed,
            aspect_ratio=aspect_ratio,
            reference_images=reference_images if reference_images else None
        )
        
        # Блокируем кнопку
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        if batch_mode:
            self.progress_bar.setRange(0, len(prompts_list))
            self.progress_bar.setValue(0)
            self.batch_status_label.setVisible(True)
            self.batch_status_label.setText(f"Генерация 0/{len(prompts_list)}...")
        else:
            self.progress_bar.setRange(0, 0)  # Неопределенный прогресс
            self.batch_status_label.setVisible(False)
        
        # Если есть референсы, загружаем их на публичные URL
        reference_urls = []
        if reference_images:
            self.batch_status_label.setVisible(True)
            self.batch_status_label.setText("Загрузка референсных изображений...")
            
            for idx, ref_path in enumerate(reference_images, 1):
                self.batch_status_label.setText(f"Загрузка референса {idx}/{len(reference_images)}...")
                ref_url = upload_image(ref_path)
                if ref_url:
                    reference_urls.append(ref_url)
                else:
                    QMessageBox.warning(
                        self, "Ошибка",
                        f"Не удалось загрузить референсное изображение: {Path(ref_path).name}\n"
                        "Генерация продолжится без этого референса."
                    )
            
            if not reference_urls and reference_images:
                QMessageBox.warning(
                    self, "Ошибка",
                    "Не удалось загрузить ни одного референсного изображения.\n"
                    "Генерация продолжится без референсов."
                )
        
        # Получаем значение чекбокса обрезки
        crop_to_aspect = self.crop_to_aspect_checkbox.isChecked()
        
        # Запускаем генерацию в отдельном потоке
        self.worker = GenerationWorker(
            self.api_client, 
            request, 
            batch_mode, 
            prompts_list if batch_mode else None,
            reference_urls if reference_urls else None,
            crop_to_aspect
        )
        if batch_mode:
            self.worker.progress.connect(self.on_batch_progress)
            self.worker.image_saved.connect(self.on_batch_image_saved)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.start()
    
    def on_batch_progress(self, current: int, total: int, prompt: str):
        """Обработка прогресса пакетной генерации"""
        self.progress_bar.setValue(current)
        self.batch_status_label.setText(f"Генерация {current}/{total}: {prompt[:50]}...")
    
    def add_reference_image(self):
        """Добавить референсное изображение"""
        if len(self.reference_images) >= 8:
            QMessageBox.warning(self, "Ошибка", "Максимум 8 референсных изображений!")
            return
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите референсные изображения",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        for file_path in file_paths:
            if file_path not in self.reference_images and len(self.reference_images) < 8:
                self.reference_images.append(file_path)
                # Создаем миниатюру
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # Масштабируем до 80x80 с сохранением пропорций
                    scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item = QListWidgetItem(Path(file_path).name)
                    item.setIcon(QIcon(scaled_pixmap))
                    item.setData(Qt.UserRole, file_path)
                    item.setToolTip(file_path)  # Показываем полный путь при наведении
                    self.references_list.addItem(item)
                else:
                    # Если не удалось загрузить изображение, добавляем без иконки
                    item = QListWidgetItem(Path(file_path).name)
                    item.setData(Qt.UserRole, file_path)
                    self.references_list.addItem(item)
        
        self.update_reference_count()
    
    def remove_selected_reference(self):
        """Удалить выбранное референсное изображение"""
        current_item = self.references_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.UserRole)
            if file_path in self.reference_images:
                self.reference_images.remove(file_path)
            self.references_list.takeItem(self.references_list.row(current_item))
            self.update_reference_count()
    
    def clear_references(self):
        """Очистить все референсные изображения"""
        self.reference_images.clear()
        self.references_list.clear()
        self.update_reference_count()
    
    def update_reference_count(self):
        """Обновить счетчик референсов"""
        self.reference_count_label.setText(f"Референсов: {len(self.reference_images)}/8")
    
    def on_reference_selection_changed(self):
        """Обработка изменения выбора референса"""
        self.remove_reference_btn.setEnabled(self.references_list.currentItem() is not None)
    
    def on_model_changed(self, index: int):
        """Обработка смены модели"""
        # Референсы работают только с Pro моделью
        is_pro = index == 1
        reference_group = self.references_list.parent().parent()
        reference_group.setEnabled(is_pro)
        
        if not is_pro and self.reference_images:
            reply = QMessageBox.question(
                self, "Предупреждение",
                "Референсные изображения поддерживаются только в Pro модели.\n"
                "Очистить список референсов?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.clear_references()
    
    def on_batch_image_saved(self, image_path: str, prompt: str, model: str, resolution: str, negative_prompt: str):
        """Обработка сохранения изображения в пакетном режиме"""
        if self.db_manager:
            self.db_manager.add_generation(
                gen_type="generate",
                prompt=prompt,
                model=model,
                image_path=image_path,
                resolution=resolution,
                negative_prompt=negative_prompt if negative_prompt else None
            )
    
    def on_generation_finished(self, success: bool, message: str, image_path: str):
        """Обработка завершения генерации"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.batch_status_label.setVisible(False)
        
        if success:
            # Сохраняем в БД (только для одиночной генерации)
            if self.db_manager and image_path and not self.batch_mode_radio.isChecked():
                model = "pro" if self.model_combo.currentIndex() == 1 else "flash"
                resolution = self.resolution_combo.currentText().split()[0]
                self.db_manager.add_generation(
                    gen_type="generate",
                    prompt=self.prompt_text.toPlainText(),
                    model=model,
                    image_path=image_path,
                    resolution=resolution,
                    negative_prompt=self.negative_prompt_text.toPlainText().strip() or None
                )
            
            QMessageBox.information(self, "Успех", message)
            # Можно добавить сигнал для обновления галереи
        else:
            QMessageBox.critical(self, "Ошибка", message)

