' macro-dashboard 8001 HTTP 서버를 콘솔 창 없이 시작.
' .venv\Scripts\pythonw.exe로 wrapper _serve_http.py를 실행.

Dim shell, cmd
Set shell = CreateObject("Wscript.Shell")
cmd = """C:\Users\Hana_FI\claude code_ai\macro-dashboard\.venv\Scripts\pythonw.exe""" & _
      " """ & _
      "C:\Users\Hana_FI\claude code_ai\macro-dashboard\scripts\_serve_http.py" & _
      """"
shell.Run cmd, 0, False
