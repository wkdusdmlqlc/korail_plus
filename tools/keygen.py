"""핫패치 서명용 Ed25519 키쌍 생성 (한 번만 실행).

- 개인키: ~/.config/korailplus/signing_key.pem  (절대 공개/커밋 금지, 당신만 보관)
- 공개키: korailplus/update_pubkey.txt           (저장소에 커밋 → APK에 번들됨)

실행:  python tools/keygen.py
이후 ktx.py를 고칠 때마다  python tools/sign_ktx.py  로 서명 후 커밋/푸시.
"""
import os
import stat

from Crypto.PublicKey import ECC

PRIV_DIR = os.path.join(os.path.expanduser("~"), ".config", "korailplus")
PRIV = os.path.join(PRIV_DIR, "signing_key.pem")
PUB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "korailplus", "update_pubkey.txt")


def main():
    if os.path.exists(PRIV):
        print(f"이미 개인키가 있습니다: {PRIV}")
        print("새로 만들면 기존 서명이 무효화됩니다. 덮어쓰려면 먼저 삭제하세요.")
        return
    os.makedirs(PRIV_DIR, exist_ok=True)
    key = ECC.generate(curve="Ed25519")
    with open(PRIV, "wt") as f:
        f.write(key.export_key(format="PEM"))
    os.chmod(PRIV, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    pub_pem = key.public_key().export_key(format="PEM")
    with open(PUB, "wt") as f:
        f.write(pub_pem + "\n")
    print(f"✅ 개인키 저장(비공개): {PRIV}  (권한 600)")
    print(f"✅ 공개키 저장(커밋): {PUB}")
    print("\n다음: git add korailplus/update_pubkey.txt && 커밋/푸시")
    print("그리고 ktx.py 변경 시마다: python tools/sign_ktx.py")


if __name__ == "__main__":
    main()
