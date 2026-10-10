"""korail+ Android GUI (Kivy) — 현대적 다크 UI

korailplus/ktx.py 코어를 재사용. 자동 재시도는 service.py(Foreground Service)가 담당.
한글 렌더링을 위해 NanumGothic을 기본 폰트로 등록한다.
"""
import json
import os
import sys
import threading
import time
import traceback

# 시작 크래시를 파일로 남겨 진단 가능하게 (앱 저장소)
def _log_crash(exc_type, exc, tb):
    try:
        p = os.path.join(os.path.expanduser("~"), ".config", "korailplus")
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, "crash.log"), "w") as f:
            f.write("".join(traceback.format_exception(exc_type, exc, tb)))
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc, tb)

sys.excepthook = _log_crash

# --- 한글 폰트를 Kivy 기본 폰트("Roboto") 이름으로 등록 → 모든 위젯에 적용 ---
from kivy.core.text import LabelBase

try:
    _FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
    _REG = os.path.join(_FONT_DIR, "NanumGothic-Regular.ttf")
    _BOLD = os.path.join(_FONT_DIR, "NanumGothic-Bold.ttf")
    if os.path.exists(_REG):
        LabelBase.register(name="Roboto", fn_regular=_REG,
                           fn_bold=_BOLD if os.path.exists(_BOLD) else _REG)
except Exception:
    pass  # 폰트 등록 실패해도 앱은 계속(한글은 기본 폰트로)

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.scrollview import ScrollView

# 핫패치: 번들/캐시 ktx를 즉시 로드하고 백그라운드로 최신본을 받아둔다(다음 실행 반영)
from korailplus import updater as _updater

_K = _updater.load_ktx()
AdultPassenger = _K.AdultPassenger
ChildPassenger = _K.ChildPassenger
SeniorPassenger = _K.SeniorPassenger
Disability1To3Passenger = _K.Disability1To3Passenger
Disability4To6Passenger = _K.Disability4To6Passenger
Korail = _K.Korail
KorailError = _K.KorailError
ReserveOption = _K.ReserveOption
SoldOutError = _K.SoldOutError

Window.clearcolor = (0.055, 0.063, 0.078, 1)  # #0E1014

KTX_STATIONS = ["서울", "용산", "영등포", "광명", "수원", "천안아산", "오송", "대전",
                "서대전", "김천구미", "동대구", "경주", "포항", "밀양", "구포", "부산",
                "울산(통도사)", "마산", "창원중앙", "경산", "논산", "익산", "정읍",
                "광주송정", "목포", "전주", "순천", "여수EXPO", "청량리", "강릉",
                "행신", "정동진"]

SEAT_OPTIONS = {
    "일반실 우선": ReserveOption.GENERAL_FIRST,
    "일반실만": ReserveOption.GENERAL_ONLY,
    "특실 우선": ReserveOption.SPECIAL_FIRST,
    "특실만": ReserveOption.SPECIAL_ONLY,
}

KV = """
#:import dp kivy.metrics.dp

<MDButton@ButtonBehavior+Label>:
    bg: 0, 0.655, 0.345, 1
    radius: dp(14)
    color: 1, 1, 1, 1
    bold: True
    font_size: '16sp'
    size_hint_y: None
    height: dp(52)
    canvas.before:
        Color:
            rgba: (self.bg[0]*0.8, self.bg[1]*0.8, self.bg[2]*0.8, self.bg[3]) if self.state=='down' else self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16), dp(16), dp(16), dp(16)]

<GhostButton@ButtonBehavior+Label>:
    radius: dp(14)
    color: 0.82, 0.85, 0.88, 1
    bold: True
    font_size: '15sp'
    size_hint_y: None
    height: dp(46)
    canvas.before:
        Color:
            rgba: (0.2, 0.22, 0.26, 1) if self.state=='down' else (0.13, 0.14, 0.17, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16), dp(16), dp(16), dp(16)]
        Color:
            rgba: 0.25, 0.27, 0.31, 1
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(16))
            width: 1

<Card@BoxLayout>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(6)
    radius: dp(18)
    bg: 0.098, 0.106, 0.125, 1
    canvas.before:
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16), dp(16), dp(16), dp(16)]

<Field@TextInput>:
    multiline: False
    size_hint_y: None
    height: dp(52)
    font_size: '16sp'
    padding: [dp(14), dp(15)]
    background_normal: ''
    background_active: ''
    background_color: 0, 0, 0, 0
    foreground_color: 0.93, 0.94, 0.95, 1
    cursor_color: 0.235, 0.863, 0.518, 1
    hint_text_color: 0.5, 0.53, 0.57, 1
    canvas.before:
        Color:
            rgba: 0.098, 0.106, 0.125, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(13)]
        Color:
            rgba: (0.235, 0.863, 0.518, 1) if self.focus else (0.22, 0.24, 0.28, 1)
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(13))
            width: 1.3

<Pick@Spinner>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: 0.93, 0.94, 0.95, 1
    font_size: '15sp'
    size_hint_y: None
    height: dp(48)
    canvas.before:
        Color:
            rgba: 0.098, 0.106, 0.125, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(13)]
        Color:
            rgba: 0.22, 0.24, 0.28, 1
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(13))
            width: 1.2
"""
Builder.load_string(KV)

from kivy.factory import Factory  # noqa: E402

TXT = (0.93, 0.94, 0.95, 1)
MUTED = (0.55, 0.58, 0.63, 1)
ACCENT = (0.235, 0.863, 0.518, 1)
PRIMARY = (0.0, 0.655, 0.345, 1)
BRAND = (0.235, 0.863, 0.518, 1)  # 재시도 완료 강조(=ACCENT 톤)
SAFE_TOP = 44  # 상단 상태바/노치 회피 여백(dp — 기기 상태바 ~37dp보다 크게)


def _hex(color):
    """(r,g,b,a) 0~1 → 'RRGGBB' (Kivy 마크업 [color=...]용)."""
    r, g, b = (int(max(0, min(1, c)) * 255) for c in color[:3])
    return f"{r:02X}{g:02X}{b:02X}"


# ---------- 저장소/설정/서비스 제어 ----------
def _cfg_dir():
    # 안드로이드: HOME 루트(/data/user/0/<pkg>)는 쓰기 불가. ANDROID_PRIVATE(files 디렉터리) 사용.
    root = os.environ.get("ANDROID_PRIVATE") or os.path.join(os.path.expanduser("~"), ".config")
    d = os.path.join(root, "korailplus")
    try:
        os.makedirs(d, exist_ok=True)
        return d
    except OSError:
        d = os.path.join(os.getcwd(), "korailplus_data")  # 최후 폴백(앱 files/app)
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass
        return d


CRED_PATH = os.path.join(_cfg_dir(), "credentials.json")
SETTINGS_PATH = os.path.join(_cfg_dir(), "settings.json")
JOBS_PATH = os.path.join(_cfg_dir(), "jobs.json")          # 작업 목록(GUI가 추가/취소)
JOBSTATUS_PATH = os.path.join(_cfg_dir(), "job_status.json")  # 작업별 상태(서비스가 기록)
STOP_PATH = os.path.join(_cfg_dir(), "stop.flag")


def _load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save(path, data):
    """원자적 저장(tmp+replace) — 백그라운드 서비스와의 동시 접근 경합 방지."""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except OSError:
        pass


# ---------- Android Keystore 기반 암호화 저장 (로그인/카드) ----------
# 키 생성/암복호화는 Java 헬퍼(org.korailplus.SecureStore)가 전담한다.


def _secure_store():
    """Java 헬퍼 org.korailplus.SecureStore 로드(안드로이드 전용). 실패 시 None."""
    try:
        from jnius import autoclass
        return autoclass("org.korailplus.SecureStore")
    except Exception:
        return None


def _ks_encrypt(text):
    """평문 -> base64 암호문. Keystore 불가(비안드로이드/오류) 시 None.

    모든 Keystore/Cipher 로직은 Java(SecureStore)에서 수행한다. pyjnius로
    배열 인자를 마셜링하던 기존 방식이 네이티브 abort를 일으켜 앱을 종료시켰기
    때문에, 파이썬은 encrypt/decrypt 호출만 담당한다.
    """
    store = _secure_store()
    if store is None:
        return None
    try:
        return store.encrypt(text)  # 실패 시 Java가 null -> 파이썬 None
    except Exception:
        return None


