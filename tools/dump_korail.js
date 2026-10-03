/*
 * 코레일톡 7.0.8 값 덤프용 Frida 스크립트
 * 목적: AlienGuard로 암호화된 상수(Version/Key/Device)와 실제 로그인 요청 본문을
 *       평문으로 출력한다. 로그인 성공 불필요 — 요청을 "만들기만" 하면 캡처됨.
 *
 * 실행:
 *   frida -U -f com.korail.talk -l dump_korail.js         (spawn)
 *   또는 앱 실행 후:  frida -U -n 코레일 -l dump_korail.js  (attach)
 *
 * 앱이 뜨면 아이디/비번 아무거나 입력 후 "로그인"을 누르면 요청이 캡처된다.
 */
'use strict';

Java.perform(function () {
  console.log('[*] dump_korail loaded');

  // ---- 1) NetworkConstants 상수 덤프 (Version/BASE_URL) ----
  try {
    var NC = Java.use('com.korail.talk.common.NetworkConstants');
    var inst = NC.INSTANCE.value;
    console.log('[NC] VERSION   = ' + NC.getVERSION.call(inst));
    console.log('[NC] BASE_URL  = ' + NC.getBASE_URL.call(inst));
    console.log('[NC] COMMON    = ' + NC.getCOMMON_PARAMETER.call(inst));
  } catch (e) {
    console.log('[NC] err: ' + e);
  }

  // ---- 2) 모든 요청의 FieldMap 덤프 (STLidb: JsonElement -> Map<String,String>) ----
  // 난독화 메서드명이라 NetworkService의 Map 반환 메서드를 전수 후킹
  try {
    var NS = Java.use('com.korail.talk.network.NetworkService');
    var methods = NS.class.getDeclaredMethods();
    methods.forEach(function (m) {
      var name = m.getName();
      var ret = m.getReturnType().getName();
      if (ret === 'java.util.Map') {
        try {
          var overloads = NS[name].overloads;
          overloads.forEach(function (ov) {
            ov.implementation = function () {
              var r = ov.apply(this, arguments);
              try { console.log('[FieldMap:' + name + '] ' + JSON.stringify(mapToObj(r))); } catch (e) {}
              return r;
            };
          });
        } catch (e) {}
      }
    });
    console.log('[*] NetworkService Map hooks set');
  } catch (e) {
    console.log('[NS] err: ' + e);
  }

  // ---- 3) OkHttp 요청 직접 캡처 (URL + 폼 바디 + 헤더) ----
  try {
    var Interceptor = Java.use('okhttp3.Interceptor');
    // RealCall 레벨에서 최종 Request를 보기 위해 FormBody를 직접 읽는다
    var RealChain = Java.use('okhttp3.internal.http.RealInterceptorChain');
    RealChain.proceed.overload('okhttp3.Request').implementation = function (req) {
      try { dumpRequest(req); } catch (e) {}
      return this.proceed(req);
    };
    console.log('[*] OkHttp hook set');
  } catch (e) {
    console.log('[okhttp] err: ' + e);
  }

  // ---- 4) 비밀번호 암호화 확인 (AESCrypto.encrypt) ----
  try {
    var AES = Java.use('com.korail.talk.crypto.AESCrypto');
    AES.encrypt.overload('java.lang.String', 'java.lang.String').implementation = function (plain, key) {
      var out = this.encrypt(plain, key);
      console.log('[AES] key=' + key + ' plain=' + plain + ' -> ' + out);
      return out;
    };
  } catch (e) {
    console.log('[AES] err: ' + e);
  }

  function dumpRequest(req) {
    var url = req.url().toString();
    if (url.indexOf('letskorail') < 0) return; // 코레일 요청만
    console.log('\n==== REQUEST ' + req.method() + ' ' + url);
    var headers = req.headers();
    var hs = headers.size();
    for (var i = 0; i < hs; i++) {
      console.log('  H ' + headers.name(i) + ': ' + headers.value(i));
    }
    var body = req.body();
    if (body !== null) {
      var FormBody = Java.use('okhttp3.FormBody');
      if (FormBody.class.isInstance(body)) {
        var fb = Java.cast(body, FormBody);
        var n = fb.size();
        console.log('  -- form body (' + n + ') --');
        for (var j = 0; j < n; j++) {
          console.log('    ' + fb.name(j) + ' = ' + fb.value(j));
        }
      } else {
        console.log('  body class = ' + body.getClass().getName());
      }
    }
    console.log('====\n');
  }

  function mapToObj(m) {
    var o = {};
    var it = m.keySet().iterator();
    while (it.hasNext()) {
      var k = it.next();
      o['' + k] = '' + m.get(k);
    }
    return o;
  }
});
