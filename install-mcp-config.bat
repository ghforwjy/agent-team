@echo off
chcp 65001 >nul
echo 正在安装 Evolver MCP 配置到 Trae...

set "SOURCE=f:\mycode\垂直领域工具类\agent-team\trae-mcp-config.json"
set "TARGET=C:\Users\Administrator\AppData\Roaming\Trae CN\User\mcp_config.json"

copy /Y "%SOURCE%" "%TARGET%"

if %errorlevel% == 0 (
    echo ✅ 配置安装成功！
    echo 配置文件位置: %TARGET%
) else (
    echo ❌ 安装失败，请手动复制
    echo 源文件: %SOURCE%
    echo 目标: %TARGET%
)

pause
