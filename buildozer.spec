[app]
title = Металлоёмкость зданий
package.name = metalcalc
package.domain = ru.metalcalc

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Главный файл
source.main = main_android.py

# Версия
version = 1.0.0

# Зависимости Python (таблицы вшиты в код — pandas/docx не нужны)
requirements = python3,kivy==2.3.1,kivymd==1.2.0,pillow

# Ориентация: портрет + альбомная
orientation = portrait

# Android
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.ndk_path =
android.sdk_path =
android.accept_sdk_license = True

# Архитектуры (arm64 для современных устройств)
android.archs = arm64-v8a, armeabi-v7a

# Логотип и иконка (можно заменить своими)
# android.icon.filename = %(source.dir)s/icon.png

# Полноэкранное приложение
fullscreen = 0

# Окна логирования
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
