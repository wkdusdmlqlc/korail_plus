package org.korailplus;

import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;

import java.security.KeyStore;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/**
 * Android Keystore 기반 AES-256/GCM 암복호화 헬퍼.
 *
 * pyjnius에서 KeyGenParameterSpec.Builder.setBlockModes(String[]) 등 배열 인자를
 * 마셜링할 때 네이티브 abort(앱 강제 종료, try/except로 못 막음)가 발생했다.
 * 모든 Keystore/Cipher 로직을 Java로 옮겨 파이썬은 encrypt/decrypt 두 메서드만
 * 호출하도록 한다 → JNI 레벨에서 안전.
 *
 * 저장 포맷: base64( ivLen(1byte) | iv | ciphertext )
 * 실패 시 null 반환 → 파이썬에서 평문 폴백.
 */
public final class SecureStore {
    private static final String ALIAS = "korailplus_secret_v1";
    private static final String TRANSFORM = "AES/GCM/NoPadding";
    private static final int GCM_TAG_BITS = 128;

    private SecureStore() {}

    private static SecretKey getOrCreateKey() throws Exception {
        KeyStore ks = KeyStore.getInstance("AndroidKeyStore");
        ks.load(null);
        KeyStore.Entry entry = ks.getEntry(ALIAS, null);
        if (entry instanceof KeyStore.SecretKeyEntry) {
            return ((KeyStore.SecretKeyEntry) entry).getSecretKey();
        }
        KeyGenerator kg = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        KeyGenParameterSpec spec = new KeyGenParameterSpec.Builder(
                ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build();
        kg.init(spec);
        return kg.generateKey();
    }

    /** 평문 -> base64(ivLen|iv|ct). 실패 시 null. */
    public static String encrypt(String plain) {
        if (plain == null) {
            return null;
        }
        try {
            Cipher c = Cipher.getInstance(TRANSFORM);
            c.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
            byte[] iv = c.getIV();
            byte[] ct = c.doFinal(plain.getBytes("UTF-8"));
            byte[] out = new byte[1 + iv.length + ct.length];
            out[0] = (byte) iv.length;
            System.arraycopy(iv, 0, out, 1, iv.length);
            System.arraycopy(ct, 0, out, 1 + iv.length, ct.length);
            return android.util.Base64.encodeToString(out, android.util.Base64.NO_WRAP);
        } catch (Throwable t) {
            return null;
        }
    }

    /** base64(ivLen|iv|ct) -> 평문. 실패 시 null. */
    public static String decrypt(String b64) {
        if (b64 == null) {
            return null;
        }
        try {
            byte[] raw = android.util.Base64.decode(b64, android.util.Base64.NO_WRAP);
            int ivLen = raw[0] & 0xFF;
            byte[] iv = new byte[ivLen];
            System.arraycopy(raw, 1, iv, 0, ivLen);
            byte[] ct = new byte[raw.length - 1 - ivLen];
            System.arraycopy(raw, 1 + ivLen, ct, 0, ct.length);
            Cipher c = Cipher.getInstance(TRANSFORM);
            c.init(Cipher.DECRYPT_MODE, getOrCreateKey(), new GCMParameterSpec(GCM_TAG_BITS, iv));
            return new String(c.doFinal(ct), "UTF-8");
        } catch (Throwable t) {
            return null;
        }
    }
}
