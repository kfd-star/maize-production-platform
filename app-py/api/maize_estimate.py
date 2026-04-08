"""
Maize_Yield_API1 API路由
支持文件夹路径输入和文件上传两种方式
"""
from fastapi import APIRouter, Form, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
import shutil
import json
import uuid
import asyncio
import aiohttp
import requests  # 保留用于同步调用（兼容性）
from datetime import datetime
from pathlib import Path
from fastapi.responses import JSONResponse
from concurrent.futures import ThreadPoolExecutor
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.maize_estimate_config import (
    MAIZE_ESTIMATE_SERVICE,
    MAIZE_ESTIMATE_PATHS,
    APP_PY_OUTPUT_DIR,
    get_maize_estimate_url,
    read_maize_estimate_config_from_file,
    update_maize_estimate_config_file,
    get_default_maize_estimate_params
)

router = APIRouter()

# 任务管理器：存储正在运行的任务
# {task_id: {'cancelled': bool, 'process': subprocess.Popen or None}}
task_manager: Dict[str, Dict[str, Any]] = {}
task_manager_lock = threading.Lock()

# 文件映射：前端字段名 -> 目标文件名
FILE_MAPPING = {
    'climate_file': 'climate_data_even.npy',
    'params_file': 'param_values_corn.npy',
    'plant_doy_file': 'plant_DOY_even.npy',
    'n_fertilizer_file': 'sim_N_fertilizer_even.npy',
    'density_file': 'Density.npy',
    'soil_ad_file': 'Soil_AD.npy',
    'soil_bd_file': 'Soil_BD.npy',
    'soil_dul_file': 'Soil_DUL.npy',
    'soil_ll_file': 'Soil_LL.npy',
    'soil_ph_file': 'Soil_PH.npy',
    'soil_sat_file': 'Soil_Sat.npy',
    'soil_soc_file': 'Soil_SOC.npy',
}

# Shapefile 必需文件（基础文件）
SHP_REQUIRED_FILES = ['.shp', '.shx', '.dbf', '.prj', '.CPG']
# Shapefile 可选文件（扩展文件）
SHP_OPTIONAL_FILES = ['.sbn', '.sbx', '.shp.xml']

class MaizeEstimateConfig(BaseModel):
    """模型配置"""
    model_path: str = Field(default="TL-ONEYEAR425_MUS_SLB_Time_1031.sav", description="模型文件名")
    current_model: str = Field(default="TL-ONEYEAR425_MUS_SLB_Time_1031.sav", description="当前选择的模型文件名")

# 全局参数存储（参考LSTM实现）
current_params = {
    "MaizeEstimate": MaizeEstimateConfig()
}


# 已移除 copy_files_to_flask_input 函数
# 现在直接使用上传的目录作为Flask服务的输入目录，不需要再复制

async def call_flask_service_async(
    data_dir: Path, 
    shp_path: Path, 
    model_dir: Path, 
    output_path: Path,
    task_id: str
) -> Dict[str, Any]:
    """异步调用Flask服务进行预测，支持取消"""
    request_data = {
        "your_data_dir": str(data_dir),
        "model_data_dir": str(model_dir),
        "shp_input_path": str(shp_path),
        "geojson_output_path": str(output_path)
    }
    
    api_url = get_maize_estimate_url(MAIZE_ESTIMATE_SERVICE['API_ENDPOINT'])
    
    try:
        print(f"调用Flask服务: {api_url}")
        print(f"请求数据: {request_data}")
        print(f"任务ID: {task_id}")
        
        # 检查任务是否已取消
        with task_manager_lock:
            if task_id in task_manager and task_manager[task_id].get('cancelled', False):
                raise asyncio.CancelledError("任务已被取消")
        
        # 使用aiohttp异步调用
        timeout = aiohttp.ClientTimeout(total=MAIZE_ESTIMATE_SERVICE['TIMEOUT'])
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(api_url, json=request_data) as response:
                # 再次检查是否已取消
                with task_manager_lock:
                    if task_id in task_manager and task_manager[task_id].get('cancelled', False):
                        raise asyncio.CancelledError("任务已被取消")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Flask服务返回错误: {error_text}"
                    )
                
                result = await response.json()
                
                if result.get('code') != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"预测失败: {result.get('msg', '未知错误')}"
                    )
                
                return result
        
    except asyncio.CancelledError:
        print(f"任务 {task_id} 已被取消")
        raise
    except aiohttp.ClientError as e:
        if isinstance(e, aiohttp.ServerConnectionError):
            raise HTTPException(
                status_code=503,
                detail="无法连接到Flask服务，请确保服务已启动在8006端口"
            )
        elif isinstance(e, asyncio.TimeoutError):
            raise HTTPException(
                status_code=504,
                detail="Flask服务响应超时"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"调用Flask服务失败: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"调用Flask服务失败: {str(e)}"
        )

