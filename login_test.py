"""DynaPath v1.0.3 패치 후 로그인 검증용 임시 스크립트.
실제 터미널에서 실행:  python login_test.py
아이디/비밀번호는 getpass로 입력받아 화면·로그에 남지 않습니다."""
import getpass
from srtgo.ktx import Korail

korail_id = input("코레일 아이디(멤버십번호/이메일/휴대폰): ").strip()
korail_pw = getpass.getpass("비밀번호: ")

k = Korail(korail_id, korail_pw, auto_login=False, verbose=True)
ok = k.login()
print("\n==== 결과 ====")
print("로그인 성공" if ok else "로그인 실패")
if ok:
    # 예약 조회까지 토큰 경로(DynaPath) 한 번 더 태움
    try:
        trains = k.search_train("서울", "부산")  # 역 "이름"으로 조회
        print(f"조회 성공: {len(trains)}개 열차")
    except Exception as e:
        print(f"조회 에러: {type(e).__name__}: {e}")