def _ks_decrypt(b64):
    store = _secure_store()
    if store is None:
        return None
    try:
        return store.decrypt(b64)
    except Exception:
        return None


def secure_save(path, d):
    raw = json.dumps(d)
    enc = _ks_encrypt(raw)
    try:
        with open(path, "w") as f:
            f.write("KS1:" + enc if enc else "PLAIN:" + raw)
    except OSError:
        pass


def secure_load(path, default):
    try:
        with open(path) as f:
            s = f.read()
    except OSError:
        return default
    try:
        if s.startswith("KS1:"):
            dec = _ks_decrypt(s[4:])
            return json.loads(dec) if dec else default
        if s.startswith("PLAIN:"):
            return json.loads(s[6:])
        return json.loads(s)  # 레거시 평문 자동 마이그레이션
    except (ValueError, TypeError):
        return default


def load_creds():
    return secure_load(CRED_PATH, {})


def save_creds(d):
    secure_save(CRED_PATH, d)


def load_settings():
    # 기본 알림: 안드로이드. enabled=알림 on/off.
    d = _load(SETTINGS_PATH, {})
    return {
        "enabled": d.get("enabled", True),
        "notify": d.get("notify", "android"),
        "tg_token": d.get("tg_token", ""),
        "tg_chat": d.get("tg_chat", ""),
        "interval": d.get("interval", "3"),
    }


def save_settings(d):
    _save(SETTINGS_PATH, d)


STATIONS_PATH = os.path.join(_cfg_dir(), "stations.json")          # 사용자 커스텀 목록
STATION_MASTER_PATH = os.path.join(_cfg_dir(), "stations_master.json")  # 코레일 역 마스터 캐시


def load_stations():
    """역 목록 우선순위: 사용자 커스텀 → 코레일 마스터 캐시 → 하드코딩 폴백."""
    lst = _load(STATIONS_PATH, None)
    if isinstance(lst, list) and lst:
        return lst
    master = _load(STATION_MASTER_PATH, None)
    if isinstance(master, list) and master:
        return master
    return list(KTX_STATIONS)


def save_stations(lst):
    _save(STATIONS_PATH, lst)


def fetch_station_master(force=False):
    """코레일에서 전체 역 목록을 받아 캐시에 저장하고 반환. 실패 시 None.

    네트워크 호출이므로 백그라운드 스레드에서 부른다. 이미 캐시가 있으면
    force=False일 때 건너뛴다(앱 시작 지연·트래픽 방지)."""
    if not force:
        cached = _load(STATION_MASTER_PATH, None)
        if isinstance(cached, list) and cached:
            return cached
    try:
        names = _K.fetch_stations()
    except Exception:
        names = []
    if names:
        _save(STATION_MASTER_PATH, names)
        return names
    return None


def test_telegram(token, chat):
    """텔레그램 설정 검증용 테스트 전송. (성공여부, 메시지) 반환."""
    if not token or not chat:
        return False, "토큰과 chat_id를 모두 입력하세요"
    try:
        import requests
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat, "text": "✅ korail+ 텔레그램 알림 테스트"}, timeout=10)
        try:
            j = r.json()
        except ValueError:
            j = {}
        if r.status_code == 200 and j.get("ok"):
            return True, "테스트 메시지를 보냈습니다. 텔레그램을 확인하세요."
        return False, j.get("description") or f"실패 (HTTP {r.status_code})"
    except Exception as e:  # noqa
        return False, str(e)


def request_notification_permission():
    """Android 13+ 런타임 알림 권한(POST_NOTIFICATIONS) 요청.

    미승인 시 nm.notify()가 조용히 무시돼 재시도/예매 성공 알림이 안 뜬다.
    비안드로이드/오류 시 조용히 무시."""
    try:
        from android.permissions import Permission, request_permissions
        request_permissions([Permission.POST_NOTIFICATIONS])
    except Exception:
        pass


def ensure_station_master_async():
    """역 마스터 캐시가 없으면 백그라운드로 받아 둔다."""
    threading.Thread(target=fetch_station_master, daemon=True).start()


CARD_PATH = os.path.join(_cfg_dir(), "card.json")


def load_card():
    return secure_load(CARD_PATH, {"number": "", "password": "", "birthday": "", "expire": ""})


def save_card(d):
    secure_save(CARD_PATH, d)


def pay_reservation(rail, rsv):
    """저장된 카드로 예약 결제. 카드 정보 없으면 False."""
    c = load_card()
    if not c.get("number"):
        return False
    bday = c.get("birthday", "")
    return rail.pay_with_card(
        rsv, c["number"], c["password"], bday, c["expire"], 0,
        "J" if len(bday) == 6 else "S",
    )


def load_jobs():
    lst = _load(JOBS_PATH, [])
    return lst if isinstance(lst, list) else []


def save_jobs(jobs):
    _save(JOBS_PATH, jobs)


def read_job_status():
    d = _load(JOBSTATUS_PATH, {})
    return d if isinstance(d, dict) else {}


def add_job(job):
    """작업을 목록에 추가하고 백그라운드 서비스를 시작한다.

    주의: job["id"]/["pass"]는 코레일 로그인 자격증명이므로 건드리지 않는다.
    작업 식별자는 별도 키 job["jid"]를 쓴다."""
    import uuid
    job["jid"] = uuid.uuid4().hex[:8]
    job["created"] = int(time.time())
    jobs = load_jobs()
    jobs.append(job)
    save_jobs(jobs)
    try:  # 새 작업 추가 시 전체중지 플래그 해제
        if os.path.exists(STOP_PATH):
            os.remove(STOP_PATH)
    except OSError:
        pass
    return start_retry_service()


def cancel_job(job_id):
    """작업 하나를 목록에서 제거(서비스가 다음 사이클에 반영). 확보된 예약은 유지됨."""
    jobs = [j for j in load_jobs() if j.get("jid") != job_id]
    save_jobs(jobs)
    if not jobs:
        stop_retry_service()  # 남은 작업 없으면 서비스 종료


def clear_all_jobs():
    """모든 작업 중지 및 제거."""
    save_jobs([])
    stop_retry_service()


def start_retry_service():
    """p4a가 생성한 서비스 클래스의 정적 start()로 시작.

    수동으로 Intent만 만들어 startService()하면 PythonService.onStartCommand가
    기대하는 extras(androidPrivate/serviceEntrypoint/pythonServiceArgument 등)가
    없어 NullPointerException으로 즉시 종료된다. 생성된 start()가 그 extras를
    모두 채워주므로 반드시 이를 호출한다.
    """
    try:
        from jnius import autoclass

        ctx = autoclass("org.kivy.android.PythonActivity").mActivity
        Service = autoclass("org.korailplus.korailplus.ServiceKorailretry")
        Service.start(ctx, "")
        return True
    except Exception:
        return False


def stop_retry_service():
    try:
        with open(STOP_PATH, "w") as f:
            f.write("1")
    except OSError:
        pass
    try:
        from jnius import autoclass

        ctx = autoclass("org.kivy.android.PythonActivity").mActivity
        Service = autoclass("org.korailplus.korailplus.ServiceKorailretry")
        Service.stop(ctx)
    except Exception:
        pass


# ---------- UI 헬퍼 ----------
def label(text, color=TXT, size="15sp", **kw):
    kw.setdefault("markup", True)
    return Label(text=text, color=color, font_size=size, **kw)


def button(text, cb, kind="primary", h=52):
    cls = {"primary": "MDButton", "ghost": "GhostButton"}[kind]
    b = Factory.get(cls)()
    b.text = text
    if kind == "primary":
        b.height = dp(h)
    if cb:
        b.bind(on_release=lambda *_: cb())
    return b


def accent_button(text, cb, h=52):
    b = button(text, cb, "primary", h)
    b.bg = ACCENT
    return b


def field(hint, password=False, text=""):
    f = Factory.Field()
    f.hint_text = hint
    f.password = password
    f.text = text
    return f