def call_flask_service(data_dir: Path, shp_path: Path, model_dir: Path, output_path: Path) -> Dict[str, Any]:
    """同步调用Flask服务进行预测（保留用于兼容性）"""
    request_data = {
        "your_data_dir": str(data_dir),
        "model_data_dir": str(model_dir),
        "shp_input_path": str(shp_path),
        "geojson_output_path": str(output_path)
    }
    
    api_url = get_maize_estimate_url(MAIZE_ESTIMATE_SERVICE['API_ENDPOINT'])
    
    try:
        print(f"调用Flask服务: {api_url}")
        print(f"请求数据: {request_data}")
        
        response = requests.post(
            api_url,
            json=request_data,
            timeout=MAIZE_ESTIMATE_SERVICE['TIMEOUT']
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Flask服务返回错误: {response.text}"
            )
        
        result = response.json()
        
        if result.get('code') != 200:
            raise HTTPException(
                status_code=500,
                detail=f"预测失败: {result.get('msg', '未知错误')}"
            )
        
        return result
        
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="无法连接到Flask服务，请确保服务已启动在8006端口"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Flask服务响应超时"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"调用Flask服务失败: {str(e)}"
        )

def process_flask_result(flask_result: Dict[str, Any], task_id: str, task_dir: Path, flask_output_path: Path, model_filename: str = None) -> Dict[str, Any]:
    """处理Flask返回的结果"""
    result_data = flask_result.get('result', {})
    static_info_str = result_data.get('static_info', '{}')
    
    # 解析统计信息
    try:
        if isinstance(static_info_str, str):
            static_info = json.loads(static_info_str)
        else:
            static_info = static_info_str
    except:
        static_info = {}
    
    # GeoJSON文件应该已经在任务目录中（因为flask_output_path指向task_dir）
    task_geojson = task_dir / 'prediction_results.geojson'
    if task_geojson.exists():
        print(f"✓ GeoJSON结果已保存: {task_geojson}")
    else:
        # 如果不在任务目录，尝试从Flask返回的output_path查找
        flask_output_dir = Path(result_data.get('output_path', ''))
        if flask_output_dir.exists():
            possible_geojson = flask_output_dir / 'prediction_results.geojson'
            if possible_geojson.exists():
                shutil.copy2(possible_geojson, task_geojson)
                print(f"✓ 复制GeoJSON结果: {task_geojson}")
            else:
                print(f"⚠️ 未找到GeoJSON文件，可能路径: {flask_output_dir}")
        else:
            print(f"⚠️ 未找到GeoJSON文件，可能路径: {flask_output_path}")
    
    # 生成task_info.json
    # 记录本次任务实际使用的算法参数快照（从 Maize_Yield_API1/predict/server/config.py 读取）
    try:
        algorithm_params_used = read_maize_estimate_config_from_file()
    except Exception:
        algorithm_params_used = {}

    task_info = {
        "task_id": task_id,
        "algorithm": "maize_estimate",
        "model_name": model_filename or "TL-ONEYEAR425_MUS_SLB_Time_1031.sav",
        "created_at": datetime.now().isoformat(),
        "output_path": str(task_dir),
        "static_info": static_info,
        "algorithm_params_used": algorithm_params_used,
        "status": "completed",
        "message": "估产完成"
    }
    
    task_info_path = task_dir / 'task_info.json'
    with open(task_info_path, 'w', encoding='utf-8') as f:
        json.dump(task_info, f, indent=2, ensure_ascii=False)
    
    return task_info

#
# 注意：此文件曾经存在两套重复的 /parameters/maize_estimate 路由定义。
# 重复路由会导致前端保存“算法参数”时命中只支持模型配置的接口，从而出现“保存成功但 config.py 未更新”的问题。
# 下面仅保留一套统一的参数接口（模型配置 + 算法参数），并确保算法参数会写回 Maize_Yield_API1/predict/server/config.py。

