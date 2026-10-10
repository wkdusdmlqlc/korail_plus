"""korail+ 백그라운드 자동 재시도 서비스 (python-for-android Foreground Service)

여러 경로(작업)를 동시에 백그라운드로 재시도한다.
- main.py(GUI)가 jobs.json(작업 목록)에 경로를 추가하고 이 서비스를 시작한다.
- 서비스는 로그인 1회(동일 계정) 후, 매 사이클마다 모든 활성 작업을 순회하며
  조회 -> 예매를 시도하고 상태를 job_status.json에 기록한다.
- 예매: 전원 한 번에 시도하고, 실패하면 1명씩 분할 예매(되는 만큼 먼저 확보 +
  나머지 계속 재시도). 각 예약 건은 설정에 따라 자동결제.
- 작업별 취소: GUI가 jobs.json에서 해당 작업만 제거 → 다음 사이클에 그 작업만
  빠지고 나머지는 계속 진행(확보된 예약은 유지).
- 전체 중지: stop.flag 생성 → 모든 작업 중단 후 서비스 종료.
"""
import json
import os
import time
import traceback

# 핫패치: 번들/캐시 ktx를 즉시 로드(백그라운드로 최신본 확인)
from korailplus import updater as _updater

_K = _updater.load_ktx()
AdultPassenger = _K.AdultPassenger
ChildPassenger = _K.ChildPassenger
SeniorPassenger = _K.SeniorPassenger
Disability1To3Passenger = _K.Disability1To3Passenger
Disability4To6Passenger = _K.Disability4To6Passenger
Korail = _K.Korail
NoResultsError = _K.NoResultsError
ReserveOption = _K.ReserveOption
SoldOutError = _K.SoldOutError

_ROOT = os.environ.get("ANDROID_PRIVATE") or os.path.join(os.path.expanduser("~"), ".config")
CFG_DIR = os.path.join(_ROOT, "korailplus")
try:
    os.makedirs(CFG_DIR, exist_ok=True)
except OSError:
    pass
JOBS = os.path.join(CFG_DIR, "jobs.json")           # GUI가 추가/취소하는 작업 목록
JOBSTATUS = os.path.join(CFG_DIR, "job_status.json")  # 서비스가 쓰는 작업별 상태
STOP = os.path.join(CFG_DIR, "stop.flag")

# 승객 유형 키 -> (Passenger 클래스)
_PSG_TYPES = [
    ("adult", AdultPassenger),
    ("child", ChildPassenger),
    ("senior", SeniorPassenger),
    ("dis13", Disability1To3Passenger),
    ("dis46", Disability4To6Passenger),
]


def _load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save(path, data):
    """원자적 저장(tmp+replace) — GUI와의 동시 접근 경합 방지."""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except OSError:
        pass


def _counts_total(counts):
    return sum(int(counts.get(k, 0)) for k, _ in _PSG_TYPES)


def _group_passengers(counts):
    """잔여 counts -> 유형별 Passenger 리스트(전원 묶음 예매용)."""
    ps = []
    for key, cls in _PSG_TYPES:
        n = int(counts.get(key, 0))
        if n > 0:
            ps.append(cls(n))
    return ps or [AdultPassenger(1)]


def _one_passenger(key):
    for k, cls in _PSG_TYPES:
        if k == key:
            return cls(1)
    return AdultPassenger(1)


# ---------- 알림 ----------
def _notify(job, title, msg):
    method = job.get("notify", "android")
    if method == "android":
        _notify_android(title, msg)
    elif method == "telegram":
        ok, err = _notify_telegram(job, f"{title}\n{msg}")
        if not ok:
            # 조용히 실패하지 않도록 안드로이드 알림으로 폴백(원인 포함)
            _notify_android("⚠ 텔레그램 전송 실패",
                            f"{err}\n알림 설정에서 토큰/chat_id를 확인하세요.\n(알림: {title})")


