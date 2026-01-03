# Инструкция по сборке исполняемого файла

Это руководство поможет вам создать исполняемый файл приложения NanoBanana Pro для Windows и macOS, чтобы пользователи могли использовать приложение без установки Python.

## Требования для сборки

- Python 3.8 или выше
- Все зависимости из `requirements.txt`
- PyInstaller (устанавливается автоматически)

## Установка зависимостей

```bash
pip install -r requirements.txt
```

Это установит:
- PyQt5 (GUI библиотека)
- requests (HTTP клиент)
- Pillow (работа с изображениями)
- pyinstaller (создание исполняемых файлов)

## Сборка приложения

### Автоматическая сборка (рекомендуется)

Используйте скрипт `build.py`:

```bash
python build.py
```

Скрипт автоматически:
- Определит вашу платформу (Windows/macOS)
- Настроит параметры сборки
- Создаст исполняемый файл в папке `dist/`

### Ручная сборка через PyInstaller

#### Windows

```bash
pyinstaller --onefile --windowed --name "NanoBananaPro" --add-data "data;data" --hidden-import PyQt5.QtCore --hidden-import PyQt5.QtGui --hidden-import PyQt5.QtWidgets --hidden-import sqlite3 --hidden-import PIL --hidden-import requests main.py
```

#### macOS

**Рекомендуемый способ (автоматический):**

```bash
# Используйте скрипт сборки
chmod +x build_macos.sh
./build_macos.sh
```

Или используйте Python скрипт:

```bash
python3 build.py
```

**Альтернативный способ (через spec файл):**

```bash
pyinstaller build_macos.spec
```

**Ручная сборка через PyInstaller:**

```bash
pyinstaller --onedir --windowed --name "NanoBananaPro" --add-data "data:data" --hidden-import PyQt5.QtCore --hidden-import PyQt5.QtGui --hidden-import PyQt5.QtWidgets --hidden-import sqlite3 --hidden-import PIL --hidden-import requests main.py
```

**Важно для macOS:**
- Используйте `--onedir` вместо `--onefile` для создания `.app` bundle
- PyInstaller автоматически создаст `.app` bundle при использовании `--windowed` на macOS

### Использование spec-файла

Если нужна более детальная настройка, используйте `build.spec`:

```bash
pyinstaller build.spec
```

## Результат сборки

После успешной сборки:

- **Windows**: `dist/NanoBananaPro.exe`
- **macOS**: `dist/NanoBananaPro.app`

## Тестирование

**ВАЖНО**: Перед распространением обязательно протестируйте приложение:

1. Запустите исполняемый файл на чистой системе (без установленного Python)
2. Проверьте все функции:
   - Генерация изображений
   - Редактирование изображений
   - Комбинирование изображений
   - Просмотр галереи
   - Сохранение настроек
   - Работа с базой данных

3. Убедитесь, что:
   - Приложение запускается без ошибок
   - Изображения сохраняются в правильную папку
   - База данных создается и работает
   - API запросы выполняются корректно

## Распространение

### Windows

1. Скопируйте `NanoBananaPro.exe` в отдельную папку
2. Опционально: создайте установщик с помощью:
   - [Inno Setup](https://jrsoftware.org/isinfo.php)
   - [NSIS](https://nsis.sourceforge.io/)
3. Упакуйте в ZIP архив для распространения

### macOS

1. Скопируйте `NanoBananaPro.app` в папку Applications:
   ```bash
   cp -R dist/NanoBananaPro.app /Applications/
   ```

2. Опционально: создайте DMG образ для распространения:

   **Способ 1 (create-dmg - рекомендуется):**
   ```bash
   # Установите create-dmg
   brew install create-dmg
   
   # Создайте DMG
   create-dmg --volname "NanoBanana Pro" --window-pos 200 120 --window-size 800 400 \
     --icon-size 100 --app-drop-link 600 185 dist/NanoBananaPro.dmg dist/
   ```

   **Способ 2 (hdiutil - встроенный в macOS):**
   ```bash
   hdiutil create -volname "NanoBanana Pro" -srcfolder dist/NanoBananaPro.app \
     -ov -format UDZO dist/NanoBananaPro.dmg
   ```

3. Для распространения через App Store потребуется кодовая подпись:
   ```bash
   # Подпись приложения (требует Apple Developer аккаунт)
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/NanoBananaPro.app
   
   # Проверка подписи
   codesign --verify --verbose dist/NanoBananaPro.app
   ```

4. Тестирование приложения:
   ```bash
   # Открыть приложение для тестирования
   open dist/NanoBananaPro.app
   ```

## Размер файла

Ожидаемый размер исполняемого файла:
- Windows: ~50-80 MB
- macOS: ~60-90 MB

Размер зависит от включенных библиотек и может варьироваться.

## Устранение проблем

### Ошибка "ModuleNotFoundError"

Если при запуске exe возникает ошибка о недостающем модуле:

1. Добавьте модуль в `hiddenimports` в `build.spec` или `build.py`
2. Пересоберите приложение

### Ошибка "Failed to execute script"

1. Запустите с консолью для просмотра ошибок:
   ```bash
   pyinstaller --onefile --console main.py
   ```

2. Проверьте логи ошибок
3. Убедитесь, что все зависимости установлены

### Приложение не запускается

1. Проверьте, что все файлы из папки `data` включены в сборку
2. Убедитесь, что пути к ресурсам корректны (используется `utils/path_utils.py`)
3. Проверьте права доступа к файлам

### Большой размер файла

Для уменьшения размера:

1. Используйте `--exclude-module` для неиспользуемых модулей
2. Используйте UPX для сжатия (включено по умолчанию)
3. Проверьте, что не включены лишние файлы

## Дополнительные настройки

### Иконка приложения

1. Создайте иконку:
   - Windows: `.ico` файл (256x256)
   - macOS: `.icns` файл

2. Поместите в `resources/icons/`
3. Укажите путь в `build.py` или `build.spec`

### Версия приложения

Для добавления информации о версии (Windows):

1. Создайте файл `version_info.txt`
2. Добавьте в `build.spec`:
   ```python
   version='version_info.txt',
   ```

## Структура после сборки

```
dist/
└── NanoBananaPro.exe (или .app)

build/  # Временные файлы сборки (можно удалить)
```

## Важные замечания

1. **База данных**: SQLite работает внутри exe, но данные сохраняются в папке рядом с exe
2. **Изображения**: Сохраняются в `data/images/` рядом с исполняемым файлом
3. **Конфигурация**: Сохраняется в `~/.nanobanana_pro/config.json` (домашняя папка пользователя)
4. **curl**: На Windows может отсутствовать, но есть резервный метод через requests

## Поддержка

При возникновении проблем:
1. Проверьте логи ошибок
2. Убедитесь, что все зависимости установлены
3. Попробуйте пересобрать с параметром `--clean`




