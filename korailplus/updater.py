"""핫패치 자동 업데이트 (B 방식, 서버 불필요)

코레일 API가 바뀌면 깨지는 부분은 거의 항상 ktx.py다.
이 모듈은 GitHub(공개 저장소)의 raw ktx.py를 받아 앱 저장소에 캐시하고,
그 캐시본을 import 한다. 시작은 즉시(캐시/번들) 로드하고, 최신본 확인은
백그라운드로 수행해 "다음 실행"에 반영한다(시작 지연·오프라인 안전).

보안: 공개 저장소라 배포되는 코드가 누구에게나 투명하게 공개되고, 저장소에
쓰기 권한이 있는 소유자만 코드를 바꿀 수 있다 → 몰래 백도어를 넣을 수 없다.
HTTPS(raw.githubusercontent.com)로 무결성 확보. 필요 시 커밋 해시 핀 고정 가능.
"""
import importlib.util
import os
import re
import threading

# 공개 저장소의 raw ktx.py (main 브랜치)
RAW_URL = "https://raw.githubusercontent.com/wkdusdmlqlc/korail_plus/main/korailplus/ktx.py"

_HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLED = os.path.join(_HERE, "ktx.py")


def _cfg_dir():
    base = os.path.join(os.path.expanduser("~"), ".config", "korailplus", "hotpatch")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        base = os.path.expanduser("~")
    return base


CACHE = os.path.join(_cfg_dir(), "ktx.py")


def _version_of_src(src):
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', src or "")
    return m.group(1) if m else "0"


def _version_of_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return _version_of_src(f.read())
    except OSError:
        return "0"


def _active_path():
    """캐시본이 번들보다 최신이고 유효하면 캐시본, 아니면 번들을 사용."""
    if os.path.exists(CACHE) and _version_of_file(CACHE) >= _version_of_file(BUNDLED):
        return CACHE
    return BUNDLED


def ensure_latest(timeout=8):
    """원격 ktx.py가 현재보다 최신이고 컴파일되면 캐시에 저장(다음 실행 반영)."""
    try:
        import requests

        r = requests.get(RAW_URL, timeout=timeout)
        if r.status_code != 200 or not r.text:
            return
        src = r.text
        remote_ver = _version_of_src(src)
        current = max(_version_of_file(BUNDLED), _version_of_file(CACHE))
        if remote_ver <= current:
            return
        # 안전장치: 문법 검증 후에만 캐시
        compile(src, "ktx_hotpatch", "exec")
        tmp = CACHE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(src)
        os.replace(tmp, CACHE)
    except Exception:
        # 오프라인·오류 시 조용히 무시하고 기존 버전 유지
        pass


def check_async():
    """백그라운드로 최신본 확인(시작 지연 없음)."""
    threading.Thread(target=ensure_latest, daemon=True).start()


def load_ktx():
    """현재 활성 ktx 모듈을 로드해 반환. 시작 시 즉시 로드 + 백그라운드 업데이트."""
    path = _active_path()
    spec = importlib.util.spec_from_file_location("korailplus_ktx_live", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    check_async()
    return mod
