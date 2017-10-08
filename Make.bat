pyinstaller -F -w -i ./data./dtq.ico DTQ_USB_COUNTER.py
del DTQ_USB_COUNTER.spec
del *.pyc
rd /s /q build
copy dist/DTQ_USB_COUNTER.exe ./DTQ_USB_COUNTER.exe
rd /s /q dist
