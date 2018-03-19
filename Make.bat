pyinstaller -F -w -i ./data./dtq.ico DTQ_USB_HID.py
del DTQ_USB_HID.spec
del *.pyc
del *.txt
rd /s /q build
copy dist/DTQ_USB_HID.exe ./DTQ_USB_HID.exe
rd /s /q dist
