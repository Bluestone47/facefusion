@echo off
call conda activate facefusion
python facefusion.py run --config-path=facefusion.local.ini
pause
