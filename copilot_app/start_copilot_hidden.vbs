Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\himan\Downloads\HJAI\copilot_app"
WshShell.Run "python main.py", 0, False
