# Maize_Yield_API1 集成方案

## 一、集成架构

```
前端 (corn-system)
    ↓ 选择算法：玉米估产算法 (Maize_Yield_API1)
    ↓ POST /api/maize_estimate (上传12个文件)
FastAPI网关 (app-py:8001)
    ↓ 保存文件到 Maize_Yield_API1/predict/data/input/data_dir_datian/
    ↓ POST http://127.0.0.1:8006/CropParamInversionService/param_inversion
Flask服务 (Maize_Yield_API1/predict:8006)
    ↓ 返回预测结果 (GeoJSON + 统计信息)
FastAPI网关 (app-py)
    ↓ 复制结果到 app-py/output/<task_id>/
    ↓ 返回给前端
前端 (corn-system)
```

## 二、核心差异分析

### 输入方式差异

| 项目 | LSTM算法（现有） | Maize_Yield_API1算法（新） |
|------|----------------|---------------------------|
| **输入方式** | 12个文件逐个上传 | 目录路径（包含所有.npy文件） |
| **API格式** | multipart/form-data | JSON（路径字符串） |
| **文件处理** | 临时目录 → JSON转换 | 直接使用.npy文件 |
| **Shapefile** | 不需要 | 必需（定义预测区域） |

### 输出差异

| 项目 | LSTM算法 | Maize_Yield_API1算法 |
|------|---------|---------------------|
| **输出格式** | CSV文件 | GeoJSON文件 |
| **统计信息** | 相同（mean/max/min/count） | 相同 |
| **空间信息** | 无 | 有（地理坐标） |

## 三、实现步骤

### 步骤1：创建后端API路由

**文件**：`app-py/api/maize_estimate.py`

**功能**：
1. 接收前端上传的12个.npy文件
2. 保存到 `Maize_Yield_API1/predict/data/input/data_dir_datian/`
3. 处理Shapefile（如果上传，或使用默认）
4. 调用Flask服务API
5. 处理返回结果，保存到 `app-py/output/<task_id>/`
6. 返回统一格式的响应

**关键接口**：
- `POST /api/maize_estimate` - 主预测接口
- `GET /api/maize_estimate/tasks` - 任务列表
- `GET /api/maize_estimate/tasks/{task_id}` - 任务详情
- `GET /api/maize_estimate/download/{task_id}` - 下载结果

### 步骤2：创建配置文件

**文件**：`app-py/core/maize_estimate_config.py`

**配置内容**：
- Flask服务地址（127.0.0.1:8006）
- Maize_Yield_API1路径映射
- 输入/输出目录路径

### 步骤3：前端算法切换

**文件**：`corn-system/src/router/algor/production.vue`

**功能**：
1. 顶部添加算法选择器（下拉框/切换按钮）
   - 选项1：玉米产量预测（LSTM）
   - 选项2：玉米估产算法（Maize_Yield_API1）
2. 根据选择的算法动态切换UI：
   - **LSTM模式**：显示12个文件上传框（现有UI）
   - **Maize_Yield_API1模式**：显示12个文件上传框 + Shapefile上传（新增）
3. 提交时调用对应的API：
   - LSTM → `/api/maize_yield`
   - Maize_Yield_API1 → `/api/maize_estimate`

### 步骤4：创建前端API封装

**文件**：`corn-system/src/api/maizeEstimate.js`

**功能**：
- 封装所有Maize_Yield_API1相关的API调用
- 与现有的 `maizeYield.js` 结构类似

## 四、数据流转详解

### 4.1 文件上传流程

```
前端上传12个.npy文件
    ↓
FastAPI接收 (multipart/form-data)
    ↓
保存到临时目录: temp/maize_estimate/<timestamp>/
    ↓
复制到目标目录: Maize_Yield_API1/predict/data/input/data_dir_datian/
    ↓
文件映射：
  climate_file → climate_data_even.npy
  params_file → param_values_corn.npy
  plant_doy_file → plant_DOY_even.npy
  n_fertilizer_file → sim_N_fertilizer_even.npy
  density_file → Density.npy
  soil_ad_file → Soil_AD.npy
  soil_bd_file → Soil_BD.npy
  soil_dul_file → Soil_DUL.npy
  soil_ll_file → Soil_LL.npy
  soil_ph_file → Soil_PH.npy
  soil_sat_file → Soil_Sat.npy
  soil_soc_file → Soil_SOC.npy
```

### 4.2 API调用流程

```python
# FastAPI网关调用Flask服务
request_data = {
    "your_data_dir": "Maize_Yield_API1/predict/data/input/data_dir_datian",
    "model_data_dir": "Maize_Yield_API1/predict/server/models",
    "shp_input_path": "Maize_Yield_API1/predict/data/input/shp/小区.shp",
    "geojson_output_path": "Maize_Yield_API1/predict/data/output/prediction_results.geojson"
}

response = requests.post(
    "http://127.0.0.1:8006/CropParamInversionService/param_inversion",
    json=request_data,
    timeout=3600
)
```

### 4.3 结果处理流程

