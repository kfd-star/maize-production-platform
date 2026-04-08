from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import os
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

router = APIRouter()

# FSPM参数模型
class FSPMParameters(BaseModel):
    cultivar: str = Field(default="JK968", description="玉米品种")
    density: int = Field(default=4000, description="种植密度")
    row_distance: int = Field(default=60, description="行距")
    num_rows: int = Field(default=2, description="行数")
    plants_per_row: int = Field(default=3, description="每行株数")
    plant_azimuth_range: int = Field(default=15, description="植物方位角范围")
    roi_num_plants: int = Field(default=4, description="ROI植物数量")
    date_planting: str = Field(default="2021/06/26", description="种植日期")
    date_start: str = Field(default="2021/06/30", description="开始日期")
    date_end: str = Field(default="2021/09/01", description="结束日期")
    longitude: float = Field(default=116.3, description="经度")
    latitude: float = Field(default=39.5, description="纬度")
    double_side_facet: bool = Field(default=False, description="双面刻面")
    canopy_recon_mode: str = Field(default="True", description="冠层重建模式")
    use_measured_heights: str = Field(default="False", description="使用测量高度")

# 参数配置文件路径 - 直接使用FSPM的paras.json文件
import os
# 使用绝对路径，确保无论从哪里运行都能找到文件
# PARAMS_FILE = r"D:\kfd\corn-system-server-master-newest\corn-system-server-master\FSPM_Corn_Growth\dmb_API\000\config\paras.json"
# 使用相对路径，基于当前文件位置构建路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARAMS_FILE = os.path.join(BASE_DIR, "FSPM_Corn_Growth", "dmb_API", "000", "config", "paras.json")
print(f"FSPM参数文件路径: {PARAMS_FILE}")
print(f"文件是否存在: {os.path.exists(PARAMS_FILE)}")

# 默认参数
DEFAULT_PARAMS = {
    "cultivar": "JK968",
    "density": 4000,
    "row_distance": 60,
    "num_rows": 2,
    "plants_per_row": 3,
    "plant_azimuth_range": 15,
    "roi_num_plants": 4,
    "date_planting": "2021/06/26",
    "date_start": "2021/06/30",
    "date_end": "2021/09/01",
    "longitude": 116.3,
    "latitude": 39.5,
    "double_side_facet": False,
    "canopy_recon_mode": "True",
    "use_measured_heights": "False"
}

# 参数验证规则
PARAM_VALIDATION = {
    "cultivar": {
        "type": "select",
        "options": ["JK968", "JNK728", "JMC01", "J2416", "DE1", "J724"],
        "description": "玉米品种选择，影响植物形态和生理参数"
    },
    "density": {
        "type": "number",
        "min": 1000,
        "max": 10000,
        "step": 100,
        "description": "种植密度，单位：株/公顷"
    },
    "row_distance": {
        "type": "number",
        "min": 30,
        "max": 100,
        "step": 5,
        "description": "行距，单位：厘米"
    },
    "num_rows": {
        "type": "number",
        "min": 1,
        "max": 10,
        "step": 1,
        "description": "种植行数"
    },
    "plants_per_row": {
        "type": "number",
        "min": 1,
        "max": 20,
        "step": 1,
        "description": "每行株数"
    },
    "plant_azimuth_range": {
        "type": "number",
        "min": 0,
        "max": 90,
        "step": 5,
        "description": "植物方位角范围，单位：度"
    },
    "roi_num_plants": {
        "type": "number",
        "min": 1,
        "max": 20,
        "step": 1,
        "description": "感兴趣区域植物数量"
    },
    "date_planting": {
        "type": "date",
        "format": "YYYY/MM/DD",
        "description": "种植日期"
    },
    "date_start": {
        "type": "date",
        "format": "YYYY/MM/DD",
        "description": "模拟开始日期"
    },
    "date_end": {
        "type": "date",
        "format": "YYYY/MM/DD",
        "description": "模拟结束日期"
    },
    "longitude": {
        "type": "number",
        "min": 70,
        "max": 140,
        "step": 0.1,
        "description": "经度，单位：度"
    },
    "latitude": {
        "type": "number",
        "min": 15,
        "max": 55,
        "step": 0.1,
        "description": "纬度，单位：度"
    },
    "double_side_facet": {
        "type": "boolean",
        "description": "是否使用双面刻面"
    },
    "canopy_recon_mode": {
        "type": "select",
        "options": ["True", "False"],
        "description": "冠层重建模式"
    },
    "use_measured_heights": {
        "type": "select",
        "options": ["True", "False"],
        "description": "是否使用测量高度"
    }
}

