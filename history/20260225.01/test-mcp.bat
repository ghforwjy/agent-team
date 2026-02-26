@echo off
chcp 65001 >nul
echo 测试 Evolver MCP Server...
echo.

cd /d "f:\mycode\垂直领域工具类\agent-team\evolver"

echo { "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {} } | node mcp-server.js

echo.
echo 测试完成！
pause
