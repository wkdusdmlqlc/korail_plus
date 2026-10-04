# korail+ : 코레일+(KTX) 예매 어시스턴트

> [!NOTE]
> 원본 [srtgo](https://github.com/lapis42/srtgo) → [srtgo_plus](https://github.com/junddao/srtgo_plus)를 이어받아,
> **코레일+/코레일톡 7.0.8**(2026-09)의 로그인·조회·예매 요청 규격 변경과 anti-bot(DynaPath) 정책에
> 대응하도록 수정한 포크입니다. SRT는 코레일+로 통합되어 별도 노선 선택 없이 **코레일+(KTX)로 통합 예매**합니다.

> [!WARNING]
> 모든 상업적·영리적 이용을 엄격히 금지합니다. **개인 승차권 예매 용도로만** 사용하세요.
> 사용에 따른 민·형사상 책임을 포함한 모든 책임은 사용자에게 있으며, 개발자는 책임지지 않습니다.
> 내려받음으로써 위 사항에 동의하는 것으로 간주됩니다.

---

## 목차
- [실행 방법 선택](#실행-방법-선택)
- [방법 1. 안드로이드 APK (스마트폰 앱)](#방법-1-안드로이드-apk-스마트폰-앱)
- [방법 2. 안드로이드 Termux (폰에서 CLI)](#방법-2-안드로이드-termux-폰에서-cli)
- [방법 3. WSL / Linux (PC에서 CLI)](#방법-3-wsl--linux-pc에서-cli)
- [방법 4. pip 간편 설치](#방법-4-pip-간편-설치)
- [사용법](#사용법)
- [자동 업데이트(핫패치)](#자동-업데이트-핫패치)
- [보안](#보안)
- [소스에서 APK 빌드](#소스에서-apk-빌드)
- [변경사항](#변경사항-코레일-708-대응)

---

## 실행 방법 선택

| 목적 | 추천 방법 |
|------|-----------|
| 폰에 앱으로 설치, GUI + 백그라운드 자동 재시도 | **1. 안드로이드 APK** |
| 폰에서 간단히 CLI로 쓰고 싶음 (앱 설치 없이) | **2. Termux** |
| PC(윈도우 WSL/리눅스)에서 상시 실행·자동 재시도 | **3. WSL / Linux** |
| 그냥 빠르게 설치 | **4. pip** |

> 자동 재시도(매진→빈자리 재시도)를 **오래 돌리려면** 끄기 어려운 PC(방법 3)나
> 안드로이드 **포그라운드 서비스**(방법 1)가 유리합니다.

---

## 방법 1. 안드로이드 APK (스마트폰 앱)

GUI + **백그라운드 자동 재시도**(화면 꺼도 동작) + 안드로이드/텔레그램 알림.

### 설치
1. [릴리즈 페이지](https://github.com/wkdusdmlqlc/korail_plus/releases/latest)에서 `korailplus-*-debug.apk` 다운로드
2. 폰에서 APK 열기 → "출처를 알 수 없는 앱 설치 허용" 요청 시 허용
   - 설정 → 앱 → 특별한 앱 접근 → 알 수 없는 앱 설치 → (브라우저/파일앱) 허용
3. 설치 후 실행. Android 13+는 **알림 권한**을 허용해야 알림이 옵니다.

### 사용
1. 코레일+ 통합회원 아이디/비밀번호로 **로그인**
2. 출발·도착역, 날짜, 시간, 인원, 좌석 유형 선택 → **조회**
3. 결과에서:
   - **즉시 예매**: 해당 열차 바로 예매 시도
   - **재시도**: 그 열차를 매진 시에도 **백그라운드로 계속 재시도**
   - **전체 자동 재시도**: 조회된 모든 열차를 대상으로 재시도
4. **알림 설정**에서 텔레그램/안드로이드 알림 전환, 재시도 간격 조정

> ⚠️ 디버그 서명 APK라 Play Protect 경고가 뜰 수 있습니다(개인용 사이드로드). "무시하고 설치".

---

## 방법 2. 안드로이드 Termux (폰에서 CLI)

앱 포장 없이 폰에서 CLI를 직접 실행. [Termux](https://github.com/termux/termux-app)(F-Droid 권장) 설치 후:

```bash
pkg update && pkg upgrade -y
pkg install -y python git rust binutils          # rust/binutils는 일부 패키지 빌드용
pip install --upgrade pip wheel

git clone https://github.com/wkdusdmlqlc/korail_plus.git
cd korail_plus
pip install -e .
korailplus
```

- `curl_cffi` 빌드가 어려우면 생략해도 됩니다 — 코드가 자동으로 `requests`로 폴백합니다.
  (문제 시: `pip install -e . || pip install click requests inquirer keyring pycryptodome prompt_toolkit python-telegram-bot termcolor && pip install -e . --no-deps`)
- Termux는 백그라운드 유지가 OS에 따라 제한될 수 있으니, 장시간 자동 재시도는 방법 1(앱) 또는 방법 3(PC)을 권장합니다.

---

## 방법 3. WSL / Linux (PC에서 CLI)

PC에 상시 띄워 자동 재시도 + 텔레그램 알림으로 쓰기 좋습니다.

```bash
git clone https://github.com/wkdusdmlqlc/korail_plus.git
cd korail_plus
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
korailplus
```

최신 데비안/우분투/Kali는 시스템 파이썬 직접 설치가 막혀 있어(`externally-managed-environment`) **venv를 꼭 사용**하세요.

### 키체인(keyring) 백엔드 — WSL/서버 필수
데스크톱 키링(gnome-keyring)이 없으면 로그인 저장 시 `NoKeyringError`가 납니다. 파일 기반 백엔드 설치:

```bash
pip install keyrings.alt
mkdir -p ~/.config/python_keyring
cat > ~/.config/python_keyring/keyringrc.cfg <<'EOF'
[backend]
default-keyring=keyrings.alt.file.PlaintextKeyring
EOF
```

> [!CAUTION]
> `PlaintextKeyring`은 자격증명을 평문에 가깝게 저장합니다. **개인 기기에서만** 사용하세요.

---

## 방법 4. pip 간편 설치

```bash
pip install git+https://github.com/wkdusdmlqlc/korail_plus.git
korailplus
```
(PEP 668 환경이면 방법 3의 venv를 사용하세요.)

---

## 사용법

### CLI (방법 2·3·4)
```bash
korailplus          # 일반 실행
korailplus --debug  # 서버 응답 원문 출력(문제 진단용)
```

메뉴:
```
예매 시작          # 조회 → 열차 선택 → 좌석유형 → (매진 시) 자동 재시도
예매 확인/결제/취소
로그인 설정         # 코레일+ 통합회원 아이디/비밀번호 등록
텔레그램 설정       # 예매 성공 알림 봇
카드 설정           # 자동 결제용 카드(선택)
역 설정 / 역 직접 수정
예매 옵션 설정
```

- **아이디**: 멤버십번호 / 이메일 / 휴대폰(하이픈 없이) 중 하나
- **텔레그램 알림**: [@BotFather](https://t.me/BotFather)에서 봇 생성 → 토큰/chat_id 입력

### 앱 GUI (방법 1)
로그인 → 조회 → (즉시/재시도) → 진행 상태에서 중지. 알림 설정에서 텔레그램↔안드로이드 알림 전환.

---

## 자동 업데이트 (핫패치)

코레일이 앱을 바꾸면 보통 `ktx.py`(API 로직)만 영향을 받습니다. 이 프로젝트는 **재설치 없이**
GitHub 공개 저장소의 최신 `ktx.py`를 받아 자동 반영합니다.

- 앱/CLI 시작 시 **캐시/번들본을 즉시 로드**하고, **백그라운드로 최신본을 내려받아 다음 실행에 적용**(시작 지연·오프라인 안전)
- 받은 코드는 **Ed25519 서명 검증**을 통과해야만 적용됩니다(아래 보안 참고)
- 저장 위치: `~/.config/korailplus/hotpatch/ktx.py`

---

## 보안

- **공개 저장소 + 소유자만 쓰기** → 배포되는 코드가 누구에게나 공개되어 감사 가능하고, 몰래 변조 불가
- **핫패치 서명 검증** → 저장소/CDN이 변조돼도 **개인키 없는 코드는 앱이 거부**
  - 공개키는 앱에 번들(`korailplus/update_pubkey.txt`), 개인키는 소유자만 보관(`~/.config/korailplus/signing_key.pem`, 커밋 금지)
  - `ktx.py` 수정 시: `python tools/sign_ktx.py` 로 서명 후 `ktx.py` + `ktx.py.sig` 함께 커밋
- 권장: 저장소 소유자 계정 **2FA**, `main` 브랜치 보호(force-push 금지)

---

## 소스에서 APK 빌드

APK는 **GitHub Actions**가 자동 빌드합니다. 태그를 올리면 빌드 후 릴리즈에 첨부됩니다:

```bash
git tag v0.1.1 && git push origin v0.1.1
# → .github/workflows/build-apk.yml 가 빌드하여 Releases에 APK 업로드
```

로컬 빌드(리눅스, 오래 걸림):
```bash
pip install buildozer Cython
buildozer android debug     # bin/*.apk 생성
```
(Android SDK/NDK 자동 다운로드, JDK 17 필요. `buildozer.spec` 참고)

---

## 변경사항 (코레일+ 7.0.8 대응)

- **DynaPath 토큰(`x-dynapath-m-token`)**: SDK v1 → **v1.0.3** (sv·dynkey 접두사·base62 난수·rt 처리)
- **디바이스 ID**: 설치별 고유 생성·보관(`~/.config/korailplus/device_id`) — 공유 값 블록리스트 회피
- **API Version**: `250601002` → `250601003`
- **로그인**: 비밀번호 이중 Base64(내부 표준 + 외부 URL-safe), `checkValidPw`·`AppVersion`·`Key` 필드, cphd 키 요청에 공통 파라미터 + 서비스 사전 체크
- **조회(ScheduleView)**: `AppVersion`·`Key`·`qryDvCd` 추가
- **예매(TicketReservation)**: `AppVersion` + 역 편성/운행 순서 필드 추가
- **앱/자동화**: Kivy GUI, 백그라운드 자동 재시도(Foreground Service), 안드로이드/텔레그램 알림, 핫패치 자동 업데이트, SRT 선택 제거

---

## Credits
- 원본: [srtgo](https://github.com/lapis42/srtgo) by lapis42 · 상위 포크: [srtgo_plus](https://github.com/junddao/srtgo_plus)
- KTX 모듈: [korail2](https://github.com/carpedm20/korail2) by carpedm20 (BSD)
- 7.0.8 규격 대조: [korail-mobile-api](https://github.com/yakisoba0728/korail-mobile-api), [pykorail](https://github.com/devgyurak/pykorail)
- 폰트: [나눔고딕](https://hangeul.naver.com/font) (OFL)
