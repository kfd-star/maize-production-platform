# 服务启动说明

## 服务架构

系统需要启动 **2个独立服务**：

1. **Flask 服务**（Maize_Yield_API1/predict）- 端口 **8006**
   - 提供玉米估产算法的核心计算服务
   - 独立运行，不依赖其他服务

2. **FastAPI 网关**（app-py）- 端口 **8001**
   - 提供统一的 API 接口
   - 接收前端请求，转发到 Flask 服务
   - 处理文件上传、任务管理等

## 启动步骤

### 1. 启动 Flask 服务（必须先启动）

```powershell
# 进入 Maize_Yield_API1/predict 目录
cd D:\kfd\corn-system-server-master-newest\corn-system-server-master\Maize_Yield_API1\predict

# 激活 Python 3.10 环境
conda activate py310

# 启动 Flask 服务
python server\app.py
```

**预期输出**：
```
============================================================
🌾 玉米估产服务启动
============================================================
服务名称: Maize_yield_estimation
运行地址: http://0.0.0.0:8006
============================================================
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8006
```

**验证服务**：
- 访问：http://127.0.0.1:8006/
- 应该返回服务信息 JSON

### 2. 启动 FastAPI 网关

**在新的命令行窗口**：

```powershell
# 进入 app-py 目录
cd D:\kfd\corn-system-server-master-newest\corn-system-server-master\app-py

# 激活 Python 环境（根据你的环境配置）
conda activate <你的环境名>

# 启动 FastAPI 服务
python main.py
```

**预期输出**：
```
🌽 启动 MaizeSM 数据同化服务...
📖 API文档: http://127.0.0.1:8001/docs
⚙️  参数配置: http://127.0.0.1:8001/parameters
🚀 服务启动中，请稍候...
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**验证服务**：
- 访问：http://127.0.0.1:8001/docs
- 应该看到 FastAPI 的 Swagger 文档页面

## 端口配置说明

### Flask 服务端口（8006）

**配置文件**：`Maize_Yield_API1/predict/server/config.py`

```python
self.PORT = 8006  # 可以修改
```

### FastAPI 网关端口（8001）

**配置文件**：`app-py/main.py`

```python
uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
```

**注意**：`app-py/utils/maize_yield/config.py` 中的 `SERVER_CONFIG.PORT = 8080` 是**历史遗留配置**，实际未被使用。

## 服务依赖关系

```
┌─────────────────┐
│   前端服务      │
│  (corn-system)  │
└────────┬────────┘
         │ HTTP请求
         ↓
┌─────────────────┐
│  FastAPI网关    │ ← 必须先启动
│  (app-py:8001)  │
└────────┬────────┘
         │ HTTP转发
         ↓
┌─────────────────┐
│  Flask服务      │ ← 必须先启动
│  (predict:8006) │
└─────────────────┘
```

## 启动顺序

**重要**：必须先启动 Flask 服务，再启动 FastAPI 网关

1. ✅ 启动 Flask 服务（8006）
2. ✅ 启动 FastAPI 网关（8001）
3. ✅ 启动前端服务（如果需要）

## 验证服务状态

### 检查 Flask 服务

```powershell
# 方法1：访问根路径
curl http://127.0.0.1:8006/

# 方法2：检查服务状态
curl http://127.0.0.1:8006/CropParamInversionService/status
```

### 检查 FastAPI 网关

```powershell
# 访问 API 文档
# 浏览器打开：http://127.0.0.1:8001/docs

# 或使用 curl
curl http://127.0.0.1:8001/
```

## 常见问题

### 1. 端口被占用

**错误**：`Address already in use`

**解决**：
- 检查端口占用：`netstat -ano | findstr :8006` 或 `netstat -ano | findstr :8001`
- 修改配置文件中的端口号
- 或关闭占用端口的进程

### 2. Flask 服务无法连接

**错误**：FastAPI 网关报错 "无法连接到 Flask 服务"

**解决**：
- 确认 Flask 服务已启动（检查 8006 端口）
- 检查防火墙设置
- 确认 Flask 服务配置的 HOST 是 `0.0.0.0`（不是 `127.0.0.1`）

### 3. Python 版本不匹配

**错误**：Flask 服务启动失败，DLL 加载错误

**解决**：
- 确保使用 Python 3.10 环境
- 参考 `Maize_Yield_API1/predict/SETUP_PYTHON310.md`

## 生产环境部署建议

### 使用进程管理器

**Windows**：
- 使用 `nssm`（Non-Sucking Service Manager）
- 或使用 Windows 服务

**Linux**：
- 使用 `systemd` 服务
- 或使用 `supervisor`

### 使用反向代理

建议使用 Nginx 作为反向代理：
- 前端 → Nginx → FastAPI (8001)
- FastAPI → Flask (8006)

这样可以：
- 统一端口（如 80/443）
- 负载均衡
- SSL 终止

## 快速启动脚本

### Windows 批处理脚本

创建 `start_services.bat`：

```batch
@echo off
echo 启动玉米估产系统服务...

echo.
echo [1/2] 启动 Flask 服务 (8006)...
start "Flask Service" cmd /k "cd /d D:\kfd\corn-system-server-master-newest\corn-system-server-master\Maize_Yield_API1\predict && conda activate py310 && python server\app.py"

timeout /t 3

echo.
echo [2/2] 启动 FastAPI 网关 (8001)...
start "FastAPI Gateway" cmd /k "cd /d D:\kfd\corn-system-server-master-newest\corn-system-server-master\app-py && conda activate <你的环境名> && python main.py"

echo.
echo 服务启动完成！
echo Flask 服务: http://127.0.0.1:8006
echo FastAPI 网关: http://127.0.0.1:8001/docs
pause
```

### PowerShell 脚本

创建 `start_services.ps1`：

```powershell
Write-Host "启动玉米估产系统服务..." -ForegroundColor Green

Write-Host "`n[1/2] 启动 Flask 服务 (8006)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\kfd\corn-system-server-master-newest\corn-system-server-master\Maize_Yield_API1\predict'; conda activate py310; python server\app.py"

Start-Sleep -Seconds 3

Write-Host "`n[2/2] 启动 FastAPI 网关 (8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\kfd\corn-system-server-master-newest\corn-system-server-master\app-py'; conda activate <你的环境名>; python main.py"

Write-Host "`n服务启动完成！" -ForegroundColor Green
Write-Host "Flask 服务: http://127.0.0.1:8006" -ForegroundColor Cyan
Write-Host "FastAPI 网关: http://127.0.0.1:8001/docs" -ForegroundColor Cyan
```

