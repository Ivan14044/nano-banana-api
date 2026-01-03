"""
Главное окно приложения
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTabWidget,
                             QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt
from api.client import NanoBananaAPIClient
from database.db_manager import DatabaseManager
from gui.generation_tab import GenerationTab
from gui.editing_tab import EditingTab
from gui.combine_tab import CombineTab
from gui.gallery_tab import GalleryTab
from utils.config import Config


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.api_client = None
        self.db_manager = DatabaseManager()
        self.init_ui()
        self.load_api_key()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("NanoBanana Pro - Генератор изображений")
        self.setMinimumSize(1000, 700)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        
        # Панель настроек API
        api_group = QGroupBox("Настройки API")
        api_layout = QHBoxLayout()
        
        api_layout.addWidget(QLabel("API ключ:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Введите ваш API ключ от nanobananaapi.ai")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        api_layout.addWidget(self.api_key_input, stretch=1)  # Поле ввода растягивается
        
        self.save_key_btn = QPushButton("Сохранить")
        self.save_key_btn.clicked.connect(self.save_api_key)
        api_layout.addWidget(self.save_key_btn)
        
        self.check_balance_btn = QPushButton("Проверить баланс")
        self.check_balance_btn.clicked.connect(self.check_balance)
        self.check_balance_btn.setEnabled(False)
        api_layout.addWidget(self.check_balance_btn)
        
        api_group.setLayout(api_layout)
        main_layout.addWidget(api_group)
        
        # Вкладки
        self.tabs = QTabWidget()
        
        # Вкладка генерации
        self.generation_tab = GenerationTab()
        self.generation_tab.set_db_manager(self.db_manager)
        self.tabs.addTab(self.generation_tab, "Генерация")
        
        # Вкладка редактирования
        self.editing_tab = EditingTab()
        self.editing_tab.set_db_manager(self.db_manager)
        self.tabs.addTab(self.editing_tab, "Редактирование")
        
        # Вкладка комбинирования
        self.combine_tab = CombineTab()
        self.combine_tab.set_db_manager(self.db_manager)
        self.tabs.addTab(self.combine_tab, "Комбинирование")
        
        # Вкладка галереи
        self.gallery_tab = GalleryTab()
        self.gallery_tab.set_db_manager(self.db_manager)
        self.tabs.addTab(self.gallery_tab, "Галерея")
        
        # Подключаем сигнал обновления галереи
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Вкладки занимают все доступное пространство
        main_layout.addWidget(self.tabs, stretch=1)
        
        central_widget.setLayout(main_layout)
        
        # Устанавливаем политику размера для адаптивности
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
    
    def load_api_key(self):
        """Загрузка сохраненного API ключа"""
        api_key = self.config.get("api_key", "")
        # Если ключ не сохранен, используем ключ по умолчанию
        if not api_key:
            api_key = "90672e824ceaf1268cff719d9adbe810"
            self.config.set("api_key", api_key)
        if api_key:
            self.api_key_input.setText(api_key)
            self.set_api_client(api_key)
    
    def on_api_key_changed(self):
        """Обработка изменения API ключа"""
        self.check_balance_btn.setEnabled(bool(self.api_key_input.text().strip()))
    
    def save_api_key(self):
        """Сохранение API ключа"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Ошибка", "Введите API ключ!")
            return
        
        self.config.set("api_key", api_key)
        self.set_api_client(api_key)
        QMessageBox.information(self, "Успех", "API ключ сохранен!")
    
    def set_api_client(self, api_key: str):
        """Установить API клиент"""
        if api_key:
            self.api_client = NanoBananaAPIClient(api_key)
            # Обновляем клиенты во всех вкладках
            self.generation_tab.set_api_client(self.api_client)
            self.editing_tab.set_api_client(self.api_client)
            self.combine_tab.set_api_client(self.api_client)
            self.check_balance_btn.setEnabled(True)
        else:
            self.api_client = None
            self.check_balance_btn.setEnabled(False)
    
    def check_balance(self):
        """Проверка баланса"""
        if not self.api_client:
            QMessageBox.warning(self, "Ошибка", "API ключ не установлен!")
            return
        
        try:
            balance_info = self.api_client.check_balance()
            if balance_info.get("success"):
                QMessageBox.information(self, "Баланс", balance_info.get("message", f"Кредитов: {balance_info.get('credits', 0)}"))
            else:
                QMessageBox.warning(self, "Ошибка", balance_info.get("error", "Неизвестная ошибка"))
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось проверить баланс: {str(e)}")
    
    def on_tab_changed(self, index: int):
        """Обработка смены вкладки"""
        # Обновляем галерею при переходе на вкладку галереи
        if index == 3:  # Индекс вкладки галереи
            self.gallery_tab.load_gallery()

