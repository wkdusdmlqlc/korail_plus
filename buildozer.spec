[app]
title = korail+
package.name = korailplus
package.domain = org.korailplus

# main.py(GUI) + service.py(백그라운드 재시도) + korailplus 패키지 포함
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = korailplus/*.py
# 빌드/개발 산출물 제외
source.exclude_dirs = tests, bin, .buildozer, .venv, .git, .github, tools, __pycache__
source.exclude_patterns = login_test.py, buildozer.spec

version = 0.1.0

# curl_cffi는 안드로이드 빌드 레시피가 없어 제외 -> ktx.py의 requests 폴백 사용.
# keyring/inquirer/click/prompt_toolkit/telegram(CLI 전용)은 앱에 불필요.
requirements = python3,kivy==2.3.0,pycryptodome,requests,urllib3,idna,charset-normalizer,certifi,plyer,pyjnius,android

orientation = portrait
fullscreen = 0

# 백그라운드 자동 재시도 서비스 (Foreground Service)
services = Korailretry:service.py:foreground

# 권한: 인터넷 + 포그라운드 서비스 + 알림 + 웨이크락
android.permissions = INTERNET, ACCESS_NETWORK_STATE, FOREGROUND_SERVICE, FOREGROUND_SERVICE_DATA_SYNC, POST_NOTIFICATIONS, WAKE_LOCK, RECEIVE_BOOT_COMPLETED

android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a
android.wakelock = True

# 화면 꺼짐/백그라운드에서도 네트워크 유지
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
