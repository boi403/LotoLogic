@echo off
REM ============================================================
REM  lotologic-core - Atualizacao automatica do cache de loterias
REM ============================================================
REM
REM  Este script roda `sync all` em todas as 9 loterias da CAIXA
REM  e salva os resultados em ~/.lotologic-core/cache/*.json
REM
REM  USO MANUAL:
REM    sync_dados.bat
REM
REM  USO AUTOMATICO (Agendador de Tarefas do Windows):
REM    1. Win + R -> taskschd.msc
REM    2. "Criar Tarefa Basica..."
REM    3. Disparador: Diariamente, 22:00
REM    4. Acao: "Iniciar um programa"
REM       Programa/script: C:\Users\mateu\LotoLogic\lotologic-core\sync_dados.bat
REM    5. Salvar
REM
REM ============================================================

echo.
echo === Sincronizando dados das loterias da CAIXA ===
echo Inicio: %DATE% %TIME%
echo.

cd /d "%~dp0"
python -m lotologic_core.cli sync all
set EXITCODE=%ERRORLEVEL%

echo.
echo Fim: %DATE% %TIME%
echo Exit code: %EXITCODE%
echo.

REM Loga em arquivo (ultimas execucoes)
echo [%DATE% %TIME%] sync exit=%EXITCODE% >> sync_log.txt

exit /b %EXITCODE%
