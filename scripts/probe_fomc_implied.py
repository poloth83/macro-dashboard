# WIRP-style FOMC meeting-implied rate를 blpapi로 받을 수 있는지 probe하는 일회성 스크립트
"""
회사 PC에서 한 번 돌려서 어떤 field/security 조합이 통하는지 확인용.
결과를 기준으로 fetch_bloomberg 정식 통합 여부를 결정.

사용 (macro-dashboard 폴더에서):
  .venv/Scripts/python.exe scripts/probe_fomc_implied.py
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


KEYWORDS = ["FOMC", "WIRP", "MEETING_IMPLIED", "IMPLIED_FED", "FED_TARGET_PROB", "OIS_IMPLIED"]

CANDIDATE_SECURITIES = [
    "FDTR Index",        # Fed Funds Target Rate upper bound
    "FDTRMID Index",     # Fed Funds Target midpoint
    "FEDL01 Index",      # Effective Fed Funds Rate
    "USRINDEX Index",    # placeholder candidate
]

CANDIDATE_FIELDS = [
    # 정책금리 implied rate 후보 (단일 필드 — 다음 회의 1회분)
    "OIS_IMPLIED_FED_FUNDS_TGT_RATE",
    "IMPLIED_FED_FUNDS_TARGET_RATE",
    "FED_TARGET_RT_HIKE_PROB",
    "FED_TARGET_RT_CUT_PROB",
    # 회의 일정
    "NEXT_FOMC_MEETING_DATE",
    "ECO_FOMC_NEXT_MEETING_DT",
    # bulk 필드 후보 (회의별 시퀀스)
    "FED_MEETING_DATES",
    "IMPLIED_RATE_AT_FOMC_MEETING",
    "IMPLIED_RATE_FED_FUNDS_FUT",
    # WIRP screen 관련 추정 필드
    "WIRP_RATE_HIKE_PROB",
    "WIRP_PROBABILITY_HIKE",
    "WIRP_PROBABILITY_CUT",
    "PROBABILITY_RATE_HIKE",
    "PROBABILITY_RATE_CUT",
    # CBO 확률 관련
    "BLOOMBERG_PRBLTY_NXT_FOMC_INC_25BP",
    "BLOOMBERG_PRBLTY_NXT_FOMC_DEC_25BP",
    "BLOOMBERG_PRBLTY_NXT_FOMC_UNCHG",
]


def enumerate_fields_via_apiflds(session):
    """apiFLDS FieldSearchRequest로 키워드 포함 필드를 자동 발견."""
    print("\n=== Phase 1: apiFLDS FieldSearchRequest ===")
    if not session.openService("//blp/apiflds"):
        print("  ⚠ //blp/apiflds 서비스 오픈 실패")
        return []
    apiflds = session.getService("//blp/apiflds")

    discovered = []
    for kw in KEYWORDS:
        req = apiflds.createRequest("FieldSearchRequest")
        req.set("searchSpec", kw)
        # 결과를 reference data 쪽으로 제한
        try:
            include = req.getElement("include")
            if include.hasElement("fieldType"):
                include.setElement("fieldType", "All")
        except Exception:
            pass
        session.sendRequest(req)

        results_for_kw = []
        while True:
            ev = session.nextEvent(2000)
            for msg in ev:
                if not msg.hasElement("fieldData"):
                    continue
                arr = msg.getElement("fieldData")
                for i in range(arr.numValues()):
                    item = arr.getValue(i)
                    fid = item.getElementAsString("id") if item.hasElement("id") else ""
                    if not item.hasElement("fieldInfo"):
                        continue
                    info = item.getElement("fieldInfo")
                    mn = info.getElementAsString("mnemonic") if info.hasElement("mnemonic") else ""
                    desc = info.getElementAsString("description") if info.hasElement("description") else ""
                    cat = info.getElementAsString("categoryName") if info.hasElement("categoryName") else ""
                    ftype = info.getElementAsString("datatype") if info.hasElement("datatype") else ""
                    results_for_kw.append((mn, desc, cat, ftype, fid))
            import blpapi
            if ev.eventType() == blpapi.Event.RESPONSE:
                break

        print(f"\n  [{kw}] {len(results_for_kw)} fields")
        for mn, desc, cat, ftype, fid in results_for_kw[:30]:
            print(f"    {mn:42s}  ({ftype:10s}) {desc[:60]}")
        discovered.extend(m for m, *_ in results_for_kw)
    return sorted(set(discovered))


def try_reference_data(session, securities, fields):
    """주어진 (securities × fields) 조합으로 ReferenceDataRequest 시도."""
    print("\n=== Phase 2: ReferenceDataRequest probe ===")
    import blpapi
    if not session.openService("//blp/refdata"):
        print("  ⚠ //blp/refdata 서비스 오픈 실패")
        return
    refdata = session.getService("//blp/refdata")

    req = refdata.createRequest("ReferenceDataRequest")
    for s in securities:
        req.append("securities", s)
    for f in fields:
        req.append("fields", f)
    session.sendRequest(req)

    while True:
        ev = session.nextEvent(2000)
        for msg in ev:
            if not msg.hasElement("securityData"):
                continue
            arr = msg.getElement("securityData")
            for i in range(arr.numValues()):
                sd = arr.getValue(i)
                sec = sd.getElementAsString("security") if sd.hasElement("security") else "?"
                print(f"\n  --- {sec} ---")
                if sd.hasElement("securityError"):
                    err = sd.getElement("securityError")
                    msg_txt = err.getElementAsString("message") if err.hasElement("message") else "?"
                    print(f"    securityError: {msg_txt}")
                    continue
                fd = sd.getElement("fieldData")
                # 필드별로 있는지 확인
                for f in fields:
                    if fd.hasElement(f):
                        el = fd.getElement(f)
                        # bulk vs scalar 처리
                        try:
                            if el.isArray():
                                n = el.numValues()
                                print(f"    {f:42s} = BULK[{n}]")
                                for k in range(min(n, 5)):
                                    sub = el.getValue(k)
                                    parts = []
                                    try:
                                        for j in range(sub.numElements()):
                                            e = sub.getElement(j)
                                            parts.append(f"{e.name()}={e.getValueAsString()}")
                                    except Exception:
                                        parts.append(str(sub))
                                    print(f"      [{k}] {', '.join(parts)}")
                            else:
                                v = el.getValueAsString()
                                print(f"    {f:42s} = {v}")
                        except Exception as e:
                            print(f"    {f:42s} = (parse error: {e})")
                # 필드 에러
                if sd.hasElement("fieldExceptions"):
                    fe = sd.getElement("fieldExceptions")
                    if fe.numValues() > 0:
                        print(f"    (fieldExceptions: {fe.numValues()}건 — 일부 필드 인식 안 됨)")
                        for k in range(min(fe.numValues(), 5)):
                            ex = fe.getValue(k)
                            fid = ex.getElementAsString("fieldId") if ex.hasElement("fieldId") else "?"
                            err = ex.getElement("errorInfo") if ex.hasElement("errorInfo") else None
                            err_msg = err.getElementAsString("message") if err and err.hasElement("message") else "?"
                            print(f"      {fid}: {err_msg}")
        if ev.eventType() == blpapi.Event.RESPONSE:
            break


def main():
    print(f"[probe_fomc_implied] starting")
    import blpapi
    session = blpapi.Session()
    if not session.start():
        print("  ⚠ blpapi session 시작 실패 (Terminal 로그인 확인)")
        sys.exit(2)
    try:
        discovered = enumerate_fields_via_apiflds(session)
        print(f"\n  → Phase 1 발견된 유일 필드 수: {len(discovered)}")

        # Phase 2: 사전 후보 + 발견된 것 중 일부
        all_fields = list(dict.fromkeys(CANDIDATE_FIELDS + discovered[:60]))
        try_reference_data(session, CANDIDATE_SECURITIES, all_fields)
    finally:
        session.stop()
    print("\n[probe_fomc_implied] done")


if __name__ == "__main__":
    main()
