@echo off
title AriaBot Launcher - Stellabiblia v4.2+
color 0A

echo ==========================
echo   Stellabiblia �N��������...
echo ==========================
echo.

echo ?? ���f���T�[�o�[�N�����iserver.py�j...
start cmd /k python server.py

timeout /t 5 >nul

echo ?? Aria�\���l�i�N�����ienglish_bot.py�j...
start cmd /k python english_bot.py

echo.
echo ? ���ׂĂ̍\���l�i�G���W�����N�����܂����B
echo   Discord��Aria�ɘb�������Ă݂Ă��������B
echo.
pause
