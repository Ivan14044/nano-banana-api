# Быстрая сборка

## Самый простой способ

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Запустите скрипт сборки
python build.py
```

Готово! Исполняемый файл будет в папке `dist/`

## Для Windows
- Результат: `dist/NanoBananaPro.exe`
- Размер: ~50-80 MB

## Для macOS

**Способ 1: Использование скрипта (рекомендуется)**
```bash
chmod +x build_macos.sh
./build_macos.sh
```

**Способ 2: Использование Python скрипта**
```bash
python3 build.py
```

**Способ 3: Использование spec файла**
```bash
pyinstaller build_macos.spec
```

- Результат: `dist/NanoBananaPro.app`
- Размер: ~60-90 MB

**Создание DMG образа (опционально):**
```bash
# Способ 1: create-dmg
brew install create-dmg
create-dmg --volname 'NanoBanana Pro' dist/NanoBananaPro.dmg dist/

# Способ 2: hdiutil (встроенный)
hdiutil create -volname 'NanoBanana Pro' -srcfolder dist/NanoBananaPro.app -ov -format UDZO dist/NanoBananaPro.dmg
```

## Что дальше?

1. Протестируйте файл на чистой системе
2. Проверьте все функции приложения
3. Распространяйте!

Подробная документация: [BUILD.md](BUILD.md)




