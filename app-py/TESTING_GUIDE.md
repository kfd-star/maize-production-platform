# Maize_Yield_API1 集成测试指南

## 测试前准备

### 1. 确保服务运行

**终端1 - Flask服务**：
```powershell
cd Maize_Yield_API1\predict
conda activate py310
python server\app.py
```

**终端2 - FastAPI网关**：
```powershell
cd app-py
conda activate <你的环境>
python main.py
```

### 2. 验证服务状态

**Flask服务**：
- 访问：http://127.0.0.1:8006/
- 应该返回JSON格式的服务信息

**FastAPI网关**：
- 访问：http://127.0.0.1:8001/docs
- 应该看到Swagger文档，包含 `/api/maize_estimate` 相关接口

## 测试步骤

### 测试1：API参数接口

**测试获取参数**：
```bash
curl http://127.0.0.1:8001/api/parameters/maize_estimate
```

**预期结果**：
- 返回模型配置和可用模型列表

### 测试2：文件夹路径方式

**前端操作**：
1. 访问：http://localhost:5173/#/home/maizeEstimate
2. 选择"文件夹路径"输入方式
3. 输入数据文件夹路径（例如：`D:\kfd\...\Maize_Yield_API1\predict\data\input\data_dir_datian`）
4. （可选）输入Shapefile文件夹路径
5. 点击"开始预测"

**预期结果**：
- 显示预测进度
- 返回统计信息（mean, max, min, count）
- 生成任务ID

### 测试3：文件上传方式

**前端操作**：
1. 选择"文件上传"输入方式
2. 逐个上传12个.npy文件
3. （可选）上传Shapefile文件
4. 点击"开始预测"

**预期结果**：
- 文件上传成功
- 预测完成
- 返回结果

### 测试4：任务管理

**测试任务列表**：
```bash
curl http://127.0.0.1:8001/api/maize_estimate/tasks
```

**预期结果**：
- 返回所有任务列表
- 包含任务ID、创建时间、统计信息

**测试任务详情**：
```bash
curl http://127.0.0.1:8001/api/maize_estimate/tasks/<task_id>
```

**预期结果**：
- 返回任务详细信息
- 包含输出路径、统计信息

### 测试5：结果下载

**前端操作**：
1. 在任务历史中点击"下载GeoJSON"或"下载CSV"
2. 验证文件下载

**预期结果**：
- 文件成功下载
- GeoJSON文件包含地理空间数据
- CSV文件包含表格数据

## 常见问题排查

### 问题1：Flask服务连接失败

**错误信息**：`无法连接到Flask服务`

**排查步骤**：
1. 检查Flask服务是否运行：`netstat -ano | findstr :8006`
2. 检查防火墙设置
3. 检查 `core/maize_estimate_config.py` 中的HOST和PORT配置

### 问题2：文件路径不存在

**错误信息**：`数据文件夹不存在`

**排查步骤**：
1. 验证路径是否正确
2. 检查路径中是否包含所有必需文件
3. 确保路径格式正确（Windows使用反斜杠或正斜杠）

### 问题3：模型文件不存在

**错误信息**：`模型文件不存在`

**排查步骤**：
1. 检查 `Maize_Yield_API1/predict/server/models/` 目录
2. 确认模型文件名是否正确
3. 检查 `core/maize_estimate_config.py` 中的模型路径配置

### 问题4：预测超时

**错误信息**：`Flask服务响应超时`

**排查步骤**：
1. 检查Flask服务日志
2. 增加超时时间（在配置中修改）
3. 检查数据文件大小

## 验证清单

- [ ] Flask服务正常运行（8006端口）
- [ ] FastAPI网关正常运行（8001端口）
- [ ] 前端页面可以访问
- [ ] 可以获取参数配置
- [ ] 文件夹路径方式可以提交预测
- [ ] 文件上传方式可以提交预测
- [ ] 预测结果正确返回
- [ ] 任务列表可以查看
- [ ] 任务详情可以查看
- [ ] 结果文件可以下载
- [ ] GeoJSON文件格式正确
- [ ] CSV文件格式正确（如果支持）

## 性能测试

### 测试并发请求

```bash
# 使用ab工具测试（需要安装Apache Bench）
ab -n 10 -c 2 -p request.json -T application/json http://127.0.0.1:8001/api/maize_estimate
```

**注意**：由于Flask服务可能不支持并发，建议顺序测试。

### 测试大文件处理

1. 使用较大的.npy文件（>10MB）
2. 验证上传和处理是否正常
3. 检查内存使用情况

## 日志查看

### Flask服务日志
- 位置：`Maize_Yield_API1/predict/server/server.log`
- 查看错误和警告信息

### FastAPI网关日志
- 控制台输出
- 检查请求和响应信息

## 下一步

如果所有测试通过，可以：
1. 部署到生产环境
2. 配置Nginx反向代理
3. 设置进程管理器（systemd/supervisor）
4. 配置日志轮转
5. 添加监控和告警
