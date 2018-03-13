REM pyinstaller -F main.py
pyinstaller -F -w -i ./data./dtq.ico main.py
del main.spec
del *.pyc
del *.txt
rd /s /q build
copy dist/main.exe ./main.exe
rd /s /q dist
