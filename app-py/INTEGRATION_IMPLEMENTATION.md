# Maize_Yield_API1 集成实现思路

## 核心思路总结

### 1. 架构设计：网关模式

**为什么用网关模式？**
- 保持前端API统一（都通过 app-py:8001）
- 统一错误处理和日志
- 统一任务管理
- 便于后续扩展

**网关职责**：
- 接收前端文件上传
- 文件格式转换和路径映射
- 调用Flask服务
- 结果处理和存储
- 返回统一格式响应

### 2. 输入适配：文件上传 → 目录路径

**问题**：前端上传12个文件，Flask服务需要目录路径

**解决方案**：
```
前端上传 → FastAPI接收 → 保存到临时目录 → 复制到目标目录 → 调用Flask服务
```

**关键步骤**：
1. 接收multipart/form-data上传
2. 保存到 `temp/maize_estimate/<timestamp>/`
3. 复制/重命名到 `Maize_Yield_API1/predict/data/input/data_dir_datian/`
4. 文件名映射（见INTEGRATION_PLAN.md）
5. 调用Flask服务时传递目录路径

### 3. 输出适配：GeoJSON → 统一格式

**问题**：Flask返回GeoJSON，需要统一格式

**解决方案**：
1. 读取Flask返回的GeoJSON文件
2. 复制到 `app-py/output/<task_id>/`
3. 生成 `task_info.json`（包含统计信息）
4. 可选：转换GeoJSON为CSV（便于前端表格展示）
5. 返回统一格式的JSON响应

### 4. 前端切换：动态UI

**实现方式**：
- 使用Vue的 `v-if` / `v-show` 根据算法选择显示不同表单
- 算法选择器：下拉框或Tab切换
- 表单字段：LSTM模式（12个文件），Maize_Yield_API1模式（12个文件 + Shapefile）

## 实现细节

### 后端实现要点

#### 1. 文件保存逻辑

```python
# 伪代码
def save_uploaded_files(files):
    temp_dir = create_temp_dir()
    
    # 文件映射字典
    file_mapping = {
        'climate_file': 'climate_data_even.npy',
        'params_file': 'param_values_corn.npy',
        # ... 其他文件
    }
    
    # 保存并重命名
    for upload_key, target_filename in file_mapping.items():
        uploaded_file = files[upload_key]
        target_path = Maize_Yield_API1_DIR / 'data/input/data_dir_datian' / target_filename
        save_file(uploaded_file, target_path)
    
    return target_dir
```

#### 2. Flask服务调用

```python
def call_flask_service(data_dir, shp_path):
    request_data = {
        "your_data_dir": str(data_dir),
        "model_data_dir": str(MODEL_DIR),
        "shp_input_path": str(shp_path),
        "geojson_output_path": str(OUTPUT_DIR / "prediction_results.geojson")
    }
    
    response = requests.post(
        f"http://127.0.0.1:8006/CropParamInversionService/param_inversion",
        json=request_data,
        timeout=3600
    )
    
    return response.json()
```

#### 3. 结果处理

```python
def process_flask_result(flask_response, task_id):
    # 1. 解析响应
    result = flask_response['result']
    output_path = result['output_path']  # Flask服务的输出路径
    static_info = json.loads(result['static_info'])
    
    # 2. 创建任务目录
    task_dir = APP_PY_OUTPUT_DIR / f"{task_id}_{timestamp}"
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. 复制GeoJSON文件
    geojson_src = Path(output_path) / "prediction_results.geojson"
    geojson_dst = task_dir / "prediction_results.geojson"
    shutil.copy(geojson_src, geojson_dst)
    
    # 4. 生成task_info.json
    task_info = {
        "task_id": task_id,
        "algorithm": "maize_estimate",
        "static_info": static_info,
        "output_path": str(task_dir),
        ...
    }
    save_json(task_info, task_dir / "task_info.json")
    
    # 5. 可选：转换GeoJSON为CSV
    convert_geojson_to_csv(geojson_dst, task_dir / "yield_predictions.csv")
    
    return task_info
```

### 前端实现要点

#### 1. 算法选择器