def pick(default, values, width=None):
    s = Factory.Pick()
    s.text = default
    s.values = values
    if width:
        s.size_hint_x = None
        s.width = dp(width)
    return s


def header(title, subtitle=None):
    box = BoxLayout(orientation="vertical", size_hint_y=None,
                    height=dp(72 if subtitle else 48), spacing=dp(2))
    box.add_widget(label(f"[b]{title}[/b]", color=ACCENT, size="26sp",
                         halign="left", size_hint_y=None, height=dp(40),
                         text_size=(Window.width - dp(40), None)))
    if subtitle:
        box.add_widget(label(subtitle, color=MUTED, size="13sp", halign="left",
                             size_hint_y=None, height=dp(22),
                             text_size=(Window.width - dp(40), None)))
    return box


_WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def fmt_date(yyyymmdd):
    """'20261006' -> '2026-10-06 (월)'."""
    from datetime import datetime
    try:
        d = datetime.strptime(yyyymmdd, "%Y%m%d")
        return f"{d.year}-{d.month:02d}-{d.day:02d} ({_WEEKDAYS[d.weekday()]})"
    except (ValueError, TypeError):
        return yyyymmdd


def open_calendar(initial, on_pick, days_ahead=30):
    """월간 캘린더 팝업. 오늘~days_ahead일만 선택 가능. 선택 시 on_pick('YYYYMMDD')."""
    import calendar as _cal
    from datetime import datetime, timedelta
    kst = (datetime.now() + timedelta(hours=9)).date()
    last = kst + timedelta(days=days_ahead)
    try:
        cur = datetime.strptime(initial, "%Y%m%d").date()
    except (ValueError, TypeError):
        cur = kst
    state = {"y": cur.year, "m": cur.month}

    box = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(10))
    hdr = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
    prev = button("◀", None, "ghost", 46)
    prev.size_hint_x = None
    prev.width = dp(52)
    nxt = button("▶", None, "ghost", 46)
    nxt.size_hint_x = None
    nxt.width = dp(52)
    title = label("", size="17sp", halign="center", valign="middle")
    hdr.add_widget(prev)
    hdr.add_widget(title)
    hdr.add_widget(nxt)
    box.add_widget(hdr)
    wk = BoxLayout(size_hint_y=None, height=dp(26))
    for i, d in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
        col = (0.88, 0.33, 0.33, 1) if i == 0 else ((0.4, 0.6, 0.95, 1) if i == 6 else MUTED)
        wk.add_widget(label(d, color=col, size="13sp", halign="center", valign="middle"))
    box.add_widget(wk)
    grid = GridLayout(cols=7, spacing=dp(4), size_hint_y=None)
    grid.bind(minimum_height=grid.setter("height"))
    box.add_widget(grid)
    popup = Popup(title="날짜 선택", content=box, size_hint=(0.94, None), height=dp(470),
                  title_color=TXT, separator_color=ACCENT,
                  background_color=(0.06, 0.07, 0.09, 1))

    def cell(d):
        from datetime import date as _date
        if d == 0:
            return Label(size_hint_y=None, height=dp(48))
        day = _date(state["y"], state["m"], d)
        selectable = kst <= day <= last
        b = button(str(d), None, "ghost", 48)
        b.font_size = "15sp"
        if day == cur:
            b.color = ACCENT  # 선택된 날짜 강조(글자색)
        if not selectable:
            b.disabled = True
            b.opacity = 0.3
        else:
            ymd = day.strftime("%Y%m%d")
            b.bind(on_release=lambda _w, v=ymd: (on_pick(v), popup.dismiss()))
        return b

    def render():
        grid.clear_widgets()
        title.text = f"{state['y']}년 {state['m']}월"
        for week in _cal.Calendar(firstweekday=6).monthdayscalendar(state["y"], state["m"]):
            for d in week:
                grid.add_widget(cell(d))

    def shift(delta):
        m = state["m"] - 1 + delta
        state["y"] += m // 12
        state["m"] = m % 12 + 1
        render()

    prev.bind(on_release=lambda *_: shift(-1))
    nxt.bind(on_release=lambda *_: shift(1))
    render()
    popup.open()


def open_station_picker(on_pick):
    """검색 가능한 역 선택 팝업."""
    box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
    search = Factory.Field()
    search.hint_text = "역 이름 검색"
    search.size_hint_y = None
    search.height = dp(52)
    box.add_widget(search)
    sv = ScrollView()
    lst = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
    lst.bind(minimum_height=lst.setter("height"))
    sv.add_widget(lst)
    box.add_widget(sv)
    popup = Popup(title="역 선택", content=box, size_hint=(0.92, 0.85),
                  title_color=TXT, separator_color=ACCENT,
                  background_color=(0.06, 0.07, 0.09, 1))
    stations = load_stations()

    def render(flt=""):
        lst.clear_widgets()
        for s in stations:
            if flt and flt not in s:
                continue
            b = button(s, None, "ghost", 50)
            b.bind(on_release=lambda _, name=s: (on_pick(name), popup.dismiss()))
            lst.add_widget(b)

    search.bind(text=lambda _w, t: render(t.strip()))
    render()
    popup.open()


class Base(Screen):
    def toast(self, msg):
        self.manager.toast(msg)


# ---------- 화면 ----------
class LoginScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        creds = load_creds()
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        root.add_widget(Label(size_hint_y=0.25))
        root.add_widget(label("[b]korail[color=3CDC84]+[/color][/b]", size="44sp",
                              size_hint_y=None, height=dp(64)))
        root.add_widget(label("코레일+ 통합회원으로 로그인", color=MUTED,
                              size_hint_y=None, height=dp(26)))
        root.add_widget(Label(size_hint_y=None, height=dp(8)))
        self.id_in = field("멤버십번호 / 이메일 / 휴대폰", text=creds.get("id", ""))
        self.pw_in = field("비밀번호", password=True, text=creds.get("pass", ""))
        root.add_widget(self.id_in)
        root.add_widget(self.pw_in)
        arow = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.auto = CheckBox(active=(creds.get("auto") == "Y"), size_hint_x=None,
                             width=dp(40), color=ACCENT)
        arow.add_widget(self.auto)
        arow.add_widget(label("아이디·비밀번호 저장 / 자동 로그인", color=MUTED, halign="left",
                              valign="middle", text_size=(Window.width - dp(110), None)))
        root.add_widget(arow)
        self.btn = button("로그인", self.do_login)
        root.add_widget(self.btn)
        root.add_widget(Label())
        self.add_widget(root)

    def on_enter(self, *a):
        # 자동 로그인: 저장된 계정 + 자동로그인 체크 시 1회 자동 시도
        creds = load_creds()
        if (not getattr(self, "_auto_tried", False) and creds.get("auto") == "Y"
                and creds.get("id") and creds.get("pass")
                and not App.get_running_app().rail):
            self._auto_tried = True
            self.do_login()

    def do_login(self):
        kid, pw = self.id_in.text.strip(), self.pw_in.text
        if not kid or not pw:
            self.toast("아이디와 비밀번호를 입력하세요")
            return
        self.btn.text = "로그인 중…"
        self.btn.disabled = True
        threading.Thread(target=self._work, args=(kid, pw), daemon=True).start()

    def _work(self, kid, pw):
        try:
            rail = Korail(kid, pw, auto_login=True)
            self._done(rail, rail.logined, kid, pw, None)
        except Exception as e:  # noqa
            self._done(None, False, kid, pw, str(e))

    @mainthread
    def _done(self, rail, ok, kid, pw, err):
        self.btn.text = "로그인"
        self.btn.disabled = False
        if ok:
            if self.auto.active:
                save_creds({"id": kid, "pass": pw, "auto": "Y"})
            else:
                save_creds({})  # 저장 안 함
            App.get_running_app().rail = rail
            self.toast(f"{getattr(rail, 'name', '')} 님 환영합니다")
            self.manager.go("menu")
        else:
            self.toast(f"로그인 실패: {err or '정보를 확인하세요'}")


class SearchScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        from datetime import datetime, timedelta
        kst = datetime.now() + timedelta(hours=9)
        # 상태바 여백 + 스크롤: 내용이 길어 화면을 넘겨도 스크롤로 전부 보이게
        outer = BoxLayout(orientation="vertical",
                          padding=[dp(20), dp(SAFE_TOP), dp(20), dp(12)])
        sv = ScrollView()
        root = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(14),
                         padding=[0, 0, 0, dp(16)])
        root.bind(minimum_height=root.setter("height"))
        root.add_widget(header("열차 조회", "코레일+ · KTX"))

        stns = load_stations()
        self._dep = stns[0] if stns else "서울"
        self._arr = stns[-1] if stns else "부산"
        card = Factory.Card()
        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        self.dep_btn = button(self._dep, lambda: open_station_picker(self._set_dep), "ghost", 52)
        self.arr_btn = button(self._arr, lambda: open_station_picker(self._set_arr), "ghost", 52)
        row.add_widget(self.dep_btn)
        row.add_widget(label("→", color=ACCENT, size="20sp", size_hint_x=None, width=dp(26)))
        row.add_widget(self.arr_btn)
        card.add_widget(row)
        card.add_widget(Label(size_hint_y=None, height=dp(2)))
        # 날짜: 캘린더 팝업으로 선택
        self._date = kst.strftime("%Y%m%d")
        self.date_btn = button(fmt_date(self._date),
                               lambda: open_calendar(self._date, self._set_date), "ghost", 52)
        card.add_widget(self.date_btn)
        # 시간: 시 / 분 / 초 3분할
        trow = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.hh = pick(kst.strftime("%H"), [f"{i:02d}" for i in range(24)])
        self.mm = pick("00", [f"{i:02d}" for i in range(0, 60, 5)])
        self.ss = pick("00", [f"{i:02d}" for i in range(0, 60, 10)])
        trow.add_widget(self.hh)
        trow.add_widget(label("시", color=MUTED, size_hint_x=None, width=dp(22)))
        trow.add_widget(self.mm)
        trow.add_widget(label("분", color=MUTED, size_hint_x=None, width=dp(22)))
        trow.add_widget(self.ss)
        trow.add_widget(label("초", color=MUTED, size_hint_x=None, width=dp(22)))
        card.add_widget(trow)
        card.height = dp(48 + 2 + 52 + 48 + 16 * 2 + 6 * 3)
        card.size_hint_y = None
        root.add_widget(card)

        cnts = [str(i) for i in range(0, 10)]
        prow = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        prow.add_widget(label("성인", color=MUTED, size_hint_x=None, width=dp(32)))
        self.adult = pick("1", [str(i) for i in range(1, 10)], width=58)
        prow.add_widget(self.adult)
        prow.add_widget(label("아동", color=MUTED, size_hint_x=None, width=dp(32)))
        self.child = pick("0", cnts, width=58)
        prow.add_widget(self.child)
        prow.add_widget(label("경로", color=MUTED, size_hint_x=None, width=dp(32)))
        self.senior = pick("0", cnts, width=58)
        prow.add_widget(self.senior)
        root.add_widget(prow)
        prow2 = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        prow2.add_widget(label("중증장애", color=MUTED, size_hint_x=None, width=dp(56)))
        self.dis13 = pick("0", cnts, width=58)
        prow2.add_widget(self.dis13)
        prow2.add_widget(label("경증장애", color=MUTED, size_hint_x=None, width=dp(56)))
        self.dis46 = pick("0", cnts, width=58)
        prow2.add_widget(self.dis46)
        prow2.add_widget(Label())
        root.add_widget(prow2)
        # 좌석 종류는 즉시예매/재시도 누를 때 팝업으로 선택(조회 화면에서 제거)
        irow = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        irow.add_widget(label("재시도 간격(초)", color=MUTED, size_hint_x=None, width=dp(110)))
        self.interval = pick("3", ["1", "2", "3", "5", "10", "30"])
        irow.add_widget(self.interval)
        root.add_widget(irow)
        arow = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.autopay_lbl = label("예매 성공 시 자동결제", color=MUTED, size="14sp",
                                 halign="left", valign="middle")
        self.autopay_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        arow.add_widget(self.autopay_lbl)
        self.autopay = CheckBox(active=False, size_hint_x=None, width=dp(48), color=ACCENT)
        arow.add_widget(self.autopay)
        root.add_widget(arow)

        self.btn = button("조회하기", self.do_search)
        root.add_widget(self.btn)
        root.add_widget(button("← 메뉴", lambda: self.manager.go("menu", "right"), "ghost", 46))
        sv.add_widget(root)
        outer.add_widget(sv)
        self.add_widget(outer)

    def on_pre_enter(self, *a):
        # 날짜 기준 시간 자동 설정(오늘=현재 시각, 이후=00:00:00)
        self._apply_time_for_date()
        # 카드 미등록 시 자동결제 비활성화
        has_card = bool(load_card().get("number"))
        self.autopay.disabled = not has_card
        if not has_card:
            self.autopay.active = False
        self.autopay_lbl.text = ("예매 성공 시 자동결제" if has_card
                                 else "자동결제 (카드 등록 필요)")

    def _set_date(self, yyyymmdd):
        self._date = yyyymmdd
        self.date_btn.text = fmt_date(yyyymmdd)
        self._apply_time_for_date()

    def _apply_time_for_date(self):
        """날짜가 오늘이면 현재 시각, 오늘 이후면 00:00:00 으로 시/분/초를 맞춘다.

        분은 5단위, 초는 10단위 피커라 현재 시각은 내림해 맞춘다(임박 열차 누락 방지).
        과거 날짜·형식 오류는 건드리지 않는다."""
        from datetime import datetime, timedelta
        kst = datetime.now() + timedelta(hours=9)
        today = kst.strftime("%Y%m%d")
        date = (self._date or "").strip()
        if len(date) != 8 or not date.isdigit():
            return
        if date == today:
            self.hh.text = kst.strftime("%H")
            self.mm.text = f"{(kst.minute // 5) * 5:02d}"
            self.ss.text = f"{(kst.second // 10) * 10:02d}"
        elif date > today:
            self.hh.text, self.mm.text, self.ss.text = "00", "00", "00"

    def _set_dep(self, name):
        self._dep = name
        self.dep_btn.text = name

    def _set_arr(self, name):
        self._arr = name
        self.arr_btn.text = name

    def _passengers(self):
        ps = [AdultPassenger(int(self.adult.text))]
        if int(self.child.text) > 0:
            ps.append(ChildPassenger(int(self.child.text)))
        if int(self.senior.text) > 0:
            ps.append(SeniorPassenger(int(self.senior.text)))
        if int(self.dis13.text) > 0:
            ps.append(Disability1To3Passenger(int(self.dis13.text)))
        if int(self.dis46.text) > 0:
            ps.append(Disability4To6Passenger(int(self.dis46.text)))
        return ps

    def do_search(self):
        app = App.get_running_app()
        if not app.rail:
            self.manager.go("login", "right")
            return
        self.btn.text = "조회 중…"
        self.btn.disabled = True
        params = dict(dep=self._dep, arr=self._arr,
                      date=self._date.strip(),
                      time=f"{self.hh.text}{self.mm.text}{self.ss.text}",
                      adult=int(self.adult.text), child=int(self.child.text),
                      senior=int(self.senior.text), dis13=int(self.dis13.text),
                      dis46=int(self.dis46.text), interval=self.interval.text,
                      auto_pay="Y" if self.autopay.active else "N",
                      passengers=self._passengers())
        threading.Thread(target=self._work, args=(app.rail, params), daemon=True).start()

    def _work(self, rail, params):
        try:
            # 매진 열차도 모두 표시(자동 재시도 대상으로 선택 가능해야 함).
            # 결과 화면에서 특실/일반실 매진·가능을 색상으로 구분해 보여준다.
            trains = rail.search_train(params["dep"], params["arr"], date=params["date"],
                                       time=params["time"], passengers=params["passengers"],
                                       include_no_seats=True, include_waiting_list=True)
            self._done(trains, None, params)
        except Exception as e:  # noqa
            self._done([], str(e), params)

    @mainthread
    def _done(self, trains, err, params):
        self.btn.text = "조회하기"
        self.btn.disabled = False
        if err:
            self.toast(f"조회 실패: {err}")
            return
        if not trains:
            self.toast("조회 결과가 없습니다")
            return
        self.manager.get_screen("results").populate(trains, params)
        self.manager.go("results")


class ResultsScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=[dp(16), dp(SAFE_TOP), dp(16), dp(12)], spacing=dp(10))
        head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        head.add_widget(button("←", lambda: self.manager.go("search", "right"), "ghost", 44))
        head.add_widget(label("[b]조회 결과[/b]", color=TXT, size="18sp", halign="left",
                              valign="middle"))
        root.add_widget(head)
        sv = ScrollView()
        self.list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10),
                              padding=[0, dp(6)])
        self.list.bind(minimum_height=self.list.setter("height"))
        sv.add_widget(self.list)
        root.add_widget(sv)
        # 전체 자동재시도 버튼은 하단 고정(리스트를 가리지 않도록)
        self.retry_all = accent_button("전체 열차로 자동 재시도 시작", self._retry_all, 50)
        root.add_widget(self.retry_all)
        self.add_widget(root)

    def populate(self, trains, params):
        self._option = ReserveOption.GENERAL_FIRST  # 폴백(실제 좌석은 팝업에서 선택)
        self._params = params
        self._trains = trains
        self._checks = []  # (train, checkbox) — 선택 재시도용
        self.retry_all.text = "전체 열차로 자동 재시도 시작"
        self.list.clear_widgets()
        for t in trains:
            card = Factory.Card()
            card.size_hint_y = None
            card.height = dp(120)
            dep = f"{t.dep_time[:2]}:{t.dep_time[2:4]}"
            arr = f"{t.arr_time[:2]}:{t.arr_time[2:4]}"
            # 1줄: 열차/시각/구간
            card.add_widget(label(
                f"[b]{t.train_type_name[:3]} {t.train_no}[/b]   {dep}~{arr}   "
                f"{t.dep_name}→{t.arr_name}",
                size="14sp", halign="left", valign="middle", size_hint_y=None, height=dp(24),
                text_size=(Window.width - dp(64), None)))
            # 2줄: 좌석 가능 여부 (CLI와 동일) — 가능=초록, 매진=빨강
            def mark(ok):
                return ("[color=3CDC84]가능[/color]" if ok else "[color=E05555]매진[/color]")
            avail = f"특실 {mark(t.has_special_seat())}   일반실 {mark(t.has_general_seat())}"
            if getattr(t, "wait_reserve_flag", -1) is not None and t.wait_reserve_flag >= 0:
                avail += f"   예약대기 {mark(t.has_general_waiting_list())}"
            card.add_widget(label(avail, size="14sp", halign="left", valign="middle",
                                  size_hint_y=None, height=dp(26),
                                  text_size=(Window.width - dp(64), None)))
            brow = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
            cb = CheckBox(active=False, size_hint_x=None, width=dp(32),
                          color=ACCENT)
            cb.bind(active=self._on_check)
            self._checks.append((t, cb))
            brow.add_widget(cb)
            brow.add_widget(label("선택", color=MUTED, size="13sp", halign="left",
                                  valign="middle", size_hint_x=None, width=dp(36),
                                  text_size=(dp(36), None)))
            brow.add_widget(Label())  # 가변 여백
            ib = button("즉시 예매", lambda tr=t: self._reserve(tr), "primary", 36)
            ib.font_size = "14sp"
            rb = accent_button("재시도", lambda tr=t: self._retry_pick([tr]), 36)
            rb.font_size = "14sp"
            brow.add_widget(ib)
            brow.add_widget(rb)
            card.add_widget(brow)
            self.list.add_widget(card)

    def _selected_trains(self):
        return [t for (t, cb) in getattr(self, "_checks", []) if cb.active]

    def _on_check(self, *a):
        n = len(self._selected_trains())
        self.retry_all.text = (f"선택한 {n}개 열차로 자동 재시도 시작" if n
                               else "전체 열차로 자동 재시도 시작")

    def _choose_seat(self, on_pick):
        """좌석 종류 선택 팝업(4지선다). 선택 시 on_pick(ReserveOption)."""
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16))
        box.add_widget(label("좌석 종류를 선택하세요", color=TXT, size="16sp",
                             halign="center", valign="middle", size_hint_y=None, height=dp(34),
                             text_size=(Window.width * 0.72, None)))
        popup = Popup(title="좌석 선택", content=box, size_hint=(0.86, None), height=dp(360),
                      title_color=TXT, separator_color=ACCENT,
                      background_color=(0.06, 0.07, 0.09, 1))
        opts = [("일반실 우선", ReserveOption.GENERAL_FIRST),
                ("일반실만", ReserveOption.GENERAL_ONLY),
                ("특실 우선", ReserveOption.SPECIAL_FIRST),
                ("특실만", ReserveOption.SPECIAL_ONLY)]
        for text, opt in opts:
            b = button(text, None, "ghost", 50)
            b.bind(on_release=lambda _w, o=opt: (popup.dismiss(), on_pick(o)))
            box.add_widget(b)
        popup.open()

    def _reserve(self, train):
        self._choose_seat(lambda opt: self._start_reserve(train, opt))

    def _start_reserve(self, train, option):
        self.toast("예매 시도 중…")
        threading.Thread(target=self._reserve_work, args=(train, option), daemon=True).start()

    def _reserve_work(self, train, option):
        app = App.get_running_app()
        try:
            rsv = app.rail.reserve(train, passengers=self._params["passengers"],
                                   option=option)
            if rsv:
                msg = f"예매 성공! {rsv}"
                # 자동 결제 옵션 + 카드 등록 시 바로 결제
                if self._params.get("auto_pay") == "Y" and load_card().get("number"):
                    try:
                        if pay_reservation(app.rail, rsv):
                            msg = "💳 예매+결제 완료!"
                    except Exception:  # noqa
                        msg += " (자동결제 실패 — 예매확인에서 결제하세요)"
            else:
                msg = "예매 실패"
        except SoldOutError:
            msg = "매진되었습니다"
        except KorailError as e:
            msg = f"예매 실패: {e}"
        except Exception as e:  # noqa
            msg = f"오류: {e}"
        self._toast_main(msg)

    @mainthread
    def _toast_main(self, msg):
        self.toast(msg)

    def _retry_all(self):
        # 체크된 열차가 있으면 그것만, 없으면 전체로 재시도
        sel = self._selected_trains()
        self._retry_pick(sel if sel else self._trains)

    def _retry_pick(self, trains):
        """재시도 전 좌석 종류를 팝업(4지선다)으로 선택."""
        if not trains:
            self.toast("열차가 없습니다")
            return
        self._choose_seat(lambda opt: self._retry(trains, option=opt))

    def _retry(self, trains, option=None):
        s = load_settings()
        creds = load_creds()
        card = load_card()
        notify = s.get("notify", "android") if s.get("enabled", True) else "none"
        dep, arr = self._params["dep"], self._params["arr"]
        d = self._params["date"]
        date_disp = f"{d[4:6]}/{d[6:8]}" if len(d) == 8 else d
        # 재시도 대상 열차의 '실제 출발 시각'을 모두 표시(조회 조건 시간 아님)
        times = [f"{t.dep_time[:2]}:{t.dep_time[2:4]}" for t in trains]
        label = f"{dep}→{arr} {date_disp} · " + ", ".join(times)
        job = {
            "id": creds.get("id"), "pass": creds.get("pass"),
            "dep": dep, "arr": arr,
            "date": self._params["date"], "time": self._params["time"],
            "label": label,  # 현황에 표시할 라벨(열차 출발시각 기준)
            "adult": self._params.get("adult", 1), "child": self._params.get("child", 0),
            "senior": self._params.get("senior", 0), "dis13": self._params.get("dis13", 0),
            "dis46": self._params.get("dis46", 0),
            "option": option or self._option,  # 팝업 선택 좌석 우선, 없으면 조회 옵션
            "train_nos": [t.train_no for t in trains],
            "interval": self._params.get("interval", "3"),
            "notify": notify, "tg_token": s.get("tg_token", ""), "tg_chat": s.get("tg_chat", ""),
            # 자동 결제(조회에서 선택) — 분할된 예약 건마다 적용
            "auto_pay": self._params.get("auto_pay", "N"),
            "card": card if card.get("number") else None,
        }
        started = add_job(job)
        n = len(trains)
        self.toast(f"백그라운드 자동 재시도 추가됨 ({n}개 열차)" if started
                   else "추가됨 — 안드로이드 기기에서 실행하세요")
        self.manager.go("jobs")


class SettingsScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        s = load_settings()
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(SAFE_TOP), dp(20), dp(12)], spacing=dp(12))
        head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        head.add_widget(button("←", lambda: self.manager.go("menu", "right"), "ghost", 44))
        head.add_widget(label("[b]알림 설정[/b]", color=TXT, size="18sp", halign="left",
                              valign="middle"))
        root.add_widget(head)
        # 알림 사용 여부 토글 (맨 위)
        enrow = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        enrow.add_widget(label("알림 사용", color=TXT, size="16sp", halign="left",
                               valign="middle"))
        self.enabled = CheckBox(active=bool(s.get("enabled", True)), size_hint_x=None,
                                width=dp(44), color=ACCENT)
        self.enabled.bind(active=lambda *a: self._toggle_enabled())
        enrow.add_widget(self.enabled)
        root.add_widget(enrow)
        # 알림 방법/텔레그램 입력을 감싸는 영역 (알림 비활성화 시 전체 숨김)
        self.notibox = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        self.notibox.add_widget(label("알림 방법", color=MUTED, size_hint_y=None, height=dp(22),
                                      halign="left", text_size=(Window.width - dp(40), None)))
        rev = {"telegram": "텔레그램", "android": "안드로이드 알림"}
        self.notify = pick(rev.get(s.get("notify", "android"), "안드로이드 알림"),
                           ["안드로이드 알림", "텔레그램"])
        self.notify.size_hint_y = None
        self.notify.height = dp(52)
        self.notify.bind(text=lambda *a: self._toggle_tg())
        self.notibox.add_widget(self.notify)
        # 텔레그램 입력(토큰/chat_id) — 텔레그램 선택 시에만 표시
        self.tgbox = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        self.tgbox.add_widget(label("텔레그램 봇 토큰", color=MUTED, size_hint_y=None, height=dp(22),
                                    halign="left", text_size=(Window.width - dp(40), None)))
        self.tok = field("bot token", text=s.get("tg_token", ""))
        self.tgbox.add_widget(self.tok)
        self.tgbox.add_widget(label("텔레그램 chat_id", color=MUTED, size_hint_y=None, height=dp(22),
                                    halign="left", text_size=(Window.width - dp(40), None)))
        self.chat = field("chat id", text=s.get("tg_chat", ""))
        self.tgbox.add_widget(self.chat)
        self.testbtn = button("연결 테스트", self._test_tg, "ghost", 46)
        self.tgbox.add_widget(self.testbtn)
        self._TG_H = dp(22 + 52 + 22 + 52 + 46 + 12 * 4)
        self.notibox.add_widget(self.tgbox)
        root.add_widget(self.notibox)
        root.add_widget(button("저장", self.save))
        root.add_widget(Label())
        self.add_widget(root)
        self._toggle_enabled()

    def _toggle_enabled(self):
        on = bool(self.enabled.active)
        self.notibox.opacity = 1 if on else 0
        self.notibox.disabled = not on
        self._toggle_tg()  # tgbox 높이 반영 후 notibox 전체 높이 계산

    def _toggle_tg(self):
        show = (self.notify.text == "텔레그램") and bool(self.enabled.active)
        self.tgbox.height = self._TG_H if show else 0
        self.tgbox.opacity = 1 if show else 0
        self.tgbox.disabled = not show
        # notibox 높이 = 라벨(22) + 알림방법 picker(52) + tgbox + 간격(12*2)
        on = bool(self.enabled.active)
        self.notibox.height = (dp(22) + dp(52) + self.tgbox.height + dp(24)) if on else 0

    def _test_tg(self):
        self.testbtn.text = "전송 중…"
        self.testbtn.disabled = True
        tok, chat = self.tok.text.strip(), self.chat.text.strip()
        threading.Thread(target=self._test_tg_work, args=(tok, chat), daemon=True).start()

    def _test_tg_work(self, tok, chat):
        ok, msg = test_telegram(tok, chat)
        self._test_tg_done(ok, msg)

    @mainthread
    def _test_tg_done(self, ok, msg):
        self.testbtn.text = "연결 테스트"
        self.testbtn.disabled = False
        self.toast(("✅ " if ok else "⚠ ") + msg)

    def save(self):
        m = {"텔레그램": "telegram", "안드로이드 알림": "android"}
        save_settings({"enabled": bool(self.enabled.active),
                       "notify": m.get(self.notify.text, "android"),
                       "tg_token": self.tok.text.strip(), "tg_chat": self.chat.text.strip()})
        self.toast("설정이 저장되었습니다")
        self.manager.go("menu", "right")


class JobsScreen(Base):
    """자동 재시도 현황 — 실행 중인 모든 작업 목록 + 작업별 취소/전체 중지."""
    _STATE_LABEL = {"searching": ("재시도 중", MUTED), "partial": ("일부 확보", ACCENT),
                    "done": ("✅ 완료", BRAND), "error": ("⚠ 오류", (0.88, 0.33, 0.33, 1)),
                    "login": ("로그인 중", MUTED)}
    _SEAT_LABEL = {"GENERAL_FIRST": "일반실 우선", "GENERAL_ONLY": "일반실만",
                   "SPECIAL_FIRST": "특실 우선", "SPECIAL_ONLY": "특실만"}

    def __init__(self, **kw):
        super().__init__(**kw)
        self._ev = None
        root = BoxLayout(orientation="vertical",
                         padding=[dp(16), dp(SAFE_TOP), dp(16), dp(12)], spacing=dp(10))
        head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        head.add_widget(button("←", lambda: self.manager.go("menu", "right"), "ghost", 44))
        head.add_widget(label("[b]자동 재시도 현황[/b]", color=TXT, size="18sp", halign="left",
                              valign="middle"))
        root.add_widget(head)
        sv = ScrollView()
        self.list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10),
                              padding=[0, dp(6)])
        self.list.bind(minimum_height=self.list.setter("height"))
        sv.add_widget(self.list)
        root.add_widget(sv)
        self.stopall = button("전체 중지", self._stop_all, "ghost", 48)
        root.add_widget(self.stopall)
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self._render()
        if self._ev:
            self._ev.cancel()
        self._ev = Clock.schedule_interval(lambda *_: self._render(), 1.5)

    def on_leave(self, *a):
        if self._ev:
            self._ev.cancel()
            self._ev = None

    def _render(self, *_):
        jobs = load_jobs()
        statuses = read_job_status()
        self.list.clear_widgets()
        if not jobs:
            self.list.add_widget(label("진행 중인 자동 재시도가 없습니다.", color=MUTED,
                                       size_hint_y=None, height=dp(40), halign="center",
                                       text_size=(Window.width - dp(48), None)))
            return
        for job in jobs:
            st = statuses.get(job.get("jid"), {})
            card = Factory.Card()
            card.size_hint_y = None
            # 내용에 맞춰 카드 높이 자동(출발 시각이 여러 줄이면 늘어남)
            card.bind(minimum_height=card.setter("height"))
            route = (st.get("route") or job.get("label")
                     or f'{job.get("dep")}→{job.get("arr")} {job.get("date","")}')
            rl = label(f"[b]{route}[/b]", size="15sp", halign="left", valign="top",
                       size_hint_y=None, text_size=(Window.width - dp(64), None))
            rl.bind(texture_size=lambda w, ts: setattr(w, "height", ts[1]))
            card.add_widget(rl)
            state = st.get("state", "searching")
            stext, scolor = self._STATE_LABEL.get(state, (state, MUTED))
            booked = len(st.get("booked", []))
            total = st.get("total", "")
            seat = self._SEAT_LABEL.get(job.get("option", ""), "")
            seat_txt = f"   [color={_hex(MUTED)}]{seat}[/color]" if seat else ""
            head2 = f"[color={_hex(scolor)}]{stext}[/color]   확보 {booked}/{total}{seat_txt}"
            card.add_widget(label(head2, size="14sp", halign="left", valign="middle",
                                  size_hint_y=None, height=dp(24),
                                  text_size=(Window.width - dp(64), None)))
            msg = str(st.get("msg", "대기 중"))[:120]  # 과도한 길이 방어
            ml = label(msg, color=MUTED, size="12sp", halign="left", valign="middle",
                       size_hint_y=None, height=dp(22),
                       text_size=(Window.width - dp(64), dp(22)))
            ml.shorten = True           # 한 줄로 말줄임 — 카드 넘침 방지
            ml.shorten_from = "right"
            card.add_widget(ml)
            brow = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
            brow.add_widget(Label())
            cb = button("취소", lambda jid=job.get("jid"): self._cancel(jid), "ghost", 34)
            cb.size_hint_x = None
            cb.width = dp(90)
            cb.font_size = "13sp"
            brow.add_widget(cb)
            card.add_widget(brow)
            self.list.add_widget(card)

    def _cancel(self, job_id):
        cancel_job(job_id)        # 해당 작업만 제거(다른 작업은 계속)
        self.toast("작업을 취소했습니다")
        self._render()

    def _stop_all(self):
        clear_all_jobs()
        self.toast("모든 자동 재시도를 중지했습니다")
        self._render()


