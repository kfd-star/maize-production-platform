# GNAH_Maize_Yield 集成分析文档

## 一、项目结构分析

### GNAH_Maize_Yield 目录结构
```
GNAH_Maize_Yield/
├── server/
│   └── app.py              # Flask服务入口（端口5000）
├── client/
│   └── gnah_client.py      # 客户端调用脚本
├── core/
│   └── gnah_model.py       # GNAH算法核心（已加密）
├── config.py               # 配置文件
├── data/
│   ├── input/
│   │   ├── ERA5/           # ERA5气象栅格数据（.tif）
│   │   ├── MODIS_Ref/      # MODIS反射率数据（.tif）
│   │   ├── MODIS_PAR/      # MODIS光合有效辐射数据（.tif）
│   │   ├── Model_d1.enc    # GNAH模型文件1
│   │   └── Model_d2.joblib # GNAH模型文件2
│   └── output/             # 结果输出目录
└── run_GNAH.py             # 运行脚本
```

### 输入数据要求
- **ERA5目录**：包含多个.tif文件（气象栅格数据）
- **MODIS_Ref目录**：包含多个.tif文件（反射率数据）
- **MODIS_PAR目录**：包含多个.tif文件（光合有效辐射数据）
- **模型文件**：Model_d1.enc, Model_d2.joblib（已存在于data/input/）

### 输出结果
- **TIF文件**：`{prefix}_yield(kg_mu).tif` - 产量栅格数据
- **PNG文件**：`{prefix}_yield_render.png` - 渲染图像
- **JSON文件**：`{prefix}_result.json` - 结果统计信息

## 二、Flask服务API分析

### 1. 运行模型接口
```
POST /gnah/runModel
Content-Type: application/json

请求体：
{
  "output_prefix": "GNAH_Yield_Task1"  // 可选，输出文件前缀
}

响应：
{
  "code": 200,
  "msg": "succeed",
  "result": {
    "per_unit_yield": 1234.56,              // 平均产量（千克/亩）
    "output_time": "2026-01-16T20:00:00",
    "per_unit_yield_tif_file": "/path/to/file.tif",
    "per_unit_yield_rgb_png_file": "/path/to/file.png",
    "statistic": {
      "mean_yield_kg_mu": 1234.56
    },
    "output_json_path": "/path/to/result.json"
  }
}
```

### 2. 服务状态接口
```
GET /gnah/getStatus

响应：
{
  "code": 200,
  "msg": "succeed",
  "result": {
    "status": "running",
    "service": "GNAH Yield Estimation",
    "server_time": "2026-01-16T20:00:00",
    "output_dir": "/path/to/output"
  }
}
```

### 3. 文件列表接口
```
GET /gnah/listResultFiles

响应：
{
  "code": 200,
  "msg": "succeed",
  "result": {
    "tif_list": ["/path/to/file1.tif", ...],
    "png_list": ["/path/to/file1.png", ...]
  }
}
```

## 三、与 Maize_Yield_API1 的对比

| 特性 | Maize_Yield_API1 | GNAH_Maize_Yield |
|------|------------------|------------------|
| **服务端口** | 8006 | 5000 |
| **输入方式** | 12个.npy文件 + Shapefile | 3个目录（ERA5, MODIS_Ref, MODIS_PAR） |
| **输入格式** | .npy（NumPy数组） | .tif（栅格图像） |
| **输出格式** | GeoJSON + CSV | TIF + PNG + JSON |
| **模型文件** | .sav（scikit-learn） | .enc + .joblib（加密模型） |
| **API端点** | `/CropParamInversionService/param_inversion` | `/gnah/runModel` |
| **参数配置** | POPULATION_SIZE, MAX_GENERATIONS等 | output_prefix（输出前缀） |

## 四、集成方案设计

### 1. 后端集成架构

```
前端 (corn-system)
    ↓ 选择算法：玉米产量预测区域版（GNAH）
    ↓ POST /api/gnah (上传3个目录的.tif文件)
FastAPI网关 (app-py:8001)
    ↓ 保存文件到 GNAH_Maize_Yield/data/input/{ERA5|MODIS_Ref|MODIS_PAR}/
    ↓ POST http://127.0.0.1:5000/gnah/runModel
Flask服务 (GNAH_Maize_Yield:5000)
    ↓ 返回预测结果 (TIF + PNG + JSON)
FastAPI网关 (app-py)
    ↓ 复制结果到 app-py/output/<task_id>/
    ↓ 返回给前端
前端 (corn-system)
```

### 2. 文件上传处理

**问题**：前端需要上传3个目录的.tif文件，每个目录可能包含多个文件

**解决方案**：
- 使用 `webkitdirectory` 或拖拽上传，支持文件夹上传
- 前端按目录分类文件（ERA5、MODIS_Ref、MODIS_PAR）
- 后端保存到对应的输入目录

