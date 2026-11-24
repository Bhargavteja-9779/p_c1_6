@echo off
cd /d %~dp0\..
:loop
findstr /C:"FINISHED" state\agent_state.json >nul && exit /b 0
if exist state\STOP exit /b 0
echo %date% %time% starting agent >> logs\supervisor.log
claude -p "Read project/HANDOFF.md and project/MASTER_PROMPT.md, verify state with python scripts/status.py, then continue from NEXT ACTION. Do not restart finished work. Do not ask me questions." >> logs\agent_run.log 2>&1
timeout /t 900
goto loop
