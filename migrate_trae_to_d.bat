@echo off
chcp 65001 >nul
echo ============================================
echo   Trae 数据目录迁移工具 (C盘 - D盘)
echo ============================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 需要管理员权限！
    echo 请右键此文件，选择"以管理员身份运行"。
    pause
    exit /b 1
)

:: 定义路径
set "SRC=%APPDATA%\TRAE SOLO CN"
set "DEST_ROOT=D:\TraeData"
set "DEST=%DEST_ROOT%\TRAE SOLO CN"

echo [信息] 源路径: %SRC%
echo [信息] 目标路径: %DEST%
echo.

:: 检查源目录是否存在
if not exist "%SRC%" (
    echo [错误] 未找到 Trae 数据目录: %SRC%
    echo 请确认 Trae 已安装并运行过至少一次。
    echo 也可以手动检查此路径是否存在。
    pause
    exit /b 1
)

:: 检查目标是否已存在
if exist "%DEST%" (
    echo [警告] 目标目录已存在: %DEST%
    echo 如果之前迁移过，请先删除该目录再运行。
    pause
    exit /b 1
)

:: 提醒关闭 Trae
echo [警告] 请确保 Trae 已完全退出！
echo 如果 Trae 仍在运行，迁移会失败。
echo.
set /p CONFIRM="确认 Trae 已退出？输入 Y 继续: "
if /i not "%CONFIRM%"=="Y" (
    echo 已取消。
    pause
    exit /b 0
)

:: 创建目标根目录
echo.
echo [步骤1] 创建目标目录...
if not exist "%DEST_ROOT%" mkdir "%DEST_ROOT%"

:: 移动数据
echo [步骤2] 移动 Trae 数据到 D 盘（可能需要几分钟）...
xcopy "%SRC%" "%DEST%\" /E /I /Y /Q
if %errorlevel% neq 0 (
    echo [错误] 复制失败！
    pause
    exit /b 1
)

:: 删除源目录
echo [步骤3] 删除 C 盘原目录...
rmdir /S /Q "%SRC%"
if exist "%SRC%" (
    echo [警告] 无法删除源目录，可能有进程占用。
    echo 请手动关闭 Trae 后重新运行。
    pause
    exit /b 1
)

:: 创建目录联接
echo [步骤4] 创建目录联接...
mklink /J "%SRC%" "%DEST%"
if %errorlevel% neq 0 (
    echo [错误] 创建联接失败！
    echo 正在恢复源目录...
    move "%DEST%" "%SRC%"
    pause
    exit /b 1
)

echo.
echo ============================================
echo   迁移成功！
echo ============================================
echo.
echo Trae 数据已从 C 盘迁移到: %DEST%
echo C 盘的链接指向 D 盘，Trae 会正常工作。
echo.
echo 现在可以启动 Trae 了。
echo.
pause
