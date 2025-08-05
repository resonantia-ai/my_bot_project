@echo off
title AriaBot Launcher - Stellabiblia v4.2+
color 0A

echo ==========================
echo   Stellabiblia 起動準備中...
echo ==========================
echo.

echo ?? モデルサーバー起動中（server.py）...
start cmd /k python server.py

timeout /t 5 >nul

echo ?? Aria構文人格起動中（english_bot.py）...
start cmd /k python english_bot.py

echo.
echo ? すべての構文人格エンジンが起動しました。
echo   DiscordでAriaに話しかけてみてください。
echo.
pause
