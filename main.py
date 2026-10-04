"""korail+ Android GUI (Kivy) — 현대적 다크 UI

korailplus/ktx.py 코어를 재사용. 자동 재시도는 service.py(Foreground Service)가 담당.
한글 렌더링을 위해 NanumGothic을 기본 폰트로 등록한다.
"""
import json
import os
import sys
import threading
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
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.scrollview import ScrollView

# 핫패치: 번들/캐시 ktx를 즉시 로드하고 백그라운드로 최신본을 받아둔다(다음 실행 반영)
from korailplus import updater as _updater

_K = _updater.load_ktx()
AdultPassenger = _K.AdultPassenger
ChildPassenger = _K.ChildPassenger
Korail = _K.Korail
KorailError = _K.KorailError
ReserveOption = _K.ReserveOption
SoldOutError = _K.SoldOutError

Window.clearcolor = (0.055, 0.063, 0.078, 1)  # #0E1014

KTX_STATIONS = ["서울", "용산", "광명", "천안아산", "오송", "대전", "동대구", "부산",
                "울산", "포항", "마산", "진주", "여수EXPO", "목포", "광주송정",
                "전주", "익산", "강릉", "청량리", "수원"]

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


# ---------- 저장소/설정/서비스 제어 ----------
def _cfg_dir():
    base = os.path.join(os.path.expanduser("~"), ".config", "korailplus")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        base = os.path.expanduser("~")
    return base


CRED_PATH = os.path.join(_cfg_dir(), "credentials.json")
SETTINGS_PATH = os.path.join(_cfg_dir(), "settings.json")
TASK_PATH = os.path.join(_cfg_dir(), "task.json")
STATUS_PATH = os.path.join(_cfg_dir(), "status.json")
STOP_PATH = os.path.join(_cfg_dir(), "stop.flag")


def _load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def load_creds():
    return _load(CRED_PATH, {})


def save_creds(d):
    _save(CRED_PATH, d)


def load_settings():
    return _load(SETTINGS_PATH, {"notify": "telegram", "tg_token": "", "tg_chat": "", "interval": "3"})


def save_settings(d):
    _save(SETTINGS_PATH, d)


def write_task(task):
    try:
        if os.path.exists(STOP_PATH):
            os.remove(STOP_PATH)
    except OSError:
        pass
    _save(TASK_PATH, task)


def read_status():
    return _load(STATUS_PATH, {})


def start_retry_service():
    try:
        from jnius import autoclass

        ctx = autoclass("org.kivy.android.PythonActivity").mActivity
        Intent = autoclass("android.content.Intent")
        Service = autoclass("org.korailplus.korailplus.ServiceKorailretry")
        intent = Intent(ctx, Service)
        VERSION = autoclass("android.os.Build$VERSION")
        if VERSION.SDK_INT >= 26:
            ctx.startForegroundService(intent)
        else:
            ctx.startService(intent)
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
        Intent = autoclass("android.content.Intent")
        Service = autoclass("org.korailplus.korailplus.ServiceKorailretry")
        ctx.stopService(Intent(ctx, Service))
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
        self.btn = button("로그인", self.do_login)
        root.add_widget(self.btn)
        root.add_widget(Label())
        self.add_widget(root)

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
            save_creds({"id": kid, "pass": pw})
            App.get_running_app().rail = rail
            self.toast(f"{getattr(rail, 'name', '')} 님 환영합니다")
            self.manager.go("search")
        else:
            self.toast(f"로그인 실패: {err or '정보를 확인하세요'}")


class SearchScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        from datetime import datetime, timedelta
        kst = datetime.now() + timedelta(hours=9)
        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(14))
        root.add_widget(header("열차 조회", "코레일+ · KTX"))

        card = Factory.Card()
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        self.dep = pick("서울", KTX_STATIONS)
        self.arr = pick("부산", KTX_STATIONS)
        row.add_widget(self.dep)
        row.add_widget(label("→", color=ACCENT, size="20sp", size_hint_x=None, width=dp(26)))
        row.add_widget(self.arr)
        card.add_widget(row)
        card.add_widget(Label(size_hint_y=None, height=dp(2)))
        self.date_in = field("날짜 YYYYMMDD", text=kst.strftime("%Y%m%d"))
        self.time_in = field("시각 HHMMSS", text=kst.strftime("%H0000"))
        card.add_widget(self.date_in)
        card.add_widget(self.time_in)
        card.height = dp(48 + 2 + 52 + 52 + 16 * 2 + 6 * 3)
        card.size_hint_y = None
        root.add_widget(card)

        prow = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        prow.add_widget(label("성인", color=MUTED, size_hint_x=None, width=dp(36)))
        self.adult = pick("1", [str(i) for i in range(1, 7)], width=64)
        prow.add_widget(self.adult)
        prow.add_widget(label("아동", color=MUTED, size_hint_x=None, width=dp(36)))
        self.child = pick("0", [str(i) for i in range(0, 7)], width=64)
        prow.add_widget(self.child)
        root.add_widget(prow)
        self.seat = pick("일반실 우선", list(SEAT_OPTIONS))
        root.add_widget(self.seat)

        self.btn = button("조회하기", self.do_search)
        root.add_widget(self.btn)
        brow = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        brow.add_widget(button("알림 설정", lambda: self.manager.go("settings"), "ghost", 46))
        brow.add_widget(button("진행 상태", lambda: self.manager.go("status"), "ghost", 46))
        brow.add_widget(button("로그아웃", self.logout, "ghost", 46))
        root.add_widget(brow)
        root.add_widget(Label())
        self.add_widget(root)

    def logout(self):
        App.get_running_app().rail = None
        self.manager.go("login", "right")

    def _passengers(self):
        ps = [AdultPassenger(int(self.adult.text))]
        if int(self.child.text) > 0:
            ps.append(ChildPassenger(int(self.child.text)))
        return ps

    def do_search(self):
        app = App.get_running_app()
        if not app.rail:
            self.manager.go("login", "right")
            return
        self.btn.text = "조회 중…"
        self.btn.disabled = True
        params = dict(dep=self.dep.text, arr=self.arr.text,
                      date=self.date_in.text.strip(),
                      time=self.time_in.text.strip() or None,
                      adult=int(self.adult.text), child=int(self.child.text),
                      passengers=self._passengers())
        threading.Thread(target=self._work, args=(app.rail, params), daemon=True).start()

    def _work(self, rail, params):
        try:
            trains = rail.search_train(params["dep"], params["arr"], date=params["date"],
                                       time=params["time"], passengers=params["passengers"])
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
        self.manager.get_screen("results").populate(trains, self.seat.text, params)
        self.manager.go("results")


class ResultsScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        head.add_widget(button("←", lambda: self.manager.go("search", "right"), "ghost", 44))
        head.add_widget(label("[b]조회 결과[/b]", color=TXT, size="18sp", halign="left",
                              valign="middle"))
        root.add_widget(head)
        self.retry_all = accent_button("전체 열차로 자동 재시도 시작", self._retry_all, 48)
        root.add_widget(self.retry_all)
        sv = ScrollView()
        self.list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10),
                              padding=[0, dp(6)])
        self.list.bind(minimum_height=self.list.setter("height"))
        sv.add_widget(self.list)
        root.add_widget(sv)
        self.add_widget(root)

    def populate(self, trains, seat_text, params):
        self._seat_text = seat_text
        self._option = SEAT_OPTIONS[seat_text]
        self._params = params
        self._trains = trains
        self.list.clear_widgets()
        for t in trains:
            card = Factory.Card()
            card.size_hint_y = None
            card.height = dp(94)
            dep = f"{t.dep_time[:2]}:{t.dep_time[2:4]}"
            arr = f"{t.arr_time[:2]}:{t.arr_time[2:4]}"
            top = BoxLayout(size_hint_y=None, height=dp(26))
            top.add_widget(label(f"[b]{t.train_type_name[:3]} {t.train_no}[/b]",
                                 size="15sp", halign="left", valign="middle",
                                 text_size=(Window.width * 0.45, None)))
            top.add_widget(label(f"{dep} → {arr}", color=ACCENT, size="15sp",
                                 halign="right", valign="middle",
                                 text_size=(Window.width * 0.4, None)))
            card.add_widget(top)
            sp = "특실 " + ("가능" if t.has_special_seat() else "매진")
            gn = "일반 " + ("가능" if t.has_general_seat() else "매진")
            card.add_widget(label(f"{t.dep_name} → {t.arr_name}    [color=8A8F97]{sp} · {gn}[/color]",
                                  color=MUTED, size="13sp", halign="left", valign="middle",
                                  size_hint_y=None, height=dp(22),
                                  text_size=(Window.width - dp(64), None)))
            brow = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
            brow.add_widget(Label(size_hint_x=0.4))
            ib = button("즉시 예매", lambda tr=t: self._reserve(tr), "primary", 34)
            ib.font_size = "14sp"
            rb = accent_button("재시도", lambda tr=t: self._retry([tr]), 34)
            rb.font_size = "14sp"
            brow.add_widget(ib)
            brow.add_widget(rb)
            card.add_widget(brow)
            self.list.add_widget(card)

    def _reserve(self, train):
        self.toast("예매 시도 중…")
        threading.Thread(target=self._reserve_work, args=(train,), daemon=True).start()

    def _reserve_work(self, train):
        app = App.get_running_app()
        try:
            rsv = app.rail.reserve(train, passengers=self._params["passengers"],
                                   option=self._option)
            msg = f"예매 성공! {rsv}" if rsv else "예매 실패"
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
        self._retry(self._trains)

    def _retry(self, trains):
        s = load_settings()
        creds = load_creds()
        task = {
            "id": creds.get("id"), "pass": creds.get("pass"),
            "dep": self._params["dep"], "arr": self._params["arr"],
            "date": self._params["date"], "time": self._params["time"],
            "adult": self._params.get("adult", 1), "child": self._params.get("child", 0),
            "option": self._option,  # ReserveOption 값 == 문자열
            "train_nos": [t.train_no for t in trains],
            "interval": s.get("interval", "3"), "notify": s.get("notify", "telegram"),
            "tg_token": s.get("tg_token", ""), "tg_chat": s.get("tg_chat", ""),
        }
        write_task(task)
        started = start_retry_service()
        self.manager.get_screen("status").begin(started)
        self.manager.go("status")


class SettingsScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        s = load_settings()
        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))
        head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        head.add_widget(button("←", lambda: self.manager.go("search", "right"), "ghost", 44))
        head.add_widget(label("[b]알림 설정[/b]", color=TXT, size="18sp", halign="left",
                              valign="middle"))
        root.add_widget(head)
        root.add_widget(label("알림 방법", color=MUTED, size_hint_y=None, height=dp(22),
                              halign="left", text_size=(Window.width - dp(40), None)))
        rev = {"telegram": "텔레그램", "android": "안드로이드 알림", "both": "둘 다"}
        self.notify = pick(rev.get(s.get("notify", "telegram"), "텔레그램"),
                           ["텔레그램", "안드로이드 알림", "둘 다"])
        root.add_widget(self.notify)
        root.add_widget(label("재시도 간격(초)", color=MUTED, size_hint_y=None, height=dp(22),
                              halign="left", text_size=(Window.width - dp(40), None)))
        self.interval = field("3", text=str(s.get("interval", "3")))
        root.add_widget(self.interval)
        root.add_widget(label("텔레그램 봇 토큰", color=MUTED, size_hint_y=None, height=dp(22),
                              halign="left", text_size=(Window.width - dp(40), None)))
        self.tok = field("bot token", text=s.get("tg_token", ""))
        root.add_widget(self.tok)
        root.add_widget(label("텔레그램 chat_id", color=MUTED, size_hint_y=None, height=dp(22),
                              halign="left", text_size=(Window.width - dp(40), None)))
        self.chat = field("chat id", text=s.get("tg_chat", ""))
        root.add_widget(self.chat)
        root.add_widget(button("저장", self.save))
        root.add_widget(Label())
        self.add_widget(root)

    def save(self):
        m = {"텔레그램": "telegram", "안드로이드 알림": "android", "둘 다": "both"}
        save_settings({"notify": m.get(self.notify.text, "telegram"),
                       "interval": self.interval.text.strip() or "3",
                       "tg_token": self.tok.text.strip(), "tg_chat": self.chat.text.strip()})
        self.toast("설정이 저장되었습니다")
        self.manager.go("search", "right")


class StatusScreen(Base):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._ev = None
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(18))
        root.add_widget(Label(size_hint_y=0.15))
        root.add_widget(label("[b]자동 재시도[/b]", color=ACCENT, size="24sp",
                              size_hint_y=None, height=dp(40)))
        self.state = label("대기 중", size="18sp", size_hint_y=None, height=dp(32))
        self.msg = label("", color=MUTED, size="14sp", halign="center",
                         size_hint_y=None, height=dp(90))
        self.msg.bind(width=lambda w, *_: setattr(w, "text_size", (w.width - dp(20), None)))
        root.add_widget(self.state)
        root.add_widget(self.msg)
        self.stopbtn = button("중지", self.stop, "primary")
        self.stopbtn.bg = (0.8, 0.26, 0.26, 1)
        root.add_widget(self.stopbtn)
        root.add_widget(button("조회로 돌아가기", lambda: self.manager.go("search", "right"), "ghost", 46))
        root.add_widget(Label())
        self.add_widget(root)

    def begin(self, started):
        self.state.text = "실행 중" if started else "시작 실패"
        self.msg.text = ("백그라운드에서 재시도합니다.\n화면을 꺼도 계속 동작합니다."
                         if started else "서비스를 시작하지 못했습니다.\n안드로이드 기기에서 실행하세요.")
        if self._ev:
            self._ev.cancel()
        self._ev = Clock.schedule_interval(self._poll, 1.5)

    def _poll(self, *_):
        st = read_status()
        if not st:
            return
        state = st.get("state", "")
        self.state.text = {"login": "로그인 중", "searching": "재시도 중",
                           "done": "✅ 예매 성공", "stopped": "중지됨",
                           "error": "오류"}.get(state, state)
        self.msg.text = st.get("msg", "")
        if state in ("done", "stopped", "error") and self._ev:
            self._ev.cancel()
            self._ev = None

    def stop(self):
        stop_retry_service()
        self.toast("중지 요청됨")

    def on_leave(self, *a):
        if self._ev:
            self._ev.cancel()
            self._ev = None


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
        sm.add_widget(SearchScreen(name="search"))
        sm.add_widget(ResultsScreen(name="results"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(StatusScreen(name="status"))
        sm.current = "login"  # 항상 로그인 화면으로 시작
        return sm


if __name__ == "__main__":
    KorailPlusApp().run()
