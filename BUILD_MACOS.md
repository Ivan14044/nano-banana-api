# Инструкция по сборке для macOS

Это руководство поможет вам собрать приложение NanoBanana Pro для macOS.

## Требования

- macOS 10.13 или выше
- Python 3.8 или выше
- Все зависимости из `requirements.txt`
- PyInstaller (устанавливается автоматически)

## Быстрая сборка

Самый простой способ - использовать готовый скрипт:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

Скрипт автоматически:
- Проверит наличие Python и pip
- Установит все зависимости
- Соберет приложение в `.app` bundle

## Пошаговая сборка

### 1. Установка зависимостей

```bash
pip3 install -r requirements.txt
```

### 2. Сборка приложения

**Вариант A: Использование Python скрипта (рекомендуется)**

```bash
python3 build.py
```

**Вариант B: Использование spec файла**

```bash
pyinstaller build_macos.spec
```

**Вариант C: Прямой вызов PyInstaller**

```bash
pyinstaller --onedir --windowed --name "NanoBananaPro" \
  --add-data "data:data" \
  --hidden-import PyQt5.QtCore \
  --hidden-import PyQt5.QtGui \
  --hidden-import PyQt5.QtWidgets \
  --hidden-import sqlite3 \
  --hidden-import PIL \
  --hidden-import requests \
  main.py
```

## Результат сборки

После успешной сборки приложение будет находиться в:

```
dist/NanoBananaPro.app
```

## Тестирование

Перед распространением обязательно протестируйте приложение:

```bash
# Открыть приложение
open dist/NanoBananaPro.app
```

Проверьте:
- ✅ Приложение запускается без ошибок
- ✅ Все функции работают (генерация, редактирование, комбинирование)
- ✅ Изображения сохраняются корректно
- ✅ База данных работает
- ✅ API запросы выполняются

## Создание DMG образа

Для распространения приложения удобно создать DMG образ.

### Способ 1: create-dmg (рекомендуется)

```bash
# Установка
brew install create-dmg

# Создание DMG
create-dmg --volname "NanoBanana Pro" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  dist/NanoBananaPro.dmg \
  dist/
```

### Способ 2: hdiutil (встроенный в macOS)

```bash
hdiutil create -volname "NanoBanana Pro" \
  -srcfolder dist/NanoBananaPro.app \
  -ov -format UDZO \
  dist/NanoBananaPro.dmg
```

## Кодовая подпись (опционально)

Для распространения через App Store или для избежания предупреждений Gatekeeper требуется кодовая подпись.

### Требования:
- Apple Developer аккаунт
- Сертификат разработчика

### Подпись приложения:

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  dist/NanoBananaPro.app
```

### Проверка подписи:

```bash
codesign --verify --verbose dist/NanoBananaPro.app
```

### Нотаризация (для распространения вне App Store):

```bash
# Создайте zip архив
ditto -c -k --keepParent dist/NanoBananaPro.app dist/NanoBananaPro.zip

# Отправьте на нотаризацию
xcrun altool --notarize-app \
  --primary-bundle-id "com.nanobanana.pro" \
  --username "your@email.com" \
  --password "@keychain:AC_PASSWORD" \
  --file dist/NanoBananaPro.zip

# Проверка статуса
xcrun altool --notarization-info <UUID> \
  --username "your@email.com" \
  --password "@keychain:AC_PASSWORD"

# После успешной нотаризации, добавьте скрепку
xcrun stapler staple dist/NanoBananaPro.app
```

## Устранение проблем

### Ошибка "ModuleNotFoundError"

Если при запуске возникает ошибка о недостающем модуле:

1. Добавьте модуль в `hiddenimports` в `build_macos.spec`
2. Пересоберите приложение

### Ошибка "Failed to execute script"

1. Запустите с консолью для просмотра ошибок:
   ```bash
   pyinstaller --onedir --console main.py
   ```
2. Проверьте логи ошибок
3. Убедитесь, что все зависимости установлены

### Приложение не запускается

1. Проверьте, что все файлы из папки `data` включены в сборку
2. Убедитесь, что пути к ресурсам корректны
3. Проверьте права доступа к файлам:
   ```bash
   chmod +x dist/NanoBananaPro.app/Contents/MacOS/NanoBananaPro
   ```

### Предупреждение Gatekeeper

Если macOS блокирует запуск приложения:

1. Откройте Системные настройки → Защита и безопасность
2. Нажмите "Открыть в любом случае" рядом с предупреждением
3. Или используйте кодовую подпись (см. выше)

### Большой размер приложения

Для уменьшения размера:

1. Используйте `--exclude-module` для неиспользуемых модулей
2. Используйте UPX для сжатия (включено по умолчанию)
3. Проверьте, что не включены лишние файлы

## Размер приложения

Ожидаемый размер `.app` bundle: **60-90 MB**

Размер зависит от включенных библиотек и может варьироваться.

## Структура .app bundle

```
NanoBananaPro.app/
├── Contents/
│   ├── Info.plist          # Информация о приложении
│   ├── MacOS/
│   │   └── NanoBananaPro   # Исполняемый файл
│   └── Resources/         # Ресурсы приложения
│       ├── data/          # Данные приложения
│       └── resources/     # Иконки и другие ресурсы
```

## Дополнительные настройки

### Иконка приложения

1. Создайте `.icns` файл (можно использовать онлайн-конвертеры)
2. Поместите в `resources/icons/app.icns`
3. Укажите путь в `build_macos.spec`

### Версия приложения

Версия указывается в `build_macos.spec` в секции `info_plist`:
- `CFBundleShortVersionString` - версия для пользователя
- `CFBundleVersion` - номер сборки

## Важные замечания

1. **База данных**: SQLite работает внутри .app, но данные сохраняются в `~/Library/Application Support/NanoBananaPro/`
2. **Изображения**: Сохраняются в `~/Library/Application Support/NanoBananaPro/images/`
3. **Конфигурация**: Сохраняется в `~/.nanobanana_pro/config.json`
4. **Права доступа**: При первом запуске macOS может запросить разрешения

## Поддержка

При возникновении проблем:
1. Проверьте логи ошибок в консоли
2. Убедитесь, что все зависимости установлены
3. Попробуйте пересобрать с параметром `--clean`
4. Проверьте версию Python (должна быть 3.8+)


