pyinstaller -F -w -i ./data./dtq.ico DTQ_USB_HS_HID.py
del DTQ_USB_HS_HID.spec
del *.pyc
rd /s /q build
copy dist/DTQ_USB_HS_HID.exe ./DTQ_USB_HS_HID.exe
rd /s /q dist
