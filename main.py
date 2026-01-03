"""
Точка входа в приложение NanoBanana Pro
"""
import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.styles import DARK_STYLE


def main():
    """Главная функция запуска приложения"""
    app = QApplication(sys.argv)
    
    # Применяем темную тему
    app.setStyleSheet(DARK_STYLE)
    
    # Создаем и показываем главное окно на полный экран
    window = MainWindow()
    window.showMaximized()  # Открываем окно на полный экран
    
    # Запускаем цикл событий
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()





