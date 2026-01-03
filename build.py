"""
Скрипт для автоматической сборки исполняемого файла
Поддерживает Windows и macOS
"""
import PyInstaller.__main__
import os
import sys
from pathlib import Path


def get_platform_specific_args():
    """Получить аргументы специфичные для платформы"""
    is_windows = sys.platform == 'win32'
    is_macos = sys.platform == 'darwin'
    
    args = []
    
    # Разделитель для --add-data зависит от платформы
    data_separator = ';' if is_windows else ':'
    
    # Добавляем папку data если существует (необязательно, создастся при первом запуске)
    if os.path.exists('data'):
        args.append(f'--add-data=data{data_separator}data')
    
    # Добавляем ресурсы если есть
    if os.path.exists('resources'):
        args.append(f'--add-data=resources{data_separator}resources')
    
    # Иконка приложения
    if is_windows:
        icon_path = 'resources/icons/app.ico'
        if os.path.exists(icon_path):
            args.append(f'--icon={icon_path}')
    elif is_macos:
        icon_path = 'resources/icons/app.icns'
        if os.path.exists(icon_path):
            args.append(f'--icon={icon_path}')
    
    return args


def build():
    """Собрать исполняемый файл"""
    print("=" * 60)
    print("Сборка NanoBanana Pro")
    print("=" * 60)
    
    # Определяем платформу
    is_windows = sys.platform == 'win32'
    is_macos = sys.platform == 'darwin'
    
    if not (is_windows or is_macos):
        print(f"Внимание: Платформа {sys.platform} может не поддерживаться полностью")
    
    # Базовые аргументы PyInstaller
    # Для macOS используем --onedir для создания .app bundle
    # Для Windows используем --onefile для создания одного exe файла
    if is_macos:
        args = [
            'main.py',
            '--onedir',  # Создаем .app bundle для macOS
            '--windowed',  # Без консоли (GUI приложение)
            '--name=NanoBananaPro',  # Имя приложения
            '--clean',  # Очистить кэш перед сборкой
            '--noconfirm',  # Не спрашивать подтверждения
        ]
    else:
        args = [
            'main.py',
            '--onefile',  # Один исполняемый файл для Windows
            '--windowed',  # Без консоли (GUI приложение)
            '--name=NanoBananaPro',  # Имя исполняемого файла
            '--clean',  # Очистить кэш перед сборкой
            '--noconfirm',  # Не спрашивать подтверждения
        ]
    
    # Скрытые импорты (модули, которые PyInstaller может не найти автоматически)
    hidden_imports = [
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'sqlite3',
        'PIL',
        'PIL.Image',
        'requests',
        'json',
        'base64',
        'io',
        'pathlib',
    ]
    
    for imp in hidden_imports:
        args.append(f'--hidden-import={imp}')
    
    # Платформо-специфичные аргументы
    platform_args = get_platform_specific_args()
    args.extend(platform_args)
    
    # Дополнительные опции для уменьшения размера
    args.extend([
        '--exclude-module=tkinter',  # Не нужен для PyQt5
        '--exclude-module=matplotlib',  # Не используется
        '--exclude-module=numpy',  # Не используется (если не нужен)
    ])
    
    print("\nПараметры сборки:")
    print(f"  Платформа: {sys.platform}")
    if is_macos:
        print(f"  Режим: onedir (.app bundle)")
    else:
        print(f"  Режим: onefile (один exe файл)")
    print(f"  Имя: NanoBananaPro")
    print(f"  Скрытые импорты: {len(hidden_imports)}")
    print("\nНачинаю сборку...\n")
    
    try:
        # Запускаем PyInstaller
        PyInstaller.__main__.run(args)
        
        print("\n" + "=" * 60)
        print("Сборка завершена!")
        print("=" * 60)
        
        # Определяем путь к результату
        if is_windows:
            exe_path = Path('dist') / 'NanoBananaPro.exe'
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"\nИсполняемый файл создан: {exe_path}")
                print(f"Размер: {size_mb:.2f} MB")
                print(f"\nФайл готов к распространению!")
        elif is_macos:
            app_path = Path('dist') / 'NanoBananaPro.app'
            if app_path.exists():
                # Получаем размер .app bundle
                import shutil
                size_bytes = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())
                size_mb = size_bytes / (1024 * 1024)
                print(f"\nПриложение создано: {app_path}")
                print(f"Размер: {size_mb:.2f} MB")
                print(f"\nПриложение готово к распространению!")
                print("\nДля создания DMG образа используйте:")
                print("  brew install create-dmg")
                print("  create-dmg --volname 'NanoBanana Pro' dist/NanoBananaPro.dmg dist/")
                print("\nИли используйте hdiutil:")
                print("  hdiutil create -volname 'NanoBanana Pro' -srcfolder dist/NanoBananaPro.app -ov -format UDZO dist/NanoBananaPro.dmg")
        else:
            exe_path = Path('dist') / 'NanoBananaPro'
            if exe_path.exists():
                print(f"\nИсполняемый файл создан: {exe_path}")
        
        print("\nВажно:")
        print("1. Протестируйте приложение на чистой системе без Python")
        print("2. Убедитесь, что все функции работают корректно")
        print("3. Проверьте работу с базой данных и сохранение изображений")
        
    except Exception as e:
        print(f"\nОшибка при сборке: {e}")
        print("\nУбедитесь, что:")
        print("1. PyInstaller установлен: pip install pyinstaller")
        print("2. Все зависимости установлены: pip install -r requirements.txt")
        print("3. Приложение запускается в режиме разработки: python main.py")
        sys.exit(1)


if __name__ == '__main__':
    build()

