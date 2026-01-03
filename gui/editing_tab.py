"""
Вкладка для редактирования изображений с поддержкой параллельной обработки
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QLabel, QComboBox, QGroupBox, QFileDialog,
                             QMessageBox, QProgressBar, QListWidget, QListWidgetItem,
                             QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
                             QShortcut, QApplication)
from PyQt5.QtCore import Qt, QThreadPool, QRunnable, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QPixmap, QIcon, QKeySequence, QImage
from api.client import NanoBananaAPIClient
from api.models import EditRequest
from utils.image_utils import url_to_image, base64_to_image
from utils.image_uploader import upload_image
from utils.config import Config
from database.db_manager import DatabaseManager
from pathlib import Path
from datetime import datetime


class EditWorkerSignals(QObject):
    """Сигналы для воркера редактирования"""
    finished = pyqtSignal(int, bool, str, str, str)  # index, success, message, image_path, prompt
    progress = pyqtSignal(int, str)  # index, message


class EditWorker(QRunnable):
    """Воркер для параллельного редактирования изображений"""
    
    def __init__(self, index: int, client: NanoBananaAPIClient, request: EditRequest, crop_to_aspect=False, prompt: str = None):
        super().__init__()
        self.index = index
        self.client = client
        self.request = request
        self.signals = EditWorkerSignals()
        self.crop_to_aspect = crop_to_aspect
        self.prompt = prompt or request.prompt  # Сохраняем промпт для сохранения в БД
    
    def run(self):
        """Выполнение редактирования"""
        try:
            self.signals.progress.emit(self.index, "Загрузка изображения на сервер...")
            image_url = upload_image(self.request.image_path)
            
            if not image_url:
                error_msg = (
                    f"Не удалось загрузить изображение {Path(self.request.image_path).name} на публичный URL.\n\n"
                    "Возможные причины:\n"
                    "• Проблемы с интернет-соединением\n"
                    "• Временная недоступность сервисов загрузки\n"
                    "• Файл слишком большой"
                )
                self.signals.finished.emit(self.index, False, error_msg, "")
                return
            
            self.signals.progress.emit(self.index, "Изображение загружено. Отправка запроса...")
            response = self.client.edit_image(self.request, image_url)
            
            if response.success:
                # Сохраняем изображение
                config = Config()
                images_dir = Path(config.ensure_images_dir())
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = images_dir / f"edited_{self.index}_{timestamp}.png"
                
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
                    self.signals.finished.emit(self.index, True, "Успешно отредактировано!", str(image_path), self.prompt)
                else:
                    self.signals.finished.emit(self.index, False, "Ошибка сохранения изображения", "", self.prompt)
            else:
                self.signals.finished.emit(self.index, False, response.error_message or "Неизвестная ошибка", "", self.prompt)
        except Exception as e:
            self.signals.finished.emit(self.index, False, f"Ошибка: {str(e)}", "", self.prompt)


class EditingTab(QWidget):
    """Вкладка для редактирования изображений с параллельной обработкой"""
    
    def __init__(self, api_client: NanoBananaAPIClient = None, db_manager: DatabaseManager = None):
        super().__init__()
        self.api_client = api_client
        self.db_manager = db_manager
        self.config = Config()
        self.image_paths = []
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(5)  # Максимум 5 параллельных задач
        self.active_workers = {}  # Словарь активных воркеров {index: worker}
        self.results = {}  # Результаты обработки {index: (success, message, image_path)}
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        
        # Загрузка изображений
        image_group = QGroupBox("Изображения для редактирования")
        image_layout = QVBoxLayout()
        
        image_controls = QHBoxLayout()
        self.load_images_btn = QPushButton("Добавить изображения")
        self.load_images_btn.clicked.connect(self.load_images)
        image_controls.addWidget(self.load_images_btn)
        
        # Кнопка вставки из буфера обмена
        self.paste_image_btn = QPushButton("Вставить из буфера")
        self.paste_image_btn.clicked.connect(self.paste_image_from_clipboard)
        image_controls.addWidget(self.paste_image_btn)
        
        self.remove_image_btn = QPushButton("Удалить выбранное")
        self.remove_image_btn.clicked.connect(self.remove_selected_image)
        self.remove_image_btn.setEnabled(False)
        image_controls.addWidget(self.remove_image_btn)
        
        self.clear_images_btn = QPushButton("Очистить все")
        self.clear_images_btn.clicked.connect(self.clear_images)
        image_controls.addWidget(self.clear_images_btn)
        
        image_controls.addStretch()
        self.image_count_label = QLabel("Изображений: 0")
        image_controls.addWidget(self.image_count_label)
        
        image_layout.addLayout(image_controls)
        
        self.images_list = QListWidget()
        self.images_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.images_list.setMaximumHeight(200)
        self.images_list.setIconSize(QSize(100, 100))  # Размер иконок
        self.images_list.setViewMode(QListWidget.IconMode)  # Режим иконок
        image_layout.addWidget(self.images_list)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # Инструкции по редактированию
        prompt_group = QGroupBox("Инструкции по редактированию")
        prompt_layout = QVBoxLayout()
        self.edit_prompt_text = QTextEdit()
        self.edit_prompt_text.setPlaceholderText("Опишите, как нужно изменить изображения...\n(Если загружено 1 изображение, каждая строка = отдельный промпт)")
        self.edit_prompt_text.setMinimumHeight(100)
        self.edit_prompt_text.textChanged.connect(self.update_prompt_count)  # Подключаем обновление счетчика
        prompt_layout.addWidget(self.edit_prompt_text)
        
        # Метка с информацией о промптах
        self.prompt_info_label = QLabel("Промптов: 0 | Задач будет создано: 0")
        self.prompt_info_label.setStyleSheet("color: #888888; font-size: 9pt; padding: 5px;")
        prompt_layout.addWidget(self.prompt_info_label)
        
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
        
        # Модель
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Flash (быстро)", "Pro (качественно)"])
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        params_layout.addLayout(model_layout)
        
        # Разрешение (опционально)
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Разрешение (оставить пустым для исходного):"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["Исходное", "1024x1024 (1K)", "2048x2048 (2K)", "4096x4096 (4K)"])
        self.resolution_combo.setCurrentIndex(0)
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
        
        # Таблица прогресса
        progress_group = QGroupBox("Прогресс редактирования")
        progress_layout = QVBoxLayout()
        
        self.progress_table = QTableWidget()
        self.progress_table.setColumnCount(4)
        self.progress_table.setHorizontalHeaderLabels(["Изображение", "Статус", "Прогресс", "Результат"])
        self.progress_table.horizontalHeader().setStretchLastSection(True)
        self.progress_table.setColumnWidth(0, 200)
        self.progress_table.setColumnWidth(1, 150)
        self.progress_table.setColumnWidth(2, 200)
        self.progress_table.setMaximumHeight(200)
        self.progress_table.setVisible(False)
        progress_layout.addWidget(self.progress_table)
        
        # Общий прогресс
        self.overall_progress = QProgressBar()
        self.overall_progress.setVisible(False)
        progress_layout.addWidget(self.overall_progress)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Кнопка редактирования
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.edit_btn = QPushButton("Редактировать все изображения")
        self.edit_btn.clicked.connect(self.edit_images)
        self.edit_btn.setEnabled(False)
        self.edit_btn.setMinimumWidth(200)
        button_layout.addWidget(self.edit_btn)
        layout.addLayout(button_layout)
        
        layout.addStretch()
        self.setLayout(layout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Инициализируем счетчик промптов
        self.update_prompt_count()
        
        # Горячая клавиша для вставки из буфера обмена (Ctrl+V / Cmd+V)
        self.paste_shortcut = QShortcut(QKeySequence.Paste, self)
        self.paste_shortcut.activated.connect(self.paste_image_from_clipboard)
    
    def set_api_client(self, client: NanoBananaAPIClient):
        """Установить API клиент"""
        self.api_client = client
    
    def set_db_manager(self, db_manager: DatabaseManager):
        """Установить менеджер БД"""
        self.db_manager = db_manager
    
    def load_images(self):
        """Загрузка нескольких изображений"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите изображения",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        for file_path in file_paths:
            self.add_image_to_list(file_path)
    
    def remove_selected_image(self):
        """Удалить выбранное изображение"""
        current_item = self.images_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.UserRole)
            if file_path in self.image_paths:
                self.image_paths.remove(file_path)
            self.images_list.takeItem(self.images_list.row(current_item))
            self.update_image_count()
            self.edit_btn.setEnabled(len(self.image_paths) > 0)
    
    def clear_images(self):
        """Очистить все изображения"""
        self.image_paths.clear()
        self.images_list.clear()
        self.update_image_count()
        self.edit_btn.setEnabled(False)
    
    def add_image_to_list(self, file_path: str, label_prefix: str = None):
        """Добавить изображение в список с миниатюрой"""
        if file_path in self.image_paths:
            return
        
        self.image_paths.append(file_path)
        pixmap = QPixmap(file_path)
        item_name = Path(file_path).name
        if label_prefix:
            item_name = f"{label_prefix}: {item_name}"
        
        if not pixmap.isNull():
            # Масштабируем до 100x100 с сохранением пропорций
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item = QListWidgetItem(item_name)
            item.setIcon(QIcon(scaled_pixmap))
        else:
            item = QListWidgetItem(item_name)
        
        item.setData(Qt.UserRole, file_path)
        item.setToolTip(file_path)  # Полный путь при наведении
        self.images_list.addItem(item)
        
        # Обновляем счетчики и кнопку
        self.update_image_count()
        self.edit_btn.setEnabled(len(self.image_paths) > 0)
    
    def paste_image_from_clipboard(self):
        """Вставка изображения из буфера обмена"""
        clipboard = QApplication.clipboard()
        image: QImage = clipboard.image()
        
        if image.isNull():
            QMessageBox.warning(self, "Буфер обмена пуст", "В буфере нет изображения для вставки.")
            return
        
        images_dir = Path(self.config.ensure_images_dir())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = images_dir / f"pasted_{timestamp}.png"
        
        # Сохраняем изображение из буфера
        if not image.save(str(file_path), "PNG"):
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить изображение из буфера обмена.")
            return
        
        # Добавляем в список с отметкой, что источник — буфер обмена
        self.add_image_to_list(str(file_path), label_prefix="Буфер обмена")
    
    def update_image_count(self):
        """Обновить счетчик изображений"""
        self.image_count_label.setText(f"Изображений: {len(self.image_paths)}")
        self.update_prompt_count()  # Обновляем также счетчик промптов при изменении изображений
    
    def update_prompt_count(self):
        """Обновить счетчик промптов и информацию о количестве задач"""
        prompt_text = self.edit_prompt_text.toPlainText().strip()
        
        if not prompt_text:
            self.prompt_info_label.setText("Промптов: 0 | Задач будет создано: 0")
            return
        
        # Разбиваем промпты по строкам
        prompts_list = [p.strip() for p in prompt_text.split('\n') if p.strip()]
        num_prompts = len(prompts_list)
        
        # Вычисляем количество задач, которые будут созданы
        if len(self.image_paths) == 0:
            num_tasks = 0
        elif len(self.image_paths) == 1 and num_prompts > 1:
            # Режим: одно изображение, несколько промптов
            num_tasks = num_prompts
        else:
            # Режим: несколько изображений или один промпт
            num_tasks = len(self.image_paths)
        
        # Формируем текст с информацией
        if num_prompts == 1:
            prompt_text_info = f"Промптов: {num_prompts}"
        else:
            prompt_text_info = f"Промптов: {num_prompts}"
        
        if num_tasks == 0:
            tasks_text = "Задач будет создано: 0"
        elif num_tasks == 1:
            tasks_text = "Задач будет создано: 1"
        else:
            tasks_text = f"Задач будет создано: {num_tasks}"
        
        # Дополнительная информация о режиме работы
        if len(self.image_paths) == 1 and num_prompts > 1:
            mode_info = " (1 изображение × несколько промптов)"
        elif len(self.image_paths) > 1 and num_prompts == 1:
            mode_info = f" ({len(self.image_paths)} изображений × 1 промпт)"
        elif len(self.image_paths) > 1 and num_prompts > 1:
            mode_info = f" ({len(self.image_paths)} изображений × 1 промпт - используется первый)"
        else:
            mode_info = ""
        
        self.prompt_info_label.setText(f"{prompt_text_info} | {tasks_text}{mode_info}")
    
    def on_selection_changed(self):
        """Обработка изменения выбора"""
        self.remove_image_btn.setEnabled(self.images_list.currentItem() is not None)
    
    def edit_images(self):
        """Параллельное редактирование всех изображений с поддержкой нескольких промптов для одного изображения"""
        if not self.api_client:
            QMessageBox.warning(self, "Ошибка", "API ключ не установлен!")
            return
        
        if len(self.image_paths) == 0:
            QMessageBox.warning(self, "Ошибка", "Загрузите изображения!")
            return
        
        prompt_text = self.edit_prompt_text.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите инструкции по редактированию!")
            return
        
        # Разбиваем промпты по строкам (каждая строка = отдельный промпт)
        prompts_list = [p.strip() for p in prompt_text.split('\n') if p.strip()]
        if not prompts_list:
            QMessageBox.warning(self, "Ошибка", "Введите хотя бы один промпт!")
            return
        
        # Получаем параметры
        model = "pro" if self.model_combo.currentIndex() == 1 else "flash"
        resolution = None
        if self.resolution_combo.currentIndex() > 0:
            resolution_map = {"1024x1024 (1K)": "1024", "2048x2048 (2K)": "2048", "4096x4096 (4K)": "4096"}
            resolution = resolution_map[self.resolution_combo.currentText()]
        
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
        
        negative_prompt = self.negative_prompt_text.toPlainText().strip() or None
        
        # Определяем режим работы:
        # - Если одно изображение и несколько промптов: каждый промпт для этого изображения
        # - Если несколько изображений: один промпт для всех (как раньше)
        
        tasks = []  # Список задач: (image_path, prompt, task_index)
        task_index = 0
        
        if len(self.image_paths) == 1 and len(prompts_list) > 1:
            # Режим: одно изображение, несколько промптов
            image_path = self.image_paths[0]
            for prompt in prompts_list:
                tasks.append((image_path, prompt, task_index))
                task_index += 1
        else:
            # Режим: несколько изображений или один промпт - используем первый промпт для всех изображений
            prompt = prompts_list[0]
            for image_path in self.image_paths:
                tasks.append((image_path, prompt, task_index))
                task_index += 1
        
        # Предупреждение если задач много
        if len(tasks) > 20:
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Вы собираетесь обработать {len(tasks)} задач. Это может занять много времени. Продолжить?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Очищаем предыдущие результаты
        self.results.clear()
        self.active_workers.clear()
        
        # Настраиваем таблицу прогресса
        self.progress_table.setVisible(True)
        self.progress_table.setRowCount(len(tasks))
        self.total_tasks = len(tasks)  # Сохраняем общее количество задач
        self.overall_progress.setVisible(True)
        self.overall_progress.setRange(0, len(tasks))
        self.overall_progress.setValue(0)
        
        # Блокируем кнопку
        self.edit_btn.setEnabled(False)
        
        # Создаем и запускаем воркеры для каждой задачи
        for image_path, prompt, idx in tasks:
            # Формируем название задачи для таблицы
            image_name = Path(image_path).name
            if len(tasks) > len(self.image_paths):
                # Если несколько промптов для одного изображения
                prompt_preview = prompt[:30] + "..." if len(prompt) > 30 else prompt
                task_name = f"{image_name}\n({prompt_preview})"
            else:
                task_name = image_name
            
            # Заполняем таблицу
            self.progress_table.setItem(idx, 0, QTableWidgetItem(task_name))
            self.progress_table.setItem(idx, 1, QTableWidgetItem("Ожидание..."))
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 0)  # Неопределенный прогресс
            self.progress_table.setCellWidget(idx, 2, progress_bar)
            self.progress_table.setItem(idx, 3, QTableWidgetItem(""))
            
            # Создаем запрос
            request = EditRequest(
                image_path=image_path,
                prompt=prompt,
                model=model,
                resolution=resolution,
                negative_prompt=negative_prompt,
                aspect_ratio=aspect_ratio
            )
            
            # Получаем значение чекбокса обрезки
            crop_to_aspect = self.crop_to_aspect_checkbox.isChecked()
            
            # Создаем и запускаем воркер (передаем промпт для сохранения в БД)
            worker = EditWorker(idx, self.api_client, request, crop_to_aspect, prompt)
            worker.signals.progress.connect(lambda idx, msg, i=idx: self.on_worker_progress(i, msg))
            # Используем замыкание для сохранения промпта
            worker.signals.finished.connect(lambda idx, success, msg, path, p, i=idx, prompt_val=prompt: self.on_worker_finished(i, success, msg, path, prompt_val))
            self.active_workers[idx] = worker
            self.thread_pool.start(worker)
    
    def on_worker_progress(self, index: int, message: str):
        """Обработка прогресса воркера"""
        if index < self.progress_table.rowCount():
            self.progress_table.setItem(index, 1, QTableWidgetItem(message))
    
    def on_worker_finished(self, index: int, success: bool, message: str, image_path: str, prompt: str = None):
        """Обработка завершения воркера"""
        # Удаляем из активных
        if index in self.active_workers:
            del self.active_workers[index]
        
        # Обновляем таблицу
        if index < self.progress_table.rowCount():
            status = "✅ Готово" if success else "❌ Ошибка"
            self.progress_table.setItem(index, 1, QTableWidgetItem(status))
            
            # Убираем прогресс-бар
            self.progress_table.removeCellWidget(index, 2)
            self.progress_table.setItem(index, 2, QTableWidgetItem(""))
            
            # Показываем результат
            result_text = Path(image_path).name if success and image_path else message[:50]
            self.progress_table.setItem(index, 3, QTableWidgetItem(result_text))
        
        # Сохраняем результат вместе с промптом
        self.results[index] = (success, message, image_path, prompt)
        
        # Сохраняем в БД если успешно
        if success and image_path and self.db_manager:
            model = "pro" if self.model_combo.currentIndex() == 1 else "flash"
            resolution = self.resolution_combo.currentText() if self.resolution_combo.currentIndex() > 0 else None
            # Используем промпт из параметра или из текстового поля
            prompt_to_save = prompt if prompt else self.edit_prompt_text.toPlainText()
            
            self.db_manager.add_generation(
                gen_type="edit",
                prompt=prompt_to_save,
                model=model,
                image_path=image_path,
                resolution=resolution,
                negative_prompt=self.negative_prompt_text.toPlainText().strip() or None
            )
        
        # Обновляем общий прогресс
        completed = len(self.results)
        self.overall_progress.setValue(completed)
        
        # Если все завершены
        total_tasks = getattr(self, 'total_tasks', len(self.image_paths))
        if len(self.results) >= total_tasks:
            self.edit_btn.setEnabled(True)
            
            # Показываем итоговое сообщение
            success_count = sum(1 for r in self.results.values() if r[0])
            total = total_tasks
            
            if success_count == total:
                QMessageBox.information(
                    self, "Успех",
                    f"Все {total} задач успешно выполнены!"
                )
            else:
                QMessageBox.warning(
                    self, "Завершено",
                    f"Обработка завершена:\n"
                    f"✅ Успешно: {success_count}\n"
                    f"❌ Ошибок: {total - success_count}"
                )
