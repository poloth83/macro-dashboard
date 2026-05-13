# pythonw.exe(콘솔 없음) 환경에서도 안전하게 동작하는 정적 HTTP 서버 wrapper
"""
pythonw로 호출되면 sys.stderr/stdout이 None이라 http.server.log_message가
AttributeError를 내고 빈 응답으로 connection을 끊는다. 그걸 막기 위해
stderr/stdout을 devnull로 미리 교체한 뒤 serve_forever를 띄운다.

호출 (작업 스케줄러 / 시작 폴더 vbs에서):
  pythonw.exe scripts\_serve_http.py
"""

from __future__ import annotations

import functools
import http.server
import os
import socketserver
import sys
from pathlib import Path

# pythonw 환경에서 sys.stderr/sys.stdout이 None이면 NullObject로 둠.
# 콘솔 python 환경에서는 그대로 두고 log가 정상 출력되도록 함.
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SERVE_DIR = ROOT / "output"
HOST = "0.0.0.0"
PORT = 8001


def main() -> int:
    if not SERVE_DIR.is_dir():
        return 1
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(SERVE_DIR),
    )
    with socketserver.ThreadingTCPServer((HOST, PORT), handler) as httpd:
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
