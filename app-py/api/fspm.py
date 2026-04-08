from fastapi import APIRouter, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import sys
import subprocess
import json
import shutil
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import glob
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter()

# FSPM参数模型定义
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

# 全局参数存储
current_fspm_params = {
    "FSPM": FSPMParameters()
}

def _write_fspm_config_file(params: FSPMParameters, plant_mesh_path: str, meteo_path: str, canopy_path: str, output_path: str, process_path: str):
    """写入FSPM配置文件"""
    config = {
        "cultivar": params.cultivar,
        "density": params.density,
        "canopy_recon_mode": params.canopy_recon_mode,
        "use_measured_heights": params.use_measured_heights,
        "row_distance": params.row_distance,
        "num_rows": params.num_rows,
        "plants_per_row": params.plants_per_row,
        "plant_azimuth_range": params.plant_azimuth_range,
        "roi_num_plants": params.roi_num_plants,
        "date_planting": params.date_planting,
        "date_start": params.date_start,
        "date_end": params.date_end,
        "longitude": params.longitude,
        "latitude": params.latitude,
        "double_side_facet": params.double_side_facet,
        "fn_plantMesh": plant_mesh_path,
        "fn_meteorological_data": meteo_path,
        "fn_canopy_PosAzimuthHeights_data": canopy_path,
        "path_process": process_path,
        "fn_output_results": output_path
    }
    
    config_path = "./fspm_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return config_path

def _run_fspm_executable(plant_mesh_path: str, meteo_path: str, canopy_path: str, output_path: str, process_path: str, params: FSPMParameters):
    """运行FSPM可执行文件"""
    # 确保输出目录存在
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(process_path, exist_ok=True)
    
    # 构建命令行参数
    fspm_exe_path = "./FSPM_Corn_Growth/dmb_API/000/main.exe"
    
    cmd = [
        fspm_exe_path,
        f"--fn_plantMesh={plant_mesh_path}",
        f"--fn_meteorological_data={meteo_path}",
        f"--fn_canopy_PosAzimuthHeights_data={canopy_path}",
        f"--fn_output_results={output_path}",
        f"--path_process={process_path}"
    ]
    
    # 运行可执行文件
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1小时超时
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "任务执行超时"
    except Exception as e:
        return False, "", str(e)

# 参数管理路由已移动到 fspm_parameters.py 中
# 这里不再重复定义，避免路由冲突

@router.get("/fspm/files")
async def get_fspm_files():
    """获取FSPM必需文件列表"""
    files = [
        {"label": "植物网格文件", "key": "plant_mesh_file", "desc": "JK968-merge_scale.obj - 植物3D网格文件", "required": True},
        {"label": "气象数据文件", "key": "meteorological_file", "desc": "mete-haidian2021.csv - 气象数据", "required": True},
        {"label": "冠层数据文件", "key": "canopy_file", "desc": "dmy3_4000_made.csv - 冠层位置和高度数据", "required": True}
    ]
    return JSONResponse(content={"files": files})

@router.get("/fspm/descriptions")
async def get_fspm_descriptions():
    """获取FSPM参数说明"""
    descriptions = {
        "cultivar": "玉米品种选择，影响植物形态和生理参数",
        "density": "种植密度，单位：株/公顷",
        "row_distance": "行距，单位：厘米",
        "num_rows": "种植行数",
        "plants_per_row": "每行株数",
        "plant_azimuth_range": "植物方位角范围，单位：度",
        "roi_num_plants": "感兴趣区域植物数量",
        "date_planting": "种植日期，格式：YYYY/MM/DD",
        "date_start": "模拟开始日期，格式：YYYY/MM/DD",
        "date_end": "模拟结束日期，格式：YYYY/MM/DD",
        "longitude": "经度，单位：度",
        "latitude": "纬度，单位：度",
        "double_side_facet": "是否使用双面刻面",
        "canopy_recon_mode": "冠层重建模式",
        "use_measured_heights": "是否使用测量高度"
    }
    return JSONResponse(content={"descriptions": descriptions})

@router.post("/fspm")
async def run_fspm(
    plant_mesh_file: UploadFile = File(..., description="植物网格文件"),
    meteorological_file: UploadFile = File(..., description="气象数据文件"),
    canopy_file: UploadFile = File(..., description="冠层数据文件")
):
    """FSPM算法接口 - 使用当前配置的参数运行算法"""
    input_dir = "./inputfile/fspm"
    output_dir = "./output/fspm"
    process_dir = "./process/fspm"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(process_dir, exist_ok=True)

    # 保存上传的文件
    plant_mesh_path = os.path.join(input_dir, plant_mesh_file.filename)
    meteo_path = os.path.join(input_dir, meteorological_file.filename)
    canopy_path = os.path.join(input_dir, canopy_file.filename)
    
    with open(plant_mesh_path, "wb") as f:
        shutil.copyfileobj(plant_mesh_file.file, f)
    
    with open(meteo_path, "wb") as f:
        shutil.copyfileobj(meteorological_file.file, f)
    
    with open(canopy_path, "wb") as f:
        shutil.copyfileobj(canopy_file.file, f)

    try:
        # 获取当前参数
        params = current_fspm_params["FSPM"]
        
        # 生成输出文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"fspm_results_{timestamp}.csv")
        
        # 运行FSPM算法
        success, stdout, stderr = _run_fspm_executable(
            plant_mesh_path, meteo_path, canopy_path, 
            output_file, process_dir, params
        )
        
        if not success:
            return JSONResponse(
                content={"error": f"FSPM算法执行失败: {stderr}"}, 
                status_code=500
            )
        
        # 解析结果
        result = {
            "status": "success",
            "message": "FSPM模型运行完成",
            "parameters": {
                "fn_plantMesh": plant_mesh_path,
                "fn_meteorological_data": meteo_path,
                "fn_canopy_PosAzimuthHeights_data": canopy_path,
                "fn_output_results": output_file
            },
            "stdout": stdout,
            "output_file": output_file
        }
        
        # 如果输出文件存在，尝试读取结果
        if os.path.exists(output_file):
            try:
                df = pd.read_csv(output_file)
                result["data"] = df.to_dict(orient="records")
            except Exception as e:
                result["data_error"] = str(e)
        
        return JSONResponse(content=jsonable_encoder(result), status_code=200)
        
    except Exception as e:
        return JSONResponse(
            content={"error": f"FSPM算法执行异常: {str(e)}"}, 
            status_code=500
        )