**文件分类逻辑**：
```javascript
// 前端根据文件名/路径判断目录
if (fileName.includes('ERA5') || fileName.includes('era5')) {
  // ERA5目录
} else if (fileName.includes('MODIS_Ref') || fileName.includes('modis_ref')) {
  // MODIS_Ref目录
} else if (fileName.includes('MODIS_PAR') || fileName.includes('modis_par')) {
  // MODIS_PAR目录
}
```

### 3. 配置参数

**可配置参数**（参考 `config.py`）：
- `output_prefix`: 输出文件前缀（默认："GNAH_Yield_Task1"）
- `MODEL_COEFFICIENTS`: 模型系数（cc4, factor_yield1, factor_yield2）- 可能需要从config.py读取

**参数存储**：
- 使用文件存储方式（类似SCYM），写入 `GNAH_Maize_Yield/config.py`
- 或使用内存存储（类似Production），但需要持久化

## 五、实现步骤

### 步骤1：创建后端配置文件
**文件**：`app-py/core/gnah_config.py`

**功能**：
- Flask服务连接配置（HOST: 127.0.0.1, PORT: 5000）
- 路径映射配置（GNAH项目路径、输入/输出目录）
- 配置验证函数
- 参数读取/更新函数（从config.py读取/更新）

### 步骤2：创建后端API路由
**文件**：`app-py/api/gnah.py`

**功能**：
1. `POST /api/gnah` - 主预测接口
   - 接收3个目录的文件上传（ERA5, MODIS_Ref, MODIS_PAR）
   - 保存到 `GNAH_Maize_Yield/data/input/{目录}/`
   - 调用Flask服务API
   - 处理返回结果，保存到 `app-py/output/<task_id>/`
   - 返回统一格式的响应

2. `GET /api/parameters/gnah` - 获取参数
3. `PUT /api/parameters/gnah` - 更新参数
4. `GET /api/parameters/gnah/defaults` - 获取默认参数

### 步骤3：创建任务管理路由
**文件**：`app-py/api/gnah_tasks.py`

**功能**：
- `GET /api/gnah/tasks` - 任务列表
- `GET /api/gnah/tasks/{task_id}` - 任务详情
- `DELETE /api/gnah/tasks/{task_id}` - 删除任务
- `GET /api/gnah/download/{task_id}` - 下载结果（支持tif/png/json）
- `GET /api/gnah/tasks/{task_id}/preview` - 预览结果（PNG图片）

### 步骤4：创建前端API封装
**文件**：`corn-system/src/api/gnah.js`

**功能**：
- 封装所有GNAH相关的API调用
- 与现有maizeEstimate.js结构一致

### 步骤5：创建前端页面组件
**文件**：`corn-system/src/router/algor/gnah.vue`

**功能**：
- 文件上传区域（3个目录：ERA5, MODIS_Ref, MODIS_PAR）
- 参数配置（output_prefix）
- 预测结果展示（TIF预览、PNG预览、统计信息）
- 任务历史管理
- 结果下载（TIF/PNG/JSON）

### 步骤6：注册路由和菜单
**文件**：
- `app-py/main.py` - 注册后端路由
- `corn-system/src/router/index.js` - 注册前端路由
- `corn-system/src/store/modeules/menuConfig.js` - 添加菜单项

## 六、关键技术点

### 1. 文件夹上传处理
- 前端使用 `webkitdirectory` 或拖拽上传
- 后端按目录分类保存文件
- 确保文件按正确目录结构保存

### 2. TIF文件预览
- 后端提供PNG预览接口（Flask已生成PNG）
- 前端显示PNG预览图
- 支持TIF文件下载

### 3. 任务隔离
- 每次预测创建独立的任务目录
- 避免文件冲突
- 支持任务删除和清理

### 4. 参数配置持久化
- 参考SCYM方式，使用文件存储
- 更新 `GNAH_Maize_Yield/config.py` 中的参数
- 支持参数读取和保存

## 七、注意事项

1. **Flask服务启动**：需要确保GNAH的Flask服务在5000端口运行
2. **模型文件**：Model_d1.enc 和 Model_d2.joblib 需要存在于 `data/input/` 目录
3. **文件数量**：每个目录可能包含大量.tif文件，需要注意文件大小和数量限制
4. **异步处理**：预测可能需要较长时间，需要支持异步任务和进度查询
5. **错误处理**：Flask服务可能返回错误，需要统一错误处理格式

## 八、参考实现

- **后端配置**：参考 `app-py/core/scym_config.py`
- **后端API**：参考 `app-py/api/maize_estimate.py`
- **任务管理**：参考 `app-py/api/maize_estimate_tasks.py`
- **前端页面**：参考 `corn-system/src/router/algor/maizeEstimate.vue`
- **前端API**：参考 `corn-system/src/api/maizeEstimate.js`