# 主预测接口
@router.post("/maize_estimate", tags=["maize_estimate"])
async def predict_maize_estimate(
    data_folder_path: Optional[str] = Form(None, description="数据文件夹路径（包含所有.npy文件）"),
    shp_folder_path: Optional[str] = Form(None, description="Shapefile文件夹路径（包含.shp, .shx, .dbf, .prj文件）"),
    # 数据文件（可选，如果提供了文件就不需要路径）
    data_files: Optional[List[UploadFile]] = File(None, description="数据文件列表（.npy文件）"),
    # Shapefile文件（可选，如果提供了文件就不需要路径）
    shp_files: Optional[List[UploadFile]] = File(None, description="Shapefile文件列表（.shp, .shx, .dbf, .prj文件）")
):
    """Maize_Yield_API1预测接口
    
    支持两种方式：
    1. 文件上传方式（推荐）：提供 data_files 和 shp_files，前端上传文件到服务器
    2. 文件夹路径方式（仅限后端可直接访问的路径）：提供 data_folder_path 和 shp_folder_path
    
    注意：路径方式要求后端能够直接访问该路径（通常需要前端和后端在同一台机器上，或使用共享存储）
    前端默认使用文件上传方式，因为浏览器安全限制无法直接访问用户本地路径
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        task_dir = APP_PY_OUTPUT_DIR / f"{task_id}_{timestamp}"
        task_dir.mkdir(parents=True, exist_ok=True)
        
        task_data_dir = task_dir / 'input_data'
        task_data_dir.mkdir(parents=True, exist_ok=True)
        
        task_shp_dir = task_dir / 'input_shp'
        
        # 获取模型配置
        current = current_params["MaizeEstimate"]
        model_filename = current.current_model if current.current_model else "TL-ONEYEAR425_MUS_SLB_Time_1031.sav"
        model_path = MAIZE_ESTIMATE_PATHS['MODEL_DIR'] / model_filename
        
        if not model_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"模型文件不存在: {model_path}"
            )
        
        # 处理数据文件：优先使用上传的文件，否则使用路径
        if data_files and len(data_files) > 0:
            # 文件上传方式
            print(f"使用文件上传方式处理数据文件，共 {len(data_files)} 个文件")
            
            # 直接保存所有上传的.npy文件，不进行筛查
            for file in data_files:
                if not file.filename:
                    continue
                
                filename = file.filename
                # 只使用文件名，去除路径信息（防止路径中包含目录）
                filename_only = Path(filename).name
                
                # 只保存.npy文件
                if filename_only.lower().endswith('.npy'):
                    target_file = task_data_dir / filename_only
                    with open(target_file, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    print(f"✓ 上传文件: {filename} -> {filename_only}")
                else:
                    print(f"⚠️ 跳过非.npy文件: {filename}")
        elif data_folder_path:
            # 文件夹路径方式
            print("使用文件夹路径方式处理数据文件")
            data_folder = Path(data_folder_path)
            if not data_folder.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"数据文件夹不存在: {data_folder_path}"
                )
            
            # 复制所有.npy文件到任务目录，不进行筛查
            npy_files = list(data_folder.glob('*.npy'))
            if len(npy_files) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"数据文件夹中没有找到.npy文件: {data_folder_path}"
                )
            
            for source_file in npy_files:
                target_file = task_data_dir / source_file.name
                shutil.copy2(source_file, target_file)
                print(f"✓ 从路径复制: {source_file.name}")
        else:
            raise HTTPException(
                status_code=400,
                detail="请提供数据文件夹路径或上传数据文件"
            )
        
        # 处理Shapefile：优先使用上传的文件，否则使用路径
        if shp_files and len(shp_files) > 0:
            # 文件上传方式
            print(f"使用文件上传方式处理Shapefile，共 {len(shp_files)} 个文件")
            task_shp_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查是否包含.shp文件
            has_shp = any(f.filename and f.filename.lower().endswith('.shp') for f in shp_files)
            if not has_shp:
                raise HTTPException(
                    status_code=400,
                    detail="Shapefile必须包含.shp文件"
                )
            
            # 保存所有上传的Shapefile相关文件（包括.shp, .shx, .dbf, .prj, .CPG, .sbn, .sbx, .shp.xml等）
            for file in shp_files:
                if not file.filename:
                    continue
                filename = file.filename
                filename_lower = filename.lower()
                ext = Path(filename).suffix  # 保留原始大小写
                
                # 检查是否是Shapefile相关文件
                if ext.lower() in ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.sbn', '.sbx', '.xml'] or \
                   filename_lower.endswith('.shp.xml'):
                    # 统一命名为"小区.扩展名"（保留原始扩展名大小写）
                    # 对于.shp.xml文件，使用.shp.xml作为扩展名
                    if filename_lower.endswith('.shp.xml'):
                        target_filename = '小区.shp.xml'
                    else:
                        target_filename = f'小区{ext}'
                    target_file = task_shp_dir / target_filename
                    
                    with open(target_file, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    print(f"✓ 上传Shapefile: {filename} -> {target_filename}")
        elif shp_folder_path:
            # 文件夹路径方式
            print("使用文件夹路径方式处理Shapefile")
            shp_folder = Path(shp_folder_path)
            if not shp_folder.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"Shapefile文件夹不存在: {shp_folder_path}"
                )
            
            task_shp_dir.mkdir(parents=True, exist_ok=True)
            for ext in SHP_REQUIRED_FILES:
                source_file = shp_folder / f'小区{ext}'
                if not source_file.exists():
                    # 尝试其他可能的文件名
                    shp_files_in_dir = list(shp_folder.glob(f'*{ext}'))
                    if shp_files_in_dir:
                        source_file = shp_files_in_dir[0]
                    else:
                        continue
                
                target_file = task_shp_dir / f'小区{ext}'
                shutil.copy2(source_file, target_file)
                print(f"✓ 复制Shapefile: {ext}")
        else:
            raise HTTPException(
                status_code=400,
                detail="请提供Shapefile文件夹路径或上传Shapefile文件"
            )
        
        shp_path = task_shp_dir / '小区.shp'
        
        # 直接使用上传的目录作为Flask服务的输入目录，不需要再复制
        # 输出文件也保存到任务目录
        flask_output_path = task_dir / 'prediction_results.geojson'
        
        # 注册任务到任务管理器
        with task_manager_lock:
            task_manager[task_id] = {
                'cancelled': False,
                'status': 'running',
                'created_at': datetime.now().isoformat()
            }
        
        try:
            # 使用异步方式调用Flask服务，支持取消
            flask_result = await call_flask_service_async(
                data_dir=task_data_dir,
                shp_path=shp_path,
                model_dir=MAIZE_ESTIMATE_PATHS['MODEL_DIR'],
                output_path=flask_output_path,
                task_id=task_id
            )
            
            # 检查任务是否在调用过程中被取消
            with task_manager_lock:
                if task_id in task_manager and task_manager[task_id].get('cancelled', False):
                    # 任务已被取消，清理并返回错误
                    del task_manager[task_id]
                    raise HTTPException(
                        status_code=499,  # Client Closed Request
                        detail="任务已被取消"
                    )
            
            # 处理结果
            task_info = process_flask_result(flask_result, task_id, task_dir, flask_output_path, model_filename)
            
            # 更新任务状态
            with task_manager_lock:
                if task_id in task_manager:
                    task_manager[task_id]['status'] = 'completed'
            
            return {
                "code": 200,
                "msg": "估产完成",
                "result": {
                    "task_id": task_id,
                    "output_path": str(task_dir),
                    "static_info": task_info["static_info"]
                }
            }
        except asyncio.CancelledError:
            # 任务被取消
            with task_manager_lock:
                if task_id in task_manager:
                    task_manager[task_id]['status'] = 'cancelled'
            raise HTTPException(
                status_code=499,
                detail="任务已被取消"
            )
        except HTTPException:
            # 更新任务状态为失败
            with task_manager_lock:
                if task_id in task_manager:
                    task_manager[task_id]['status'] = 'failed'
            raise
        except Exception as e:
            # 更新任务状态为失败
            with task_manager_lock:
                if task_id in task_manager:
                    task_manager[task_id]['status'] = 'failed'
            raise
        finally:
            # 清理任务管理器（保留一段时间用于查询）
            # 这里不立即删除，允许查询任务状态
            pass
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"预测失败: {str(e)}"}
        )

# 参数模型定义
class MaizeEstimateParameters(BaseModel):
    POPULATION_SIZE: Optional[int] = Field(default=50, description="种群大小", ge=1, le=1000)
    MAX_GENERATIONS: Optional[int] = Field(default=100, description="最大迭代次数", ge=1, le=10000)
    TIMEOUT: Optional[int] = Field(default=3600, description="超时时间（秒）", ge=1, le=86400)
    API_TIMEOUT: Optional[int] = Field(default=3600, description="API超时时间（秒）", ge=1, le=86400)
    MAX_WORKERS: Optional[int] = Field(default=4, description="最大工作线程数", ge=1, le=32)

# 全局参数存储（内存中）
current_maize_estimate_params: Optional[MaizeEstimateParameters] = None

# 统一的更新请求：兼容前端分别保存 config.value 和 maizeEstimateParams.value 的行为
class MaizeEstimateUpdateRequest(BaseModel):
    # 模型配置（前端 saveConfig 会提交）
    model_path: Optional[str] = Field(default=None, description="模型文件名（兼容字段）")
    current_model: Optional[str] = Field(default=None, description="当前选择的模型文件名（兼容字段）")

    # 算法参数（前端 saveParameters 会提交）
    POPULATION_SIZE: Optional[int] = Field(default=None, description="种群大小", ge=1, le=1000)
    MAX_GENERATIONS: Optional[int] = Field(default=None, description="最大迭代次数", ge=1, le=10000)
    TIMEOUT: Optional[int] = Field(default=None, description="超时时间（秒）", ge=1, le=86400)
    API_TIMEOUT: Optional[int] = Field(default=None, description="API超时时间（秒）", ge=1, le=86400)
    MAX_WORKERS: Optional[int] = Field(default=None, description="最大工作线程数", ge=1, le=32)


def _scan_available_models() -> List[str]:
    model_dir = MAIZE_ESTIMATE_PATHS['MODEL_DIR']
    available_models: List[str] = []
    if model_dir.exists():
        for file in model_dir.glob('*.sav'):
            available_models.append(file.name)
    return available_models

@router.get("/parameters/maize_estimate", tags=["maize_estimate"])
async def get_maize_estimate_params():
    """获取Maize_Yield_API1的当前参数"""
    try:
        # 1) 算法参数：从配置文件读取并同步到内存
        config_data = read_maize_estimate_config_from_file()

        global current_maize_estimate_params
        if current_maize_estimate_params is None:
            current_maize_estimate_params = MaizeEstimateParameters(**config_data)
        else:
            # 更新内存中的参数（从配置文件同步）
            for key, value in config_data.items():
                if hasattr(current_maize_estimate_params, key):
                    setattr(current_maize_estimate_params, key, value)

        # 2) 模型配置：仍沿用内存（前端用于选择模型文件名）
        current_model_cfg = current_params["MaizeEstimate"]

        return {
            "config": current_model_cfg.model_dump(),
            "params": current_maize_estimate_params.model_dump(),
            "available_models": _scan_available_models(),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取参数失败: {str(e)}"}
        )

@router.put("/parameters/maize_estimate", tags=["maize_estimate"])
async def update_maize_estimate_params(payload: MaizeEstimateUpdateRequest):
    """更新Maize_Yield_API1参数（模型配置 + 算法参数）"""
    try:
        # 1) 模型配置：更新内存（不写入 API1 的 config.py，因为那边是 MODEL_PATH/路径拼接）
        current_model_cfg = current_params["MaizeEstimate"]
        if payload.model_path:
            current_model_cfg.model_path = payload.model_path
        if payload.current_model:
            current_model_cfg.current_model = payload.current_model

        # 2) 算法参数：更新内存并写回 Maize_Yield_API1/predict/server/config.py
        algo_updates = payload.model_dump(exclude_unset=True)
        # 去掉模型字段，只保留算法参数字段
        algo_updates.pop("model_path", None)
        algo_updates.pop("current_model", None)
        algo_updates = {k: v for k, v in algo_updates.items() if v is not None}

        if algo_updates:
            global current_maize_estimate_params
            if current_maize_estimate_params is None:
                # 先以文件中的现值为基准，避免未提交字段被覆盖为默认值
                file_data = read_maize_estimate_config_from_file()
                current_maize_estimate_params = MaizeEstimateParameters(**file_data)

            for key, value in algo_updates.items():
                if hasattr(current_maize_estimate_params, key):
                    setattr(current_maize_estimate_params, key, value)

            update_maize_estimate_config_file(algo_updates)

        return {"message": "参数更新成功"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"参数更新失败: {str(e)}"}
        )

@router.get("/parameters/maize_estimate/defaults", tags=["maize_estimate"])
async def get_maize_estimate_defaults():
    """获取Maize_Yield_API1的默认参数（模型配置 + 算法参数 + 可用模型列表）"""
    try:
        return {
            "config": MaizeEstimateConfig().model_dump(),
            "params": get_default_maize_estimate_params(),
            "available_models": _scan_available_models(),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取默认参数失败: {str(e)}"}
        )
