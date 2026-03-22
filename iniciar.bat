@echo off
cd /d "%~dp0"
title BOT DISCORD - Em execucao
color 0A

echo.
echo ============================================================
echo    BOT DISCORD - MODERACAO + ECONOMIA
echo    Desenvolvido por: MARKIZIN
echo ============================================================
echo.

:: Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Execute "instalar.bat" primeiro.
    pause
    exit /b 1
)

:: Verificar .env
if not exist .env (
    echo ERRO: Arquivo .env nao encontrado!
    echo Execute "instalar.bat" primeiro para configurar o token.
    pause
    exit /b 1
)

:: Verificar dependencias
python -c "import discord" >nul 2>&1
if %errorlevel% neq 0 (
    echo Dependencias nao instaladas. Instalando...
    python -m pip install -r requirements.txt
)

echo Iniciando o bot...
echo Para parar o bot, feche esta janela ou pressione Ctrl+C
echo.
echo ------------------------------------------------------------
echo.

:loop
python bot.py
echo.
echo ============================================================
echo    O bot parou de funcionar.
echo    Isso pode acontecer por token invalido, erro de conexao,
echo    ou problema no codigo.
echo ============================================================
echo.
set /p RESTART="Deseja reiniciar o bot? (S/N): "
if /i "%RESTART%"=="S" (
    echo.
    echo Reiniciando...
    echo.
    goto loop
)
pause