```vue
<template>
  <el-select v-model="selectedAlgorithm" @change="onAlgorithmChange">
    <el-option label="玉米产量预测（LSTM）" value="lstm" />
    <el-option label="玉米估产算法（Maize_Yield_API1）" value="maize_estimate" />
  </el-select>
</template>

<script setup>
const selectedAlgorithm = ref('lstm')

const onAlgorithmChange = (value) => {
  // 重置表单
  resetForm()
  // 根据算法加载不同的参数
  if (value === 'lstm') {
    loadLSTMParams()
  } else {
    loadMaizeEstimateParams()
  }
}
</script>
```

#### 2. 动态表单显示

```vue
<template>
  <!-- LSTM模式 -->
  <div v-if="selectedAlgorithm === 'lstm'">
    <!-- 现有的12个文件上传 -->
    <el-upload v-for="file in lstmFiles" ... />
  </div>
  
  <!-- Maize_Yield_API1模式 -->
  <div v-if="selectedAlgorithm === 'maize_estimate'">
    <!-- 12个文件上传 -->
    <el-upload v-for="file in estimateFiles" ... />
    <!-- Shapefile上传（新增） -->
    <el-upload 
      :file-list="shpFiles"
      accept=".shp,.shx,.dbf,.prj"
      multiple
      ...
    />
  </div>
</template>
```

#### 3. 提交处理

```javascript
const submitPrediction = async () => {
  if (selectedAlgorithm.value === 'lstm') {
    // 调用LSTM API
    await runMaizeYield(formData)
  } else {
    // 调用Maize_Yield_API1 API
    await runMaizeEstimate(formData)
  }
}
```

## 关键决策点

### 1. 文件存储策略

**选项A：直接覆盖**（推荐）
- 每次预测直接覆盖 `data_dir_datian/` 目录
- 优点：简单，不需要清理
- 缺点：并发请求会冲突

**选项B：任务隔离目录**
- 每次预测创建独立目录
- 优点：支持并发
- 缺点：需要清理旧目录

**选择**：先实现选项A，后续如需要并发再改

### 2. Shapefile处理

**选项A：使用默认文件**
- 不要求前端上传，使用 `小区.shp`
- 优点：简单
- 缺点：不够灵活

**选项B：支持上传**
- 前端可以上传自定义Shapefile
- 优点：灵活
- 缺点：需要处理多个文件（.shp/.shx/.dbf/.prj）

**选择**：先实现选项A，后续支持选项B

### 3. 结果格式统一

**选项A：只返回GeoJSON**
- 保持Flask服务的原始输出
- 优点：简单
- 缺点：前端需要处理GeoJSON

**选项B：同时提供CSV**
- 转换GeoJSON为CSV
- 优点：便于表格展示
- 缺点：需要转换逻辑

**选择**：实现选项B，提供两种格式

## 实现顺序

### 第一步：后端核心功能
1. 创建 `api/maize_estimate.py`
2. 实现文件上传和保存
3. 实现Flask服务调用
4. 实现结果处理

### 第二步：配置和工具
1. 创建 `core/maize_estimate_config.py`
2. 创建工具函数（文件映射、路径处理等）

### 第三步：任务管理
1. 创建 `api/maize_estimate_tasks.py`
2. 实现任务列表、详情、下载接口

### 第四步：前端集成
1. 创建 `api/maizeEstimate.js`
2. 修改 `production.vue` 添加算法切换
3. 实现动态表单

### 第五步：测试和优化
1. 单元测试
2. 集成测试
3. 性能优化

## 潜在问题和解决方案

### 问题1：文件路径冲突

**场景**：多个请求同时处理，都写入同一个目录

**解决**：
- 使用文件锁
- 或改为任务隔离目录

### 问题2：Flask服务不可用

**场景**：Flask服务未启动或崩溃

**解决**：
- 健康检查
- 友好的错误提示
- 重试机制（可选）

### 问题3：大文件处理

**场景**：上传的文件很大，处理时间长

**解决**：
- 异步处理（使用后台任务）
- 进度反馈
- 超时处理

### 问题4：GeoJSON转CSV

**场景**：需要将GeoJSON转换为CSV格式

**解决**：
- 使用geopandas读取GeoJSON
- 提取属性数据
- 保存为CSV

## 下一步行动

1. ✅ 创建集成方案文档（已完成）
2. ⏳ 实现后端API路由
3. ⏳ 实现配置文件
4. ⏳ 实现前端算法切换
5. ⏳ 测试和调试