```
Flask返回结果:
{
    "code": 200,
    "msg": "估产流程完成",
    "result": {
        "output_path": "Maize_Yield_API1/predict/data/output/task_xxx/",
        "static_info": {"mean": 392.20, "max": 583.23, ...}
    }
}
    ↓
FastAPI处理：
  1. 读取GeoJSON文件
  2. 创建任务目录: app-py/output/<task_id>/
  3. 复制GeoJSON到任务目录
  4. 生成task_info.json（包含统计信息）
  5. 可选：转换GeoJSON为CSV（便于前端展示）
    ↓
返回给前端:
{
    "code": 200,
    "msg": "估产完成",
    "result": {
        "output_path": "app-py/output/<task_id>/",
        "static_info": {...},
        "task_id": "<uuid>"
    }
}
```

## 五、文件映射关系

### 5.1 输入文件映射

| 前端上传字段 | 保存文件名 | 说明 |
|------------|----------|------|
| climate_file | climate_data_even.npy | 气候数据 |
| params_file | param_values_corn.npy | 作物参数 |
| plant_doy_file | plant_DOY_even.npy | 种植日期 |
| n_fertilizer_file | sim_N_fertilizer_even.npy | 氮肥施用 |
| density_file | Density.npy | 种植密度 |
| soil_ad_file | Soil_AD.npy | 土壤AD |
| soil_bd_file | Soil_BD.npy | 土壤BD |
| soil_dul_file | Soil_DUL.npy | 土壤DUL |
| soil_ll_file | Soil_LL.npy | 土壤LL |
| soil_ph_file | Soil_PH.npy | 土壤PH |
| soil_sat_file | Soil_Sat.npy | 土壤饱和度 |
| soil_soc_file | Soil_SOC.npy | 土壤有机碳 |

### 5.2 Shapefile处理

- **如果前端上传**：保存到 `Maize_Yield_API1/predict/data/input/shp/`，覆盖默认文件
- **如果未上传**：使用默认的 `小区.shp`

## 六、错误处理

### 6.1 Flask服务不可用

```python
try:
    response = requests.post(flask_url, json=data, timeout=3600)
except requests.exceptions.ConnectionError:
    return JSONResponse(
        status_code=503,
        content={"error": "Flask服务不可用，请确保服务已启动在8006端口"}
    )
```

### 6.2 文件路径不存在

- 检查 `Maize_Yield_API1` 目录是否存在
- 检查模型文件是否存在
- 检查输入目录是否可写

### 6.3 预测超时

- Flask服务默认超时3600秒（1小时）
- 如果超时，返回504错误

## 七、任务管理

### 7.1 任务存储结构

```
app-py/output/
  └── <task_id>_<timestamp>/
      ├── prediction_results.geojson  # 从Flask服务复制
      ├── task_info.json              # 任务元数据
      └── yield_predictions.csv       # 可选：从GeoJSON转换
```

### 7.2 task_info.json 结构

```json
{
    "task_id": "uuid",
    "algorithm": "maize_estimate",
    "created_at": "2026-01-12T15:30:00",
    "output_path": "app-py/output/<task_id>/",
    "flask_output_path": "Maize_Yield_API1/predict/data/output/task_xxx/",
    "static_info": {
        "mean": 392.20,
        "max": 583.23,
        "min": 200.15,
        "count": 8
    },
    "status": "completed",
    "input_files": {
        "climate_file": "...",
        ...
    }
}
```

## 八、实现优先级

### Phase 1: 核心功能（必须）
1. ✅ 创建 `api/maize_estimate.py` - 主预测接口
2. ✅ 创建 `core/maize_estimate_config.py` - 配置文件
3. ✅ 前端算法切换UI
4. ✅ 前端API封装

### Phase 2: 任务管理（重要）
5. ✅ 任务列表接口
6. ✅ 任务详情接口
7. ✅ 结果下载接口

### Phase 3: 增强功能（可选）
8. ⚠️ GeoJSON转CSV（便于表格展示）
9. ⚠️ 结果预览（地图可视化）
10. ⚠️ 参数持久化（保存配置）

## 九、测试要点

1. **Flask服务连接测试**
   - 确保Flask服务在8006端口运行
   - 测试健康检查接口

2. **文件上传测试**
   - 12个.npy文件上传
   - Shapefile上传（可选）
   - 文件大小限制（50MB）

3. **预测流程测试**
   - 完整预测流程
   - 结果文件生成
   - 统计信息正确性

4. **错误处理测试**
   - Flask服务不可用
   - 文件路径错误
   - 预测超时

5. **前端切换测试**
   - 算法切换UI
   - 表单动态变化
   - 结果展示

## 十、注意事项

1. **路径处理**
   - Windows路径分隔符处理
   - 相对路径转绝对路径
   - 路径存在性验证

2. **文件权限**
   - 确保有写入权限
   - 临时文件清理策略

3. **并发处理**
   - 多个请求同时处理
   - 文件冲突处理
   - 任务ID唯一性

4. **性能优化**
   - 大文件处理
   - 异步处理（可选）
   - 结果缓存（可选）