class MenuScreen(Base):
    """로그인 후 허브 — TUI 메뉴 대응."""
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(SAFE_TOP), dp(20), dp(12)], spacing=dp(12))
        root.add_widget(header("korail+", "메뉴"))
        self.hello = label("", color=MUTED, size="13sp", halign="left",
                           size_hint_y=None, height=dp(22),
                           text_size=(Window.width - dp(40), None))
        root.add_widget(self.hello)
        items = [
            ("🚆  예매 시작", lambda: self.manager.go("search")),
            ("🔄  자동 재시도 현황", lambda: self.manager.go("jobs")),
            ("🎫  예매 확인 / 결제 / 취소", lambda: self._open_reservations()),
            ("💳  카드 설정", lambda: self.manager.go("card")),
            ("🚉  역 설정", lambda: self.manager.go("station")),
            ("🔔  알림 설정", lambda: self.manager.go("settings")),
        ]
        for text, cb in items:
            b = button(text, cb, "ghost", 56)
            b.halign = "left"
            b.text_size = (Window.width - dp(72), None)
            b.padding_x = dp(18)
            root.add_widget(b)
        root.add_widget(Label())
        root.add_widget(button("로그아웃", self.logout, "ghost", 46))
        self.add_widget(root)

    def on_pre_enter(self, *a):
        rail = App.get_running_app().rail
        self.hello.text = f"{getattr(rail, 'name', '')} 님" if rail else ""

    def _open_reservations(self):
        self.manager.get_screen("reservations").refresh()
        self.manager.go("reservations")

    def logout(self):
        App.get_running_app().rail = None
        self.manager.go("login", "right")


class ReservationsScreen(Base):
    """예매 확인 / 결제 / 취소 / 환불."""
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=[dp(16), dp(SAFE_TOP), dp(16), dp(12)], spacing=dp(10))
        head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        head.add_widget(button("←", lambda: self.manager.go("menu", "right"), "ghost", 44))
        head.add_widget(label("[b]예매 확인[/b]", color=TXT, size="18sp", halign="left",
                              valign="middle"))
        head.add_widget(button("새로고침", self.refresh, "ghost", 44))
        root.add_widget(head)
        sv = ScrollView()
        self.list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10),
                              padding=[0, dp(6)])
        self.list.bind(minimum_height=self.list.setter("height"))
        sv.add_widget(self.list)
        root.add_widget(sv)
        self.add_widget(root)

    def refresh(self, *_):
        self.list.clear_widgets()
        self.list.add_widget(label("불러오는 중…", color=MUTED, size_hint_y=None, height=dp(40)))
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        rail = App.get_running_app().rail
        try:
            reservations = rail.reservations() or []
            tickets = rail.tickets() or []
            err = None
        except Exception as e:  # noqa
            reservations, tickets, err = [], [], str(e)
        self._render(reservations, tickets, err)

    @mainthread
    def _render(self, reservations, tickets, err):
        self.list.clear_widgets()
        if err:
            self.list.add_widget(label(f"오류: {err}", color=MUTED, size_hint_y=None, height=dp(40)))
            return
        if not reservations and not tickets:
            self.list.add_widget(label("예매 내역이 없습니다", color=MUTED,
                                       size_hint_y=None, height=dp(40)))
            return
        for t in tickets:  # 발권 완료 → 환불
            self._card(str(t), [("환불", lambda x=t: self._refund(x), (0.8, 0.26, 0.26, 1))])
        for r in reservations:  # 미결제 → 결제/취소
            waiting = getattr(r, "is_waiting", False)
            actions = []
            if not waiting:
                actions.append(("결제", lambda x=r: self._pay(x), PRIMARY))
            actions.append(("취소", lambda x=r: self._cancel(x), (0.5, 0.3, 0.3, 1)))
            self._card(str(r) + ("  (예약대기)" if waiting else ""), actions)

    def _card(self, text, actions):
        card = Factory.Card()
        card.size_hint_y = None
        card.height = dp(96)
        card.add_widget(label(text, size="13sp", halign="left", valign="top",
                              size_hint_y=None, height=dp(52),
                              text_size=(Window.width - dp(64), None)))
        row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        row.add_widget(Label())
        for name, cb, color in actions:
            b = button(name, cb, "primary", 34)
            b.bg = color
            b.font_size = "14sp"
            b.size_hint_x = None
            b.width = dp(90)
            row.add_widget(b)
        card.add_widget(row)
        self.list.add_widget(card)

    def _pay(self, rsv):
        if not load_card().get("number"):
            self.toast("먼저 카드를 등록하세요")
            self.manager.go("card")
            return
        self.toast("결제 중…")
        threading.Thread(target=self._pay_worker, args=(rsv,), daemon=True).start()

    def _pay_worker(self, rsv):
        rail = App.get_running_app().rail
        try:
            ok = pay_reservation(rail, rsv)
            self._after("💳 결제 성공" if ok else "결제 실패")
        except Exception as e:  # noqa
            self._after(f"결제 오류: {e}")

    def _cancel(self, rsv):
        self.toast("취소 중…")
        threading.Thread(target=self._cancel_worker, args=(rsv,), daemon=True).start()

    def _cancel_worker(self, rsv):
        rail = App.get_running_app().rail
        try:
            rail.cancel(rsv)
            self._after("예약 취소됨")
        except Exception as e:  # noqa
            self._after(f"취소 오류: {e}")

    def _refund(self, ticket):
        # 먼저 수수료를 조회해 팝업으로 보여주고, 확인 시에만 실제 환불
        self.toast("환불 수수료 조회 중…")
        threading.Thread(target=self._refund_fee_worker, args=(ticket,), daemon=True).start()

    def _refund_fee_worker(self, ticket):
        rail = App.get_running_app().rail
        try:
            info = rail.refund_fee(ticket)
            self._show_fee_popup(ticket, info, None)
        except Exception as e:  # noqa
            self._show_fee_popup(ticket, None, str(e))

    @mainthread
    def _show_fee_popup(self, ticket, info, err):
        box = BoxLayout(orientation="vertical", spacing=dp(14), padding=dp(16))
        if err or info is None:
            box.add_widget(label(f"수수료 조회 실패\n{err or ''}", color=TXT, size="15sp",
                                 halign="center", valign="middle",
                                 text_size=(Window.width * 0.7, None)))
        elif not info.get("refundable"):
            box.add_widget(label("이 승차권은 환불할 수 없습니다.", color=TXT, size="16sp",
                                 halign="center", valign="middle",
                                 text_size=(Window.width * 0.7, None)))
        else:
            fee, amt = info.get("fee", 0), info.get("amount", 0)
            box.add_widget(label(
                f"환불 수수료: [b][color=E05555]{fee:,}원[/color][/b]\n"
                f"돌려받는 금액: [b][color={_hex(ACCENT)}]{amt:,}원[/color][/b]",
                color=TXT, size="17sp", halign="center", valign="middle",
                size_hint_y=None, height=dp(80), text_size=(Window.width * 0.7, None)))
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        popup = Popup(title="환불 확인", content=box, size_hint=(0.88, None), height=dp(260),
                      title_color=TXT, separator_color=ACCENT,
                      background_color=(0.06, 0.07, 0.09, 1))
        btns.add_widget(button("닫기", lambda: popup.dismiss(), "ghost", 50))
        if info and info.get("refundable"):
            def _do(*_):
                popup.dismiss()
                self.toast("환불 중…")
                threading.Thread(target=self._refund_worker, args=(ticket,),
                                 daemon=True).start()
            rb = accent_button("환불하기", _do, 50)
            rb.bg = (0.8, 0.26, 0.26, 1)
            btns.add_widget(rb)
        box.add_widget(btns)
        popup.open()

    def _refund_worker(self, ticket):
        rail = App.get_running_app().rail
        try:
            rail.refund(ticket)
            self._after("환불 완료")
        except Exception as e:  # noqa
            self._after(f"환불 오류: {e}")

    @mainthread
    def _after(self, msg):
        self.toast(msg)
        self.refresh()