def _notify_android(title, msg):
    try:
        from jnius import autoclass, cast

        PythonService = autoclass("org.kivy.android.PythonService")
        service = PythonService.mService
        Context = autoclass("android.content.Context")
        NotificationBuilder = autoclass("android.app.Notification$Builder")
        NotificationManager = autoclass("android.app.NotificationManager")
        NotificationChannel = autoclass("android.app.NotificationChannel")
        Build = autoclass("android.os.Build$VERSION")

        nm = cast(NotificationManager, service.getSystemService(Context.NOTIFICATION_SERVICE))
        chan_id = "korailplus_alert"
        if Build.SDK_INT >= 26:
            chan = NotificationChannel(chan_id, "korail+ 알림",
                                      NotificationManager.IMPORTANCE_HIGH)
            nm.createNotificationChannel(chan)
            builder = NotificationBuilder(service, chan_id)
        else:
            builder = NotificationBuilder(service)
        icon = service.getApplicationInfo().icon
        builder.setContentTitle(title)
        builder.setContentText(msg)
        builder.setSmallIcon(icon)
        builder.setAutoCancel(True)
        # 작업마다 다른 알림 ID(해시)로 띄워 서로 덮어쓰지 않게
        nm.notify(2000 + (abs(hash(title + msg)) % 1000), builder.build())
    except Exception:
        traceback.print_exc()


def _notify_telegram(job, text):
    """텔레그램 전송. (성공여부, 오류메시지) 반환 — 실패 시 상위에서 폴백 알림."""
    token, chat = job.get("tg_token"), job.get("tg_chat")
    if not token or not chat:
        return False, "토큰/chat_id가 비어 있습니다"
    try:
        import requests

        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat, "text": text}, timeout=10,
        )
        try:
            j = r.json()
        except ValueError:
            j = {}
        if r.status_code == 200 and j.get("ok"):
            return True, ""
        return False, j.get("description") or f"HTTP {r.status_code}"
    except Exception as e:  # noqa
        traceback.print_exc()
        return False, str(e)


# ---------- 결제 ----------
def _pay(rail, job, rsv):
    card = job.get("card")
    if job.get("auto_pay") != "Y" or not card or not card.get("number"):
        return False
    try:
        bday = card.get("birthday", "")
        return bool(rail.pay_with_card(
            rsv, card["number"], card["password"], bday,
            card["expire"], 0, "J" if len(bday) == 6 else "S"))
    except Exception:  # noqa
        return False


# ---------- 상태 ----------
def _route_label(job):
    # GUI가 넣어준 라벨(열차 실제 출발시각 기준) 우선
    if job.get("label"):
        return job["label"]
    return f'{job.get("dep","?")}→{job.get("arr","?")} {job.get("date","")} {job.get("time","")[:4]}'


def _init_status(job):
    counts = {k: int(job.get(k, 0)) for k, _ in _PSG_TYPES}
    if _counts_total(counts) == 0:
        counts["adult"] = 1
    return {
        "state": "searching",
        "msg": "대기 중",
        "attempts": 0,
        "remaining": counts,          # 아직 예매 못한 인원
        "total": _counts_total(counts),
        "booked": [],                 # 확보한 예약 [{pnr, paid}]
        "route": _route_label(job),
        "ts": int(time.time()),
    }


def _record(rail, job, st, rsv, dec_key=None, dec_all=False):
    """예매 성공 처리: 잔여 차감 + 결제 + 기록."""
    paid = _pay(rail, job, rsv)
    pnr = getattr(rsv, "rsv_id", None) or str(rsv)
    st["booked"].append({"pnr": str(pnr), "paid": paid})
    if dec_all:
        for k, _ in _PSG_TYPES:
            st["remaining"][k] = 0
    elif dec_key:
        st["remaining"][dec_key] = max(0, int(st["remaining"].get(dec_key, 0)) - 1)


def _try_book(rail, job, st):
    """한 사이클: 조회 후 전원 묶음 → 실패 시 1명씩 분할 예매."""
    counts = st["remaining"]
    option = getattr(ReserveOption, job.get("option", "GENERAL_FIRST"),
                     ReserveOption.GENERAL_FIRST)
    trains = rail.search_train(
        job["dep"], job["arr"], date=job.get("date"), time=job.get("time"),
        passengers=_group_passengers(counts),
    )
    wanted = set(job.get("train_nos") or [])
    if wanted:
        trains = [t for t in trains if t.train_no in wanted]

    st["reason"] = None  # 이번 사이클 실패 사유(포맷된 msg와 분리 — 재귀 누적 방지)
    last_err = None
    for train in trains:
        # 1) 전원 묶음 예매(2명 이상, 아직 아무도 확보 못했을 때 우선 — 일행 함께)
        if _counts_total(counts) > 1:
            try:
                rsv = rail.reserve(train, passengers=_group_passengers(counts),
                                   option=option)
                if rsv:
                    _record(rail, job, st, rsv, dec_all=True)
                    return  # 전원 완료
            except SoldOutError:
                pass
            except Exception as e:  # noqa
                last_err = str(e)
        # 2) 1명씩 분할 — 이 열차에서 되는 만큼 확보
        for key, _cls in _PSG_TYPES:
            while int(counts.get(key, 0)) > 0:
                try:
                    rsv = rail.reserve(train, passengers=[_one_passenger(key)],
                                       option=option)
                    if not rsv:
                        break
                    _record(rail, job, st, rsv, dec_key=key)
                except SoldOutError:
                    break  # 이 열차 더이상 자리 없음 → 다음 열차
                except Exception as e:  # noqa
                    last_err = str(e)
                    break
        if _counts_total(counts) == 0:
            return
    st["reason"] = last_err  # 없으면 None → 메인 루프에서 '빈자리 없음'


