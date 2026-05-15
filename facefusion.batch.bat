@echo off
call conda activate facefusion
python facefusion.py batch-run --config-path=facefusion.local.ini
pause