class CardScreen(Base):
    """카드 설정 — 자동 결제용."""
    def __init__(self, **kw):
        super().__init__(**kw)
        c = load_card()
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(SAFE_TOP), dp(20), dp(12)], spacing=dp(12))
        head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        head.add_widget(button("←", lambda: self.manager.go("menu", "right"), "ghost", 44))
        head.add_widget(label("[b]카드 설정[/b]", color=TXT, size="18sp", halign="left",
                              valign="middle"))
        root.add_widget(head)
        root.add_widget(label("자동 결제에 사용됩니다. 기기에만 저장됩니다.", color=MUTED,
                              size_hint_y=None, height=dp(22), halign="left",
                              text_size=(Window.width - dp(40), None)))
        self.num = field("카드번호 (하이픈 제외)", text=c.get("number", ""))
        self.pw = field("카드 비밀번호 앞 2자리", password=True, text=c.get("password", ""))
        self.bday = field("생년월일 YYMMDD / 사업자번호", text=c.get("birthday", ""))
        self.exp = field("유효기간 YYMM", text=c.get("expire", ""))
        for w in (self.num, self.pw, self.bday, self.exp):
            root.add_widget(w)
        root.add_widget(button("저장", self.save))
        root.add_widget(Label())
        self.add_widget(root)

    def save(self):
        save_card({"number": self.num.text.strip(), "password": self.pw.text.strip(),
                   "birthday": self.bday.text.strip(), "expire": self.exp.text.strip()})
        self.toast("카드 정보 저장됨")
        self.manager.go("menu", "right")


class StationScreen(Base):
    """역 설정 — 역 추가/삭제."""
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=[dp(16), dp(SAFE_TOP), dp(16), dp(12)], spacing=dp(10))
        head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        head.add_widget(button("←", lambda: self.manager.go("menu", "right"), "ghost", 44))
        head.add_widget(label("[b]역 설정[/b]", color=TXT, size="18sp", halign="left",
                              valign="middle"))
        root.add_widget(head)
        addrow = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        self.new = field("추가할 역 이름 (예: 수서)")
        self.new.bind(on_text_validate=lambda *_: self._add())  # 엔터로도 추가
        addrow.add_widget(self.new)
        b = button("추가", self._add, "primary", 52)
        b.size_hint_x = None
        b.width = dp(80)
        addrow.add_widget(b)
        root.add_widget(addrow)
        self.fetchbtn = accent_button("🔄 코레일에서 전체 역 불러오기", self._load_from_korail, 46)
        root.add_widget(self.fetchbtn)
        root.add_widget(label("등록된 역 (오른쪽 '삭제' 버튼으로 제거)", color=MUTED,
                              size_hint_y=None, height=dp(22), halign="left",
                              text_size=(Window.width - dp(32), None)))
        sv = ScrollView()
        self.list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6),
                              padding=[0, dp(4)])
        self.list.bind(minimum_height=self.list.setter("height"))
        sv.add_widget(self.list)
        root.add_widget(sv)
        self.add_widget(root)
        self._render()

    def _render(self):
        self.list.clear_widgets()
        for s in load_stations():
            rowc = Factory.Card()
            rowc.size_hint_y = None
            rowc.height = dp(50)
            rowc.padding = dp(10)
            r = BoxLayout(spacing=dp(8))
            r.add_widget(label(s, size="15sp", halign="left", valign="middle",
                               text_size=(Window.width - dp(120), None)))
            x = button("삭제", lambda name=s: self._remove(name), "ghost", 40)
            x.size_hint_x = None
            x.width = dp(72)
            x.font_size = "14sp"
            r.add_widget(x)
            rowc.add_widget(r)
            self.list.add_widget(rowc)

    def _add(self):
        name = self.new.text.strip()
        if not name:
            return
        stns = load_stations()
        if name not in stns:
            stns.insert(0, name)  # 맨 위에 추가 → 바로 보이게
            save_stations(stns)
            self.toast(f"'{name}' 추가됨")
        else:
            self.toast(f"'{name}' 은 이미 있습니다")
        self.new.text = ""
        self._render()

    def _remove(self, name):
        stns = [s for s in load_stations() if s != name]
        save_stations(stns)
        self._render()

    def _load_from_korail(self):
        self.fetchbtn.text = "불러오는 중…"
        self.fetchbtn.disabled = True
        threading.Thread(target=self._fetch_work, daemon=True).start()

    def _fetch_work(self):
        names = fetch_station_master(force=True)
        self._fetch_done(names)

    @mainthread
    def _fetch_done(self, names):
        self.fetchbtn.text = "🔄 코레일에서 전체 역 불러오기"
        self.fetchbtn.disabled = False
        if names:
            save_stations(names)  # 커스텀 목록으로 저장 → 조회 선택창에도 반영
            self.toast(f"코레일 역 {len(names)}개 불러옴")
            self._render()
        else:
            self.toast("역 목록을 불러오지 못했습니다 (네트워크 확인)")


class Manager(ScreenManager):
    def go(self, name, direction="left"):
        self.transition = SlideTransition(direction=direction, duration=0.22)
        self.current = name

    def toast(self, msg):
        # ScreenManager는 Screen만 받으므로 토스트는 Window에 오버레이로 올린다.
        from kivy.graphics import Color, RoundedRectangle
        lbl = Label(text=msg, color=(1, 1, 1, 1), font_size="14sp",
                    size_hint=(None, None), halign="center", valign="middle",
                    pos_hint={"center_x": 0.5, "y": 0.05})
        lbl.text_size = (Window.width * 0.86, None)
        lbl.texture_update()
        lbl.size = (Window.width * 0.9, max(dp(44), lbl.texture_size[1] + dp(20)))
        with lbl.canvas.before:
            Color(0.05, 0.05, 0.06, 0.95)
            rr = RoundedRectangle(radius=[dp(12), dp(12), dp(12), dp(12)])
        lbl.bind(pos=lambda w, *_: setattr(rr, "pos", w.pos),
                 size=lambda w, *_: setattr(rr, "size", w.size))
        Window.add_widget(lbl)
        Clock.schedule_once(lambda *_: Window.remove_widget(lbl), 2.6)


class KorailPlusApp(App):
    rail = None

    def build(self):
        self.title = "korail+"
        sm = Manager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(SearchScreen(name="search"))
        sm.add_widget(ResultsScreen(name="results"))
        sm.add_widget(ReservationsScreen(name="reservations"))
        sm.add_widget(CardScreen(name="card"))
        sm.add_widget(StationScreen(name="station"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(JobsScreen(name="jobs"))
        sm.current = "login"  # 항상 로그인 화면으로 시작
        request_notification_permission()  # 알림 권한(Android 13+) 요청
        ensure_station_master_async()  # 코레일 역 마스터 캐시 백그라운드 준비
        return sm


if __name__ == "__main__":
    KorailPlusApp().run()
