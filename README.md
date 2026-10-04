# korail+ : 코레일+(KTX) 예매 어시스턴트

> [!NOTE]
> 원본 [srtgo](https://github.com/lapis42/srtgo) → [srtgo_plus](https://github.com/junddao/srtgo_plus) 를 이어받아,
> **코레일+/코레일톡 7.0.8**(2026년 9월)의 로그인·조회·예매 요청 규격 변경과 anti-bot(DynaPath) 정책에
> 대응하도록 수정한 포크입니다.
>
> SRT는 코레일+로 통합되어 별도 노선 선택 없이 **코레일+(KTX) 창에서 통합 예매**합니다.

> [!WARNING]
> 본 프로그램의 모든 상업적·영리적 이용을 엄격히 금지합니다. 개인적인 승차권 예매 용도로만 사용해 주세요.
> 본 프로그램 사용에 따른 민·형사상 책임을 포함한 모든 책임은 사용자에게 있으며, 개발자는 어떠한 책임도
> 부담하지 않습니다. 본 프로그램을 내려받음으로써 위 사항에 동의하는 것으로 간주됩니다.

---

## 설치

### 일반 (시스템 Python)

```bash
pip install git+https://github.com/wkdusdmlqlc/korail_plus.git
```

### 가상환경 권장 (Kali/Ubuntu 등 PEP 668 적용 환경)

최신 데비안 계열은 시스템 Python에 직접 설치가 막혀 있어(`externally-managed-environment`) venv를 사용합니다.

```bash
git clone https://github.com/wkdusdmlqlc/korail_plus.git
cd korail_plus
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

이후 세션마다 `source .venv/bin/activate` 후 `srtgo` 실행.

### Linux/WSL 키체인 백엔드 (필요 시)

데스크톱 키링(gnome-keyring 등)이 없는 WSL/서버 환경에서는 `keyring` 백엔드가 없어
로그인 설정 저장 시 오류가 납니다. 파일 기반 백엔드를 설치하세요.

```bash
pip install keyrings.alt
# 마스터 비밀번호 없이 쓰려면 ~/.config/python_keyring/keyringrc.cfg 에 아래 추가:
#   [backend]
#   default-keyring=keyrings.alt.file.PlaintextKeyring
```

> [!CAUTION]
> `PlaintextKeyring`은 자격증명을 평문에 가깝게 파일로 저장합니다. **개인 기기에서만** 사용하세요.

## 사용법

```bash
srtgo
```

### 메뉴 구성

```
[?] 메뉴 선택:
  예매 시작
  예매 확인/결제/취소
  로그인 설정
  텔레그램 설정
  카드 설정
  역 설정
  역 직접 수정
  예매 옵션 설정
  나가기
```

### 1. 로그인 설정

처음 사용 시 **로그인 설정**에서 코레일+ 통합회원 계정을 등록합니다.

- 멤버십 번호 / 이메일 / 전화번호(하이픈 없이) 중 하나로 로그인
- 로그인 정보는 시스템 키체인(또는 설정한 keyring 백엔드)에 저장됩니다
- SRT 계정은 코레일+ 통합회원으로 통합되었습니다

### 2. 예매 시작

1. 출발역, 도착역, 날짜, 시간, 승객수 선택
2. 검색된 열차 목록에서 원하는 열차 선택 (복수 선택 가능)
3. 좌석 유형 선택 (일반실 우선 / 일반실만 / 특실 우선 / 특실만)
4. 매진 시 자동으로 빈 자리가 날 때까지 재시도

### 3. 텔레그램 알림 (선택)

1. [@BotFather](https://t.me/BotFather)에서 봇 생성 후 토큰 발급
2. **텔레그램 설정** 메뉴에서 토큰과 chat_id 입력

### 4. 카드 결제 (선택)

카드 정보를 미리 등록하면 예매와 동시에 자동 결제가 가능합니다.

## 요구사항

- Python 3.10 이상
- 의존 패키지: `click`, `curl_cffi`, `requests`, `inquirer`, `keyring`, `PyCryptodome`, `prompt_toolkit`, `python-telegram-bot`, `termcolor`

## 변경사항 (코레일+ 7.0.8 대응)

- **DynaPath 토큰(`x-dynapath-m-token`)**: SDK v1 → **v1.0.3** 알고리즘 반영 (sv, dynkey 접두사, base62 난수, rt 처리)
- **디바이스 ID**: 설치별 고유 android_id 생성·보관(`~/.config/srtgo/device_id`) — 공유 값 블록리스트 회피
- **API Version**: `250601002` → `250601003`
- **로그인**: 비밀번호 이중 Base64(내부 표준 + 외부 URL-safe) 인코딩, `checkValidPw`/`AppVersion`/`Key` 등 7.0.8 필드 반영, cphd 키 요청에 공통 파라미터 + 서비스 사전 체크 추가
- **조회(ScheduleView)**: `AppVersion`/`Key`/`qryDvCd` 필드 추가
- **예매(TicketReservation)**: `AppVersion` 및 역 편성/운행 순서 필드 추가
- **UI**: SRT 통합에 따라 노선 선택 제거(코레일+/KTX 고정)

## Credits

- 원본 프로젝트: [srtgo](https://github.com/lapis42/srtgo) by lapis42
- 상위 포크: [srtgo_plus](https://github.com/junddao/srtgo_plus)
- KTX 모듈: [korail2](https://github.com/carpedm20/korail2) by carpedm20 (BSD License)
- 7.0.8 규격 대조: [korail-mobile-api](https://github.com/yakisoba0728/korail-mobile-api), [pykorail](https://github.com/devgyurak/pykorail)
