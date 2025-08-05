@echo off
echo 🔃 Starting LLM + Discord Bot...

call start_server.bat
timeout /t 5 >nul
call start_discord_bot.bat

echo ✅ All systems launched!
pause
