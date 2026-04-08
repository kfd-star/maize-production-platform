from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
from utils.maize_yield.maize_yield_prediction import (
    run_maize_yield_prediction,
    get_default_model_config,
    get_default_normalization_params,
    get_required_files,
    get_file_descriptions
)
import json
from datetime import datetime
from fastapi.responses import JSONResponse

# 检查numpy是否可用
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ 警告: numpy未安装，将无法进行.npy到.json的转换")

router = APIRouter()

# 参数模型定义
class MaizeYieldModelConfig(BaseModel):
    FEATURE_DIM: int = Field(default=35, description="特征维度")
    HIDDEN_DIM: int = Field(default=64, description="隐藏层维度")
    NUM_LAYERS: int = Field(default=1, description="LSTM层数")
    OUTPUT_DIM: int = Field(default=1, description="输出维度")
    DROPOUT: float = Field(default=0.5, description="Dropout率")
    SEQ_LEN: int = Field(default=365, description="序列长度")
    BATCH_SIZE: int = Field(default=32, description="批次大小")

class MaizeYieldNormalizationParams(BaseModel):
    min_values: Dict[str, float] = Field(description="数据归一化最小值")
    max_values: Dict[str, float] = Field(description="数据归一化最大值")

class MaizeYieldConfig(BaseModel):
    model_path: str = Field(default="data/models/LSTM_1l_64_U_case_3I_Yield3.sav", description="模型文件路径")
    current_model: str = Field(default="LSTM_1l_64_U_case_3I_Yield3.sav", description="当前选择的模型文件名")

class MaizeYieldParameters(BaseModel):
    model_config_params: Optional[MaizeYieldModelConfig] = None
    normalization_params: Optional[MaizeYieldNormalizationParams] = None
    config: Optional[MaizeYieldConfig] = None

# 全局参数存储
current_params = {
    "MaizeYield": MaizeYieldParameters()
}

# 获取默认参数
@router.get("/parameters/maize_yield", tags=["maize_yield"])
async def get_maize_yield_params():
    """获取玉米产量预测的当前参数"""
    try:
        default_model_config = get_default_model_config()
        default_norm_params = get_default_normalization_params()
        default_config = MaizeYieldConfig()
        
        current = current_params["MaizeYield"]
        
        return {
            "model_config": current.model_config_params.model_dump() if current.model_config_params else default_model_config,
            "normalization_params": current.normalization_params.model_dump() if current.normalization_params else default_norm_params,
            "config": current.config.model_dump() if current.config else default_config.model_dump()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取参数失败: {str(e)}"}
        )

# 更新参数
@router.put("/parameters/maize_yield", tags=["maize_yield"])
async def update_maize_yield_params(params: MaizeYieldParameters):
    """更新玉米产量预测的参数"""
    try:
        current = current_params["MaizeYield"]
        
        # 只更新提供的字段，保留其他字段的现有值
        if params.model_config_params is not None:
            current.model_config_params = params.model_config_params
        if params.normalization_params is not None:
            current.normalization_params = params.normalization_params
        if params.config is not None:
            current.config = params.config
            
        return {"message": "参数更新成功"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"参数更新失败: {str(e)}"}
        )

# 获取默认参数
@router.get("/parameters/maize_yield/defaults", tags=["maize_yield"])
async def get_maize_yield_defaults():
    """获取玉米产量预测的默认参数"""
    try:
        default_config = MaizeYieldConfig()
        return {
            "model_config": get_default_model_config(),
            "normalization_params": get_default_normalization_params(),
            "config": default_config.model_dump()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取默认参数失败: {str(e)}"}
        )

# 获取必需文件列表
@router.get("/maize_yield/files", tags=["maize_yield"])
async def get_maize_yield_files():
    """获取玉米产量预测所需的文件列表"""
    try:
        required_files = get_required_files()
        file_descriptions = get_file_descriptions()
        
        files_info = []
        for file_key in required_files:
            files_info.append({
                "key": file_key,
                "description": file_descriptions.get(file_key, "未知文件"),
                "required": True
            })
        
        return {"files": files_info}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取文件列表失败: {str(e)}"}
        )

# 获取参数说明
@router.get("/maize_yield/descriptions", tags=["maize_yield"])
async def get_maize_yield_descriptions():
    """获取玉米产量预测参数的详细说明"""
    try:
        return {
            "model_config": {
                "FEATURE_DIM": "特征维度，输入数据的特征数量",
                "HIDDEN_DIM": "隐藏层维度，LSTM隐藏层的神经元数量",
                "NUM_LAYERS": "LSTM层数，网络深度",
                "OUTPUT_DIM": "输出维度，预测结果的维度",
                "DROPOUT": "Dropout率，防止过拟合",
                "SEQ_LEN": "序列长度，时间序列的窗口大小",
                "BATCH_SIZE": "批次大小，训练时的批次大小"
            },
            "normalization_params": {
                "min_values": "数据归一化最小值，用于特征标准化",
                "max_values": "数据归一化最大值，用于特征标准化"
            },
            "required_files": get_file_descriptions()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取参数说明失败: {str(e)}"}
        )

