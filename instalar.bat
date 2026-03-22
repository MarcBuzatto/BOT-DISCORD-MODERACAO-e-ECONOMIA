@echo off
cd /d "%~dp0"
title BOT DISCORD - Instalador Automatico
color 0B

echo.
echo ============================================================
echo    BOT DISCORD - MODERACAO + ECONOMIA
echo    Instalador Automatico
echo    Desenvolvido por: MARKIZIN
echo ============================================================
echo.

:: ====== VERIFICAR PYTHON ======
echo [1/4] Verificando se o Python esta instalado...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo    ERRO: Python NAO encontrado!
    echo.
    echo    Voce precisa instalar o Python primeiro:
    echo    1. Acesse: https://www.python.org/downloads/
    echo    2. Baixe a versao mais recente
    echo    3. IMPORTANTE: Marque "Add Python to PATH"
    echo    4. Depois de instalar, rode este instalador novamente
    echo ============================================================
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo    Python encontrado: versao %PYVER%
echo.

:: ====== INSTALAR DEPENDENCIAS ======
echo [2/4] Instalando dependencias do bot...
echo    Isso pode levar alguns segundos...
echo.
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Falha ao instalar dependencias.
    echo Tente rodar manualmente: pip install -r requirements.txt
    pause
    exit /b 1
)
echo.
echo    Dependencias instaladas com sucesso!
echo.

:: ====== CONFIGURAR TOKEN ======
echo [3/4] Configurando o Token do Bot...
echo.

if exist .env (
    echo    Arquivo .env ja existe!
    set /p RECONFIG="   Deseja reconfigurar o token? (S/N): "
    if /i not "%RECONFIG%"=="S" goto :skip_token
)

echo ============================================================
echo    COMO OBTER O TOKEN DO BOT:
echo.
echo    1. Acesse: https://discord.com/developers/applications
echo    2. Clique em "New Application" ou selecione seu bot
echo    3. Va em "Bot" no menu lateral
echo    4. Clique em "Reset Token" e copie o token
echo.
echo    IMPORTANTE: Ative estas opcoes em "Bot":
echo       - MESSAGE CONTENT INTENT
echo       - SERVER MEMBERS INTENT
echo       - PRESENCE INTENT
echo.
echo    NUNCA compartilhe seu token com ninguem!
echo ============================================================
echo.
set /p BOT_TOKEN="   Cole seu token aqui e pressione ENTER: "

if "%BOT_TOKEN%"=="" (
    echo.
    echo    ERRO: Token nao pode estar vazio!
    echo    Execute o instalador novamente.
    pause
    exit /b 1
)

echo DISCORD_TOKEN=%BOT_TOKEN%> .env
echo.
echo    Token salvo com sucesso no arquivo .env!
echo.

:skip_token

:: ====== FINALIZAR ======
echo [4/4] Instalacao concluida!
echo.
echo ============================================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo.
echo    Para iniciar o bot:
echo      De duplo-clique em "iniciar.bat"
echo      Ou execute: python bot.py
echo.
echo    Para convidar o bot ao seu servidor:
echo      1. Acesse discord.com/developers/applications
echo      2. Seu bot - OAuth2 - URL Generator
echo      3. Marque: bot + applications.commands
echo      4. Permissoes: Administrator
echo      5. Copie o link e abra no navegador
echo.
echo    Desenvolvido por: MARKIZIN
echo ============================================================
echo.
set /p INICIAR="Deseja iniciar o bot agora? (S/N): "
if /i "%INICIAR%"=="S" (
    echo.
    echo Iniciando o bot...
    python bot.py
)
pause
