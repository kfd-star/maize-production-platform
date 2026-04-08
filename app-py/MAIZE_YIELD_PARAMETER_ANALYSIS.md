# 玉米产量预测（Production）参数配置流程分析

## 概述
本文档详细分析了玉米产量预测（Production）模块中参数的修改、保存和应用机制。

## 参数类型

玉米产量预测模块包含三类参数：

1. **模型配置参数** (`model_config_params`)
   - `FEATURE_DIM`: 特征维度（默认：35）
   - `HIDDEN_DIM`: 隐藏层维度（默认：64）
   - `NUM_LAYERS`: LSTM层数（默认：1）
   - `OUTPUT_DIM`: 输出维度（默认：1）
   - `DROPOUT`: Dropout率（默认：0.5）
   - `SEQ_LEN`: 序列长度（默认：365）
   - `BATCH_SIZE`: 批次大小（默认：32）

2. **归一化参数** (`normalization_params`)
   - `min_values`: 数据归一化最小值字典
   - `max_values`: 数据归一化最大值字典

3. **模型路径配置** (`config`)
   - `model_path`: 模型文件路径
   - `current_model`: 当前选择的模型文件名

## 参数存储机制

### 1. 后端存储（内存存储）

**文件位置**: `app-py/api/maize_yield.py`

```python
# 全局参数存储（内存中）
current_params = {
    "MaizeYield": MaizeYieldParameters()
}
```

**特点**：
- 参数存储在**内存**中，使用全局字典 `current_params`
- 服务重启后参数会丢失，恢复为默认值
- 支持部分更新：只更新提供的字段，保留其他字段的现有值

### 2. 默认值来源

**文件位置**: `app-py/utils/maize_yield/config.py`

```python
PREDICTION_CONFIGS = {
    'yield_prediction': {
        'MODEL': {
            'FEATURE_DIM': 35,
            'HIDDEN_DIM': 64,
            # ... 其他默认值
        },
        'PREPROCESSING': {
            'MIN_VALUES': {...},
            'MAX_VALUES': {...}
        }
    }
}
```

## 参数修改流程

### 前端 → 后端

#### 1. 前端保存参数

**文件位置**: `corn-system/src/router/algor/production.vue`

**保存模型参数**:
```javascript
const saveModelParams = async () => {
  const payload = {
    model_config_params: {
      FEATURE_DIM: modelParams.value.FEATURE_DIM,
      HIDDEN_DIM: modelParams.value.HIDDEN_DIM,
      // ... 其他参数
    }
  }
  await updateMaizeYieldParams(payload)  // 调用API
}
```

**保存归一化参数**:
```javascript
const saveNormalizationParams = async () => {
  const payload = {
    normalization_params: {
      min_values: normalizationParams.value.MIN_VALUES,
      max_values: normalizationParams.value.MAX_VALUES
    }
  }
  await updateMaizeYieldParams(payload)
}
```

**保存模型配置**:
```javascript
const saveConfig = async () => {
  config.value.model_path = `data/models/${config.value.current_model}`
  const payload = {
    config: {
      model_path: config.value.model_path,
      current_model: config.value.current_model
    }
  }
  await updateMaizeYieldParams(payload)
}
```

#### 2. API调用

**文件位置**: `corn-system/src/api/maizeYield.js`

```javascript
export const updateMaizeYieldParams = async (params) => {
  return http.put(`${API_BASE}/parameters/maize_yield`, params)
}
```

#### 3. 后端接收并存储

**文件位置**: `app-py/api/maize_yield.py`

```python
@router.put("/parameters/maize_yield", tags=["maize_yield"])
async def update_maize_yield_params(params: MaizeYieldParameters):
    current = current_params["MaizeYield"]
    
    # 只更新提供的字段，保留其他字段的现有值
    if params.model_config_params is not None:
        current.model_config_params = params.model_config_params
    if params.normalization_params is not None:
        current.normalization_params = params.normalization_params
    if params.config is not None:
        current.config = params.config
        
    return {"message": "参数更新成功"}
```

## 参数应用流程

### 预测时使用保存的参数

**文件位置**: `app-py/api/maize_yield.py` → `predict_maize_yield` 函数

```python
# 获取保存的配置参数
current = current_params["MaizeYield"]

# 使用保存的配置参数，如果没有则使用默认值
if current.model_config_params:
    model_config_dict = current.model_config_params.model_dump()
else:
    model_config_dict = None  # 使用默认值

if current.normalization_params:
    min_values_dict = current.normalization_params.min_values
    max_values_dict = current.normalization_params.max_values
else:
    min_values_dict = None  # 使用默认值
    max_values_dict = None

# 获取保存的模型路径
model_path = None
if current.config and current.config.model_path:
    model_path = current.config.model_path

# 执行预测，传递参数
result = run_maize_yield_prediction(
    # ... 文件路径参数
    model_config=model_config_dict,
    min_values=min_values_dict,
    max_values=max_values_dict,
    model_path=model_path
)
```

