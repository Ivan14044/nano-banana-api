"""
Вкладка галереи для просмотра истории генераций
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QMessageBox, QFileDialog,
                             QGridLayout, QScrollArea, QFrame, QCheckBox, QDialog,
                             QTextEdit, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from database.db_manager import DatabaseManager
from gui.image_viewer import ImageViewer
from pathlib import Path
import shutil
from datetime import datetime


class GalleryTab(QWidget):
    """Вкладка галереи"""
    
    image_selected = pyqtSignal(str)  # Сигнал выбора изображения
    
    def __init__(self, db_manager: DatabaseManager = None):
        super().__init__()
        self.db_manager = db_manager
        self.generations = []
        self.selected_images = set()  # Множество выбранных изображений
        self.thumbnail_widgets = {}  # Словарь {image_path: (frame, checkbox)}
        self.init_ui()
        self.load_gallery()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        
        # Панель управления
        controls_layout = QHBoxLayout()
        
        # Поиск
        controls_layout.addWidget(QLabel("Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по промпту...")
        self.search_input.textChanged.connect(self.on_search_changed)
        controls_layout.addWidget(self.search_input)
        
        # Фильтр по типу
        controls_layout.addWidget(QLabel("Тип:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Все", "Генерация", "Редактирование", "Комбинирование"])
        self.type_filter.currentIndexChanged.connect(self.load_gallery)
        controls_layout.addWidget(self.type_filter)
        
        controls_layout.addStretch()
        
        # Кнопка скачивания выбранных
        self.download_selected_btn = QPushButton("Скачать выбранные")
        self.download_selected_btn.clicked.connect(self.download_selected_images)
        self.download_selected_btn.setEnabled(False)
        controls_layout.addWidget(self.download_selected_btn)
        
        # Кнопка удаления выбранных
        self.delete_selected_btn = QPushButton("Удалить выбранные")
        self.delete_selected_btn.clicked.connect(self.delete_selected_images)
        self.delete_selected_btn.setEnabled(False)
        controls_layout.addWidget(self.delete_selected_btn)
        
        # Кнопка выбора всех
        select_all_btn = QPushButton("Выбрать все")
        select_all_btn.clicked.connect(self.select_all_images)
        controls_layout.addWidget(select_all_btn)
        
        # Кнопка снятия выбора
        deselect_all_btn = QPushButton("Снять выбор")
        deselect_all_btn.clicked.connect(self.deselect_all_images)
        controls_layout.addWidget(deselect_all_btn)
        
        # Кнопка обновления
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_gallery)
        controls_layout.addWidget(refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Область прокрутки для галереи
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignTop)
        
        self.gallery_widget = QWidget()
        self.gallery_layout = QGridLayout()
        self.gallery_layout.setSpacing(10)
        self.gallery_widget.setLayout(self.gallery_layout)
        
        scroll_area.setWidget(self.gallery_widget)
        layout.addWidget(scroll_area, stretch=1)  # Область галереи занимает все доступное пространство
        
        # Статистика
        self.stats_label = QLabel("")
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
    
    def set_db_manager(self, db_manager: DatabaseManager):
        """Установить менеджер БД"""
        self.db_manager = db_manager
        self.load_gallery()
    
    def load_gallery(self):
        """Загрузка галереи"""
        if not self.db_manager:
            return
        
        # Очищаем текущую галерею
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Очищаем словарь виджетов
        self.thumbnail_widgets.clear()
        self.selected_images.clear()
        self.update_download_button()
        
        # Получаем фильтры
        gen_type = None
        type_map = {"Генерация": "generate", "Редактирование": "edit", "Комбинирование": "combine"}
        if self.type_filter.currentIndex() > 0:
            gen_type = type_map[self.type_filter.currentText()]
        
        search_query = self.search_input.text().strip() or None
        
        # Загружаем генерации
        self.generations = self.db_manager.get_generations(
            limit=100,
            gen_type=gen_type,
            search_query=search_query
        )
        
        # Отображаем миниатюры
        row = 0
        col = 0
        max_cols = 4
        
        for gen in self.generations:
            image_path = gen.get("image_path")
            if image_path and Path(image_path).exists():
                thumbnail_widget = self.create_thumbnail_widget(gen)
                self.gallery_layout.addWidget(thumbnail_widget, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        
        # Обновляем статистику
        stats = self.db_manager.get_statistics()
        self.stats_label.setText(
            f"Всего: {stats['total']} | "
            f"Генераций: {stats['by_type'].get('generate', 0)} | "
            f"Редактирований: {stats['by_type'].get('edit', 0)} | "
            f"Комбинирований: {stats['by_type'].get('combine', 0)}"
        )
    
    def create_thumbnail_widget(self, gen: dict) -> QFrame:
        """Создать виджет миниатюры"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Box)
        frame.setStyleSheet("border: 1px solid #3d3d3d; border-radius: 4px; padding: 5px;")
        frame.setFixedSize(200, 300)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Чекбокс для выбора
        image_path = gen.get("image_path")
        checkbox = QCheckBox()
        checkbox.setChecked(image_path in self.selected_images)
        checkbox.stateChanged.connect(lambda state, path=image_path: self.on_image_selection_changed(path, state))
        layout.addWidget(checkbox)
        
        # Миниатюра изображения
        image_label = QLabel()
        if image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(180, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
            else:
                image_label.setText("Ошибка загрузки")
        else:
            image_label.setText("Нет изображения")
        
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet("background-color: #2d2d2d; border-radius: 2px;")
        layout.addWidget(image_label)
        
        # Информация
        info_label = QLabel()
        prompt = gen.get("prompt", "")[:50]
        if len(gen.get("prompt", "")) > 50:
            prompt += "..."
        info_label.setText(f"{gen.get('type', 'unknown')}\n{prompt}")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 9pt; color: #cccccc;")
        layout.addWidget(info_label)
        
        # Кнопки
        buttons_layout = QVBoxLayout()
        
        # Первая строка кнопок
        buttons_row1 = QHBoxLayout()
        prompt_btn = QPushButton("Промпт")
        prompt_btn.clicked.connect(lambda checked, g=gen: self.view_prompt(g))
        buttons_row1.addWidget(prompt_btn)
        
        view_btn = QPushButton("Просмотр")
        view_btn.clicked.connect(lambda checked, path=image_path: self.view_image(path))
        buttons_row1.addWidget(view_btn)
        buttons_layout.addLayout(buttons_row1)
        
        # Вторая строка кнопок
        buttons_row2 = QHBoxLayout()
        download_btn = QPushButton("Скачать")
        download_btn.clicked.connect(lambda checked, path=image_path: self.download_image(path))
        buttons_row2.addWidget(download_btn)
        
        delete_btn = QPushButton("Удалить")
        delete_btn.setStyleSheet("background-color: #8b0000; color: white;")
        delete_btn.clicked.connect(lambda checked, path=image_path, g=gen: self.delete_image(path, g))
        buttons_row2.addWidget(delete_btn)
        buttons_layout.addLayout(buttons_row2)
        
        layout.addLayout(buttons_layout)
        
        frame.setLayout(layout)
        
        # Сохраняем виджет в словаре
        if image_path:
            self.thumbnail_widgets[image_path] = (frame, checkbox)
        
        return frame
    
    def view_prompt(self, gen: dict):
        """Просмотр полного промпта и информации о генерации"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Информация о генерации")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Промпт
        prompt_label = QLabel("Промпт:")
        prompt_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(prompt_label)
        
        prompt_text = QTextEdit()
        prompt_text.setPlainText(gen.get("prompt", "Не указан"))
        prompt_text.setReadOnly(True)
        prompt_text.setMaximumHeight(150)
        layout.addWidget(prompt_text)
        
        # Негативный промпт (если есть)
        if gen.get("negative_prompt"):
            negative_label = QLabel("Негативный промпт:")
            negative_label.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px;")
            layout.addWidget(negative_label)
            
            negative_text = QTextEdit()
            negative_text.setPlainText(gen.get("negative_prompt", ""))
            negative_text.setReadOnly(True)
            negative_text.setMaximumHeight(100)
            layout.addWidget(negative_text)
        
        # Информация о параметрах
        info_label = QLabel("Параметры генерации:")
        info_label.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px;")
        layout.addWidget(info_label)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        
        # Формируем информацию
        type_map = {
            "generate": "Генерация",
            "edit": "Редактирование",
            "combine": "Комбинирование"
        }
        gen_type = type_map.get(gen.get("type", "unknown"), gen.get("type", "unknown"))
        
        model = gen.get("model", "Не указана")
        resolution = gen.get("resolution", "Не указано")
        
        created_at = gen.get("created_at", "")
        if created_at:
            try:
                # Парсим дату если она в формате строки
                if isinstance(created_at, str):
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = dt.strftime("%d.%m.%Y %H:%M:%S")
            except:
                pass
        
        info_lines = [
            f"Тип: {gen_type}",
            f"Модель: {model}",
            f"Разрешение: {resolution}",
            f"Дата создания: {created_at or 'Не указана'}"
        ]
        
        image_path = gen.get("image_path", "")
        if image_path:
            info_lines.append(f"Путь к файлу: {image_path}")
        
        info_text.setPlainText("\n".join(info_lines))
        layout.addWidget(info_text)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def view_image(self, image_path: str):
        """Просмотр изображения"""
        if image_path and Path(image_path).exists():
            viewer = ImageViewer(image_path, self)
            viewer.exec_()
        else:
            QMessageBox.warning(self, "Ошибка", "Изображение не найдено!")
    
    def download_image(self, image_path: str):
        """Скачать одно изображение"""
        if not image_path or not Path(image_path).exists():
            QMessageBox.warning(self, "Ошибка", "Изображение не найдено!")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить изображение",
            Path(image_path).name,
            "Изображения (*.png *.jpg *.jpeg)"
        )
        
        if save_path:
            try:
                shutil.copy2(image_path, save_path)
                QMessageBox.information(self, "Успех", "Изображение сохранено!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")
    
    def on_image_selection_changed(self, image_path: str, state: int):
        """Обработка изменения выбора изображения"""
        if state == Qt.Checked:
            self.selected_images.add(image_path)
        else:
            self.selected_images.discard(image_path)
        self.update_download_button()
    
    def update_download_button(self):
        """Обновить состояние кнопок скачивания и удаления"""
        has_selected = len(self.selected_images) > 0
        self.download_selected_btn.setEnabled(has_selected)
        self.delete_selected_btn.setEnabled(has_selected)
        
        if has_selected:
            self.download_selected_btn.setText(f"Скачать выбранные ({len(self.selected_images)})")
            self.delete_selected_btn.setText(f"Удалить выбранные ({len(self.selected_images)})")
        else:
            self.download_selected_btn.setText("Скачать выбранные")
            self.delete_selected_btn.setText("Удалить выбранные")
    
    def select_all_images(self):
        """Выбрать все изображения"""
        for image_path, (frame, checkbox) in self.thumbnail_widgets.items():
            if Path(image_path).exists():
                checkbox.setChecked(True)
                self.selected_images.add(image_path)
        self.update_download_button()
    
    def deselect_all_images(self):
        """Снять выбор со всех изображений"""
        for image_path, (frame, checkbox) in self.thumbnail_widgets.items():
            checkbox.setChecked(False)
        self.selected_images.clear()
        self.update_download_button()
    
    def download_selected_images(self):
        """Скачать выбранные изображения"""
        if not self.selected_images:
            QMessageBox.warning(self, "Ошибка", "Не выбрано ни одного изображения!")
            return
        
        # Выбираем папку для сохранения
        save_dir = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения изображений"
        )
        
        if not save_dir:
            return
        
        # Копируем все выбранные изображения
        success_count = 0
        error_count = 0
        
        for image_path in self.selected_images:
            if not Path(image_path).exists():
                error_count += 1
                continue
            
            try:
                # Сохраняем с оригинальным именем
                dest_path = Path(save_dir) / Path(image_path).name
                # Если файл уже существует, добавляем номер
                counter = 1
                original_dest = dest_path
                while dest_path.exists():
                    stem = original_dest.stem
                    suffix = original_dest.suffix
                    dest_path = Path(save_dir) / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                shutil.copy2(image_path, dest_path)
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Ошибка при копировании {image_path}: {e}")
        
        # Показываем результат
        if error_count == 0:
            QMessageBox.information(
                self, "Успех",
                f"Успешно сохранено {success_count} изображений в:\n{save_dir}"
            )
        else:
            QMessageBox.warning(
                self, "Завершено",
                f"Сохранено: {success_count}\nОшибок: {error_count}"
            )
    
    def on_search_changed(self):
        """Обработка изменения поискового запроса"""
        self.load_gallery()
    
    def delete_image(self, image_path: str, gen: dict = None):
        """Удалить одно изображение"""
        if not image_path:
            return
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить это изображение?\n\n"
            f"Файл: {Path(image_path).name}\n\n"
            "Изображение будет удалено из базы данных и файловой системы.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Удаляем из БД
        deleted_from_db = False
        if self.db_manager:
            if gen and gen.get("id"):
                deleted_from_db = self.db_manager.delete_generation(gen.get("id"))
            else:
                deleted_from_db = self.db_manager.delete_generation_by_image_path(image_path)
        
        # Удаляем файл
        file_deleted = False
        if Path(image_path).exists():
            try:
                Path(image_path).unlink()
                file_deleted = True
            except Exception as e:
                QMessageBox.warning(
                    self, "Ошибка",
                    f"Не удалось удалить файл:\n{str(e)}"
                )
        
        # Удаляем из выбранных
        self.selected_images.discard(image_path)
        
        # Обновляем галерею
        self.load_gallery()
        
        # Показываем результат
        if deleted_from_db and file_deleted:
            QMessageBox.information(self, "Успех", "Изображение успешно удалено!")
        elif deleted_from_db:
            QMessageBox.warning(
                self, "Частично удалено",
                "Запись удалена из базы данных, но файл не был найден."
            )
        elif file_deleted:
            QMessageBox.warning(
                self, "Частично удалено",
                "Файл удален, но запись в базе данных не найдена."
            )
    
    def delete_selected_images(self):
        """Удалить выбранные изображения"""
        if not self.selected_images:
            QMessageBox.warning(self, "Ошибка", "Не выбрано ни одного изображения!")
            return
        
        # Подтверждение удаления
        count = len(self.selected_images)
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить {count} изображений?\n\n"
            "Изображения будут удалены из базы данных и файловой системы.\n"
            "Это действие нельзя отменить!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Удаляем каждое изображение
        deleted_count = 0
        error_count = 0
        
        for image_path in list(self.selected_images):  # Копируем список, так как будем изменять
            # Находим соответствующую запись в БД
            gen = None
            for g in self.generations:
                if g.get("image_path") == image_path:
                    gen = g
                    break
            
            # Удаляем из БД
            deleted_from_db = False
            if self.db_manager:
                if gen and gen.get("id"):
                    deleted_from_db = self.db_manager.delete_generation(gen.get("id"))
                else:
                    deleted_from_db = self.db_manager.delete_generation_by_image_path(image_path)
            
            # Удаляем файл
            file_deleted = False
            if Path(image_path).exists():
                try:
                    Path(image_path).unlink()
                    file_deleted = True
                except Exception as e:
                    print(f"Ошибка при удалении файла {image_path}: {e}")
            
            if deleted_from_db or file_deleted:
                deleted_count += 1
            else:
                error_count += 1
        
        # Очищаем выбранные
        self.selected_images.clear()
        
        # Обновляем галерею
        self.load_gallery()
        
        # Показываем результат
        if error_count == 0:
            QMessageBox.information(
                self, "Успех",
                f"Успешно удалено {deleted_count} изображений!"
            )
        else:
            QMessageBox.warning(
                self, "Завершено",
                f"Удалено: {deleted_count}\nОшибок: {error_count}"
            )