def _load_parameters() -> Dict[str, Any]:
    """加载参数配置"""
    if os.path.exists(PARAMS_FILE):
        try:
            with open(PARAMS_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
                # 只返回参数部分，过滤掉文件路径
                params = {}
                for key in DEFAULT_PARAMS.keys():
                    if key in all_data:
                        params[key] = all_data[key]
                    else:
                        params[key] = DEFAULT_PARAMS[key]
                return params
        except Exception as e:
            print(f"加载FSPM参数失败: {e}")
    
    return DEFAULT_PARAMS.copy()

def _save_parameters(params: Dict[str, Any]) -> bool:
    """保存参数配置"""
    try:
        print(f"_save_parameters 被调用，参数: {params}")
        print(f"目标文件路径: {os.path.abspath(PARAMS_FILE)}")
        
        # 读取现有文件，保留文件路径
        existing_data = {}
        if os.path.exists(PARAMS_FILE):
            try:
                with open(PARAMS_FILE, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                print(f"读取现有文件成功，包含 {len(existing_data)} 个字段")
            except Exception as e:
                print(f"读取现有参数文件失败: {e}")
        else:
            print("文件不存在，将创建新文件")
        
        # 只更新参数部分，保留文件路径
        updated_count = 0
        for key, value in params.items():
            if key in existing_data and existing_data[key] != value:
                print(f"更新字段 {key}: {existing_data[key]} -> {value}")
                updated_count += 1
            elif key not in existing_data:
                print(f"添加新字段 {key}: {value}")
                updated_count += 1
            existing_data[key] = value
        
        print(f"总共更新了 {updated_count} 个字段")
        
        # 保存更新后的文件
        with open(PARAMS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
        print("文件保存成功")
        return True
    except Exception as e:
        print(f"保存FSPM参数失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def _validate_parameters(params: Dict[str, Any]) -> List[str]:
    """验证参数"""
    errors = []
    
    for key, value in params.items():
        if key not in PARAM_VALIDATION:
            continue
            
        validation = PARAM_VALIDATION[key]
        
        if validation["type"] == "select":
            if value not in validation["options"]:
                errors.append(f"{key} 必须是以下值之一: {', '.join(validation['options'])}")
        
        elif validation["type"] == "number":
            if not isinstance(value, (int, float)):
                errors.append(f"{key} 必须是数字")
            else:
                if "min" in validation and value < validation["min"]:
                    errors.append(f"{key} 不能小于 {validation['min']}")
                if "max" in validation and value > validation["max"]:
                    errors.append(f"{key} 不能大于 {validation['max']}")
        
        elif validation["type"] == "boolean":
            if not isinstance(value, bool):
                errors.append(f"{key} 必须是布尔值")
        
        elif validation["type"] == "date":
            if not isinstance(value, str):
                errors.append(f"{key} 必须是字符串")
            else:
                try:
                    datetime.strptime(value, "%Y/%m/%d")
                except ValueError:
                    errors.append(f"{key} 日期格式必须为 YYYY/MM/DD")
    
    return errors

@router.get("/parameters/fspm")
async def get_fspm_parameters():
    """获取FSPM当前参数"""
    params = _load_parameters()
    return JSONResponse(content=jsonable_encoder(params))

@router.put("/parameters/fspm")
async def update_fspm_parameters(params: FSPMParameters):
    """更新FSPM参数"""
    try:
        print(f"收到参数更新请求: {params.dict()}")
        
        # 验证参数
        print("开始验证参数...")
        errors = _validate_parameters(params.dict())
        if errors:
            print(f"参数验证失败: {errors}")
            raise HTTPException(status_code=400, detail={"errors": errors})
        print("参数验证通过")
        
        # 保存参数
        print(f"开始保存参数到文件: {PARAMS_FILE}")
        save_result = _save_parameters(params.dict())
        print(f"保存结果: {save_result}")
        
        if save_result:
            print("参数保存成功，返回成功响应")
            return JSONResponse(content={
                "message": "FSPM参数更新成功",
                "parameters": jsonable_encoder(params)
            })
        else:
            print("参数保存失败，返回错误响应")
            raise HTTPException(status_code=500, detail="参数保存失败")
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"API端点发生异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/parameters/fspm/defaults")
async def get_fspm_defaults():
    """获取FSPM默认参数"""
    return JSONResponse(content=jsonable_encoder(DEFAULT_PARAMS))

@router.get("/parameters/fspm/validation")
async def get_fspm_validation_rules():
    """获取FSPM参数验证规则"""
    return JSONResponse(content=jsonable_encoder(PARAM_VALIDATION))

@router.get("/fspm/files")
async def get_fspm_files():
    """获取FSPM必需文件列表"""
    files = [
        {
            "label": "植物网格文件",
            "key": "plant_mesh_file",
            "desc": "JK968-merge_scale.obj - 植物3D网格文件",
            "required": True,
            "accept": ".obj"
        },
        {
            "label": "气象数据文件",
            "key": "meteorological_file",
            "desc": "mete-haidian2021.csv - 气象数据",
            "required": True,
            "accept": ".csv"
        },
        {
            "label": "冠层数据文件",
            "key": "canopy_file",
            "desc": "dmy3_4000_made.csv - 冠层位置和高度数据",
            "required": True,
            "accept": ".csv"
        }
    ]
    return JSONResponse(content={"files": files})

@router.get("/fspm/descriptions")
async def get_fspm_descriptions():
    """获取FSPM参数说明"""
    descriptions = {}
    for key, validation in PARAM_VALIDATION.items():
        descriptions[key] = validation["description"]
    
    return JSONResponse(content={"descriptions": descriptions})

@router.post("/parameters/fspm/reset")
async def reset_fspm_parameters():
    """重置FSPM参数为默认值"""
    if _save_parameters(DEFAULT_PARAMS):
        return JSONResponse(content={
            "message": "FSPM参数已重置为默认值",
            "parameters": jsonable_encoder(DEFAULT_PARAMS)
        })
    else:
        raise HTTPException(status_code=500, detail="参数重置失败")
