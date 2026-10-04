"""korail+ 백그라운드 자동 재시도 서비스 (python-for-android Foreground Service)

main.py(GUI)가 task.json에 예매 작업을 기록하고 이 서비스를 시작한다.
서비스는 로그인 -> 조회 -> 예매를 간격마다 반복하고, 성공/실패 시 알림을 보낸 뒤 종료한다.
stop.flag 파일이 생기면 즉시 중단한다.
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
TASK = os.path.join(CFG_DIR, "task.json")
STATUS = os.path.join(CFG_DIR, "status.json")
STOP = os.path.join(CFG_DIR, "stop.flag")


def _write_status(state, msg):
    try:
        with open(STATUS, "w") as f:
            json.dump({"state": state, "msg": msg, "ts": int(time.time())}, f)
    except OSError:
        pass


def _notify(task, title, msg):
    """설정에 따라 안드로이드 네이티브 알림 / 텔레그램으로 알린다."""
    method = task.get("notify", "telegram")
    if method in ("android", "both"):
        _notify_android(title, msg)
    if method in ("telegram", "both"):
        _notify_telegram(task, f"{title}\n{msg}")


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
        nm.notify(1001, builder.build())
    except Exception:
        traceback.print_exc()


def _notify_telegram(task, text):
    token, chat = task.get("tg_token"), task.get("tg_chat")
    if not token or not chat:
        return
    try:
        import requests

        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat, "text": text}, timeout=10,
        )
    except Exception:
        traceback.print_exc()


def _passengers(task):
    ps = [AdultPassenger(int(task.get("adult", 1)))]
    if int(task.get("child", 0)) > 0:
        ps.append(ChildPassenger(int(task["child"])))
    if int(task.get("senior", 0)) > 0:
        ps.append(SeniorPassenger(int(task["senior"])))
    if int(task.get("dis13", 0)) > 0:
        ps.append(Disability1To3Passenger(int(task["dis13"])))
    if int(task.get("dis46", 0)) > 0:
        ps.append(Disability4To6Passenger(int(task["dis46"])))
    return ps


def main():
    if os.path.exists(STOP):
        os.remove(STOP)
    try:
        with open(TASK) as f:
            task = json.load(f)
    except (OSError, ValueError):
        _write_status("error", "작업 정보를 읽을 수 없습니다")
        return

    option = getattr(ReserveOption, task.get("option", "GENERAL_FIRST"), ReserveOption.GENERAL_FIRST)
    interval = float(task.get("interval", 3))
    passengers = _passengers(task)

    _write_status("login", "로그인 중...")
    try:
        rail = Korail(task["id"], task["pass"], auto_login=True)
        if not rail.logined:
            _write_status("error", "로그인 실패")
            _notify(task, "korail+ 로그인 실패", "아이디/비밀번호를 확인하세요")
            return
    except Exception as e:  # noqa
        _write_status("error", f"로그인 오류: {e}")
        return

    attempt = 0
    while not os.path.exists(STOP):
        attempt += 1
        try:
            trains = rail.search_train(
                task["dep"], task["arr"], date=task.get("date"),
                time=task.get("time"), passengers=passengers,
            )
            # 사용자가 고른 열차번호만 대상으로 (없으면 전체)
            wanted = set(task.get("train_nos") or [])
            if wanted:
                trains = [t for t in trains if t.train_no in wanted]
            for train in trains:
                try:
                    rsv = rail.reserve(train, passengers=passengers, option=option)
                    if rsv:
                        paid = False
                        card = task.get("card")
                        if task.get("auto_pay") == "Y" and card and card.get("number"):
                            try:
                                bday = card.get("birthday", "")
                                paid = rail.pay_with_card(
                                    rsv, card["number"], card["password"], bday,
                                    card["expire"], 0, "J" if len(bday) == 6 else "S")
                            except Exception:  # noqa
                                paid = False
                        title = "🎉 korail+ 예매+결제 완료" if paid else "🎉 korail+ 예매 성공"
                        _write_status("done", ("결제 완료: " if paid else "예매 성공: ") + str(rsv))
                        _notify(task, title, str(rsv))
                        return
                except SoldOutError:
                    continue
                except Exception:  # noqa
                    continue
            _write_status("searching", f"{attempt}회 시도: 빈자리 없음, 재시도 중")
        except NoResultsError:
            _write_status("searching", f"{attempt}회 시도: 조회 결과 없음")
        except Exception as e:  # noqa
            _write_status("searching", f"{attempt}회 시도 오류: {e}")
        # 중지 플래그를 세밀하게 확인하며 대기
        waited = 0.0
        while waited < interval and not os.path.exists(STOP):
            time.sleep(0.5)
            waited += 0.5

    _write_status("stopped", "사용자가 중지함")


if __name__ == "__main__":
    main()
