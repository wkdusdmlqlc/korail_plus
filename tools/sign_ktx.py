"""korailplus/ktx.py 를 Ed25519 개인키로 서명 → korailplus/ktx.py.sig 생성.

ktx.py를 수정할 때마다 실행한 뒤 ktx.py + ktx.py.sig 를 함께 커밋/푸시해야
앱(updater)이 핫패치를 수락한다. (서명 없으면 앱은 변경을 거부)

실행:  python tools/sign_ktx.py
"""
import base64
import os

from Crypto.PublicKey import ECC
from Crypto.Signature import eddsa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIV = os.path.join(os.path.expanduser("~"), ".config", "korailplus", "signing_key.pem")
KTX = os.path.join(ROOT, "korailplus", "ktx.py")
SIG = os.path.join(ROOT, "korailplus", "ktx.py.sig")


def main():
    if not os.path.exists(PRIV):
        print(f"개인키가 없습니다: {PRIV}\n먼저 python tools/keygen.py 실행")
        return
    with open(PRIV, "rt") as f:
        key = ECC.import_key(f.read())
    with open(KTX, "rb") as f:
        data = f.read()
    signer = eddsa.new(key, "rfc8032")
    sig = signer.sign(data)
    with open(SIG, "wt") as f:
        f.write(base64.b64encode(sig).decode("ascii") + "\n")
    print(f"✅ 서명 완료: {SIG}")
    print("git add korailplus/ktx.py korailplus/ktx.py.sig && 커밋/푸시")


if __name__ == "__main__":
    main()
