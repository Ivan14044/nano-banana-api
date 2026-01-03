#!/bin/bash
# Скрипт для автоматической сборки macOS версии
# Запустите этот скрипт на macOS системе

echo "============================================================"
echo "Сборка NanoBanana Pro для macOS"
echo "============================================================"

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python3 не найден. Установите Python 3.8 или выше."
    exit 1
fi

echo "Python версия:"
python3 --version

# Проверка pip
if ! command -v pip3 &> /dev/null; then
    echo "Ошибка: pip3 не найден."
    exit 1
fi

# Установка зависимостей
echo ""
echo "Установка зависимостей..."
pip3 install -r requirements.txt

# Проверка PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "Установка PyInstaller..."
    pip3 install pyinstaller
fi

# Запуск сборки
echo ""
echo "Начинаю сборку..."
python3 build.py

echo ""
echo "============================================================"
echo "Сборка завершена!"
echo "============================================================"
echo ""

# Проверка результата
if [ -d "dist/NanoBananaPro.app" ]; then
    echo "✓ Приложение успешно создано: dist/NanoBananaPro.app"
    echo ""
    echo "Для создания DMG образа используйте один из способов:"
    echo ""
    echo "Способ 1 (create-dmg):"
    echo "  brew install create-dmg"
    echo "  create-dmg --volname 'NanoBanana Pro' --window-pos 200 120 --window-size 800 400 \\"
    echo "    --icon-size 100 --app-drop-link 600 185 dist/NanoBananaPro.dmg dist/"
    echo ""
    echo "Способ 2 (hdiutil - встроенный в macOS):"
    echo "  hdiutil create -volname 'NanoBanana Pro' -srcfolder dist/NanoBananaPro.app \\"
    echo "    -ov -format UDZO dist/NanoBananaPro.dmg"
    echo ""
    echo "Для тестирования приложения:"
    echo "  open dist/NanoBananaPro.app"
    echo ""
else
    echo "✗ Ошибка: Приложение не было создано"
    echo "Проверьте сообщения об ошибках выше"
    exit 1
fi