def _login(creds):
    try:
        rail = Korail(creds["id"], creds["pass"], auto_login=True)
        return rail if rail.logined else None
    except Exception:  # noqa
        return None


def main():
    try:
        if os.path.exists(STOP):
            os.remove(STOP)
    except OSError:
        pass

    jobs = _load(JOBS, [])
    if not jobs:
        return
    rail = _login(jobs[0])
    if not rail:
        statuses = _load(JOBSTATUS, {})
        for job in jobs:
            statuses[job["jid"]] = {**_init_status(job), "state": "error",
                                    "msg": "로그인 실패 — 아이디/비밀번호 확인"}
        _save(JOBSTATUS, statuses)
        _notify(jobs[0], "korail+ 로그인 실패", "아이디/비밀번호를 확인하세요")
        return

    while not os.path.exists(STOP):
        jobs = _load(JOBS, [])               # 매 사이클 새로 읽음(추가/취소 반영)
        if not jobs:
            break
        statuses = _load(JOBSTATUS, {})
        if not rail.logined:
            rail = _login(jobs[0]) or rail

        any_active = False
        intervals = []
        for job in jobs:
            jid = job.get("jid")
            if not jid:
                continue
            intervals.append(float(job.get("interval", 3)))
            st = statuses.get(jid) or _init_status(job)
            if st["state"] in ("done", "error"):
                statuses[jid] = st
                continue
            any_active = True
            st["attempts"] = st.get("attempts", 0) + 1
            try:
                _try_book(rail, job, st)
                booked = len(st.get("booked", []))
                total = st.get("total", 1)
                if _counts_total(st["remaining"]) == 0:
                    st["state"] = "done"
                    st["msg"] = f"예매 완료 ({booked}건)"
                    pnrs = ", ".join(b["pnr"] for b in st["booked"])
                    paidn = sum(1 for b in st["booked"] if b.get("paid"))
                    tail = f" · 결제 {paidn}건" if paidn else ""
                    _notify(job, "🎉 korail+ 예매 성공",
                            f'{st["route"]}\n예약 {booked}건{tail}\n{pnrs}')
                else:
                    st["state"] = "partial" if booked else "searching"
                    reason = st.get("reason") or "빈자리 없음"
                    st["msg"] = (f'{st["attempts"]}회 시도 · 확보 {booked}/{total} · '
                                 f'{reason} — 재시도 중')
            except NoResultsError:
                st["msg"] = f'{st["attempts"]}회 시도 · 조회 결과 없음 — 재시도 중'
            except Exception as e:  # noqa
                st["msg"] = f'{st["attempts"]}회 시도 · 오류: {e}'
            st["ts"] = int(time.time())
            statuses[jid] = st

        # jobs.json 에서 사라진(취소된) 작업의 상태는 정리
        live_ids = {j.get("jid") for j in jobs}
        statuses = {k: v for k, v in statuses.items() if k in live_ids}
        _save(JOBSTATUS, statuses)

        if not any_active:
            break  # 모든 작업 완료/오류 → 서비스 종료(다음 추가 시 재시작)

        interval = min(intervals) if intervals else 3
        waited = 0.0
        while waited < interval and not os.path.exists(STOP):
            # 작업 목록이 비면(전체 취소) 즉시 깨어남
            if not _load(JOBS, []):
                break
            time.sleep(0.5)
            waited += 0.5

    _stop_self()


def _stop_self():
    """포그라운드 서비스 자체 종료(완료/중지 시). 다음 작업 추가 때 새로 시작됨."""
    try:
        from jnius import autoclass

        PythonService = autoclass("org.kivy.android.PythonService")
        PythonService.mService.stopSelf()
    except Exception:
        pass


if __name__ == "__main__":
    main()