### 预测函数中的应用

**文件位置**: `app-py/utils/maize_yield/maize_yield_prediction.py`

```python
def run_maize_yield_prediction(
    # ... 文件路径参数
    model_config: dict = None,      # 传入的模型配置
    min_values: dict = None,        # 传入的归一化最小值
    max_values: dict = None,        # 传入的归一化最大值
    model_path: str = None          # 传入的模型路径
):
    # 基于默认配置构建本次运行的生效配置
    effective_model_cfg = deepcopy(DEFAULT_PREDICTION_CONFIGS['yield_prediction']['MODEL'])
    if model_config:
        # 合并传入的配置到默认配置
        for key, value in model_config.items():
            if key in effective_model_cfg:
                effective_model_cfg[key] = value

    effective_preproc = deepcopy(DEFAULT_PREDICTION_CONFIGS['yield_prediction']['PREPROCESSING'])
    if min_values:
        for key, value in min_values.items():
            if key in effective_preproc['MIN_VALUES']:
                effective_preproc['MIN_VALUES'][key] = value
    if max_values:
        for key, value in max_values.items():
            if key in effective_preproc['MAX_VALUES']:
                effective_preproc['MAX_VALUES'][key] = value
    
    # 使用生效的配置初始化模型和预处理器
    model = YieldPredictionModel(effective_model_cfg)
    
    if model_path:
        model.load_model(model_path)  # 使用指定的模型路径
    else:
        model.load_model(PATH_CONFIG['MODEL_PATH'])  # 使用默认路径
    
    preprocessor = YieldPreprocessor(effective_preproc)
    # ... 执行预测
```

## 参数获取流程

### 1. 获取当前参数

**前端**:
```javascript
const getCurrentModelParams = async () => {
  const res = await getMaizeYieldParams()
  if (res && res.data) {
    if (res.data.model_config) {
      modelParams.value = { ...modelParams.value, ...res.data.model_config }
    }
  }
}
```

**后端API**:
```python
@router.get("/parameters/maize_yield")
async def get_maize_yield_params():
    default_model_config = get_default_model_config()
    default_norm_params = get_default_normalization_params()
    default_config = MaizeYieldConfig()
    
    current = current_params["MaizeYield"]
    
    return {
        "model_config": current.model_config_params.model_dump() if current.model_config_params else default_model_config,
        "normalization_params": current.normalization_params.model_dump() if current.normalization_params else default_norm_params,
        "config": current.config.model_dump() if current.config else default_config.model_dump()
    }
```

### 2. 获取默认参数

**后端API**:
```python
@router.get("/parameters/maize_yield/defaults")
async def get_maize_yield_defaults():
    default_config = MaizeYieldConfig()
    return {
        "model_config": get_default_model_config(),
        "normalization_params": get_default_normalization_params(),
        "config": default_config.model_dump()
    }
```

## 关键特点

### 1. 内存存储
- 参数存储在内存中，服务重启后丢失
- 优点：简单快速，无需文件I/O
- 缺点：不持久化，服务重启后需重新配置

### 2. 部分更新机制
- 支持只更新部分参数，其他参数保持不变
- 前端可以分别保存不同类型的参数（模型参数、归一化参数、配置）

### 3. 默认值回退
- 如果未保存参数，自动使用默认值
- 默认值定义在 `config.py` 中

### 4. 参数合并策略
- 预测时，传入的参数会与默认配置合并
- 使用 `deepcopy` 避免污染默认配置

## 与SCYM和Maize_Yield_API1的对比

| 特性 | Production | SCYM | Maize_Yield_API1 |
|------|-----------|------|------------------|
| 存储方式 | 内存存储 | 文件存储（config.py） | 文件存储（config.py） |
| 持久化 | ❌ 不持久化 | ✅ 持久化 | ✅ 持久化 |
| 参数类型 | 3类（模型、归一化、配置） | 2类（系数、算法） | 1类（算法参数） |
| 更新方式 | 部分更新 | 文件正则替换 | 文件正则替换 |

## 改进建议

如果需要持久化参数，可以考虑：

1. **文件存储方案**（类似SCYM）:
   - 将参数保存到配置文件（如 `app-py/utils/maize_yield/user_config.py`）
   - 使用正则表达式更新配置文件
   - 服务重启后自动加载保存的参数

2. **数据库存储方案**:
   - 使用数据库存储用户配置
   - 支持多用户、多配置版本管理

3. **混合方案**:
   - 默认参数存储在配置文件中
   - 用户自定义参数存储在数据库或用户配置文件中
   - 运行时合并默认参数和用户参数