# 玉米产量预测主接口
@router.post("/maize_yield", tags=["maize_yield"])
async def predict_maize_yield(
    climate_file: UploadFile = File(..., description="气候数据文件"),
    params_file: UploadFile = File(..., description="作物参数文件"),
    plant_doy_file: UploadFile = File(..., description="种植日期文件"),
    n_fertilizer_file: UploadFile = File(..., description="氮肥施用文件"),
    density_file: UploadFile = File(..., description="种植密度文件"),
    soil_ad_file: UploadFile = File(..., description="土壤AD文件"),
    soil_bd_file: UploadFile = File(..., description="土壤BD文件"),
    soil_dul_file: UploadFile = File(..., description="土壤DUL文件"),
    soil_ll_file: UploadFile = File(..., description="土壤LL文件"),
    soil_ph_file: UploadFile = File(..., description="土壤PH文件"),
    soil_sat_file: UploadFile = File(..., description="土壤饱和度文件"),
    soil_soc_file: UploadFile = File(..., description="土壤有机碳文件")
):
    """玉米产量预测接口"""
    
    try:
        # 检查文件大小限制（50MB）
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        
        files_to_check = [
            ("气候数据文件", climate_file),
            ("作物参数文件", params_file),
            ("种植日期文件", plant_doy_file),
            ("氮肥施用文件", n_fertilizer_file),
            ("种植密度文件", density_file),
            ("土壤AD文件", soil_ad_file),
            ("土壤BD文件", soil_bd_file),
            ("土壤DUL文件", soil_dul_file),
            ("土壤LL文件", soil_ll_file),
            ("土壤PH文件", soil_ph_file),
            ("土壤饱和度文件", soil_sat_file),
            ("土壤有机碳文件", soil_soc_file)
        ]
        
        for file_desc, file in files_to_check:
            if file.size > MAX_FILE_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"error": f"{file_desc} ({file.filename}) 超过大小限制 50MB"}
                )
        
        # 创建临时目录保存上传的文件
        temp_base_dir = "temp/maize_yield"
        os.makedirs(temp_base_dir, exist_ok=True)
        temp_dir = os.path.join(temp_base_dir, f"temp_maize_yield_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存上传的文件
        files = {
            "climate_json_path": climate_file,
            "params_json_path": params_file,
            "plant_doy_json_path": plant_doy_file,
            "n_fertilizer_json_path": n_fertilizer_file,
            "density_json_path": density_file,
            "soil_ad_json_path": soil_ad_file,
            "soil_bd_json_path": soil_bd_file,
            "soil_dul_json_path": soil_dul_file,
            "soil_ll_json_path": soil_ll_file,
            "soil_ph_json_path": soil_ph_file,
            "soil_sat_json_path": soil_sat_file,
            "soil_soc_json_path": soil_soc_file
        }
        
        file_paths = {}
        for key, file in files.items():
            # 先保存为.npy文件
            npy_path = os.path.join(temp_dir, f"{key}.npy")
            with open(npy_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 转换为JSON格式
            json_path = os.path.join(temp_dir, f"{key}.json")
            if NUMPY_AVAILABLE:
                try:
                    arr = np.load(npy_path)
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(arr.tolist(), f, ensure_ascii=False)
                    file_paths[key] = json_path
                    print(f"✓ 成功转换 {file.filename} 为JSON格式")
                except Exception as e:
                    print(f"❌ 转换文件失败 ({file.filename}): {str(e)}")
                    # 如果转换失败，尝试直接使用.npy文件
                    file_paths[key] = npy_path
                    print(f"⚠️ 使用原始.npy文件: {npy_path}")
            else:
                # numpy不可用，直接使用.npy文件
                file_paths[key] = npy_path
                print(f"⚠️ numpy不可用，使用原始.npy文件: {npy_path}")
        
        # 获取保存的配置参数
        current = current_params["MaizeYield"]
        
        # 使用保存的配置参数，如果没有则使用默认值
        if current.model_config_params:
            model_config_dict = current.model_config_params.model_dump()
            print(f"使用保存的模型配置: {model_config_dict}")
        else:
            model_config_dict = None
            print("使用默认模型配置")
            
        if current.normalization_params:
            min_values_dict = current.normalization_params.min_values
            max_values_dict = current.normalization_params.max_values
            print(f"使用保存的归一化参数: min={min_values_dict}, max={max_values_dict}")
        else:
            min_values_dict = None
            max_values_dict = None
            print("使用默认归一化参数")
        
        # 获取保存的模型路径
        model_path = None
        if current.config and current.config.model_path:
            model_path = current.config.model_path
            print(f"使用保存的模型路径: {model_path}")
        else:
            print("使用默认模型路径")
        
        # 执行预测
        print(f"开始执行玉米产量预测...")
        print(f"文件路径: {file_paths}")
        result = run_maize_yield_prediction(
            climate_json_path=file_paths["climate_json_path"],
            params_json_path=file_paths["params_json_path"],
            plant_doy_json_path=file_paths["plant_doy_json_path"],
            n_fertilizer_json_path=file_paths["n_fertilizer_json_path"],
            density_json_path=file_paths["density_json_path"],
            soil_ad_json_path=file_paths["soil_ad_json_path"],
            soil_bd_json_path=file_paths["soil_bd_json_path"],
            soil_dul_json_path=file_paths["soil_dul_json_path"],
            soil_ll_json_path=file_paths["soil_ll_json_path"],
            soil_ph_json_path=file_paths["soil_ph_json_path"],
            soil_sat_json_path=file_paths["soil_sat_json_path"],
            soil_soc_json_path=file_paths["soil_soc_json_path"],
            model_config=model_config_dict,
            min_values=min_values_dict,
            max_values=max_values_dict,
            model_path=model_path
        )
        print(f"预测结果: {result}")
        
        # 不立即清理临时文件，保留到任务删除时一起清理
        # 临时文件路径已保存到task_info.json中，将在删除任务时清理
        
        if result["success"]:
            # 返回预测结果数据，包含task_id
            return result["data"]
        else:
            return JSONResponse(
                status_code=500,
                content={"error": result["error"]}
            )
            
    except Exception as e:
        # 发生错误时清理临时文件
        try:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir)
        except:
            pass
        
        return JSONResponse(
            status_code=500,
            content={"error": f"预测失败: {str(e)}"}
        )
