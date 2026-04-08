"""
GNAH模型API路由
支持文件上传方式
"""
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
import shutil
import json
import uuid
import asyncio
import aiohttp
import requests
from datetime import datetime
from pathlib import Path
from fastapi.responses import JSONResponse
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.gnah_config import (
    GNAH_SERVICE,
    GNAH_PATHS,
    APP_PY_OUTPUT_DIR,
    get_gnah_url,
    read_gnah_config_from_file,
    update_gnah_config_file,
    update_gnah_model_files,
    update_gnah_model_coefficients,
    backup_and_update_gnah_data_paths,
    restore_gnah_data_paths,
    get_default_gnah_params,
    get_default_model_coefficients
)

router = APIRouter()

# 任务管理器：存储正在运行的任务
task_manager: Dict[str, Dict[str, Any]] = {}
task_manager_lock = threading.Lock()

class GNAHParameters(BaseModel):
    """GNAH算法参数"""
    output_prefix: str = Field(default="GNAH_Yield_Task1", description="输出文件前缀")

class GNAHConfig(BaseModel):
    """GNAH模型配置"""
    model_d1: str = Field(default="Model_d1.enc", description="模型文件d1（.enc文件）")
    model_d2: str = Field(default="Model_d2.joblib", description="模型文件d2（.joblib文件）")
    current_model_d1: str = Field(default="Model_d1.enc", description="当前选择的模型文件d1")
    current_model_d2: str = Field(default="Model_d2.joblib", description="当前选择的模型文件d2")

class GNAHUpdateRequest(BaseModel):
    """GNAH参数更新请求"""
    params: Optional[Dict[str, Any]] = Field(default=None, description="算法参数")
    config: Optional[Dict[str, Any]] = Field(default=None, description="模型配置")
    coefficients: Optional[Dict[str, float]] = Field(default=None, description="模型系数")

# 全局模型配置存储
current_gnah_config = GNAHConfig()

def _scan_available_models_d1() -> List[str]:
    """扫描可用的d1模型文件（.enc文件）"""
    model_dir = GNAH_PATHS['MODEL_D1'].parent  # data/input目录
    available_models: List[str] = []
    if model_dir.exists():
        for file in model_dir.glob('*.enc'):
            available_models.append(file.name)
    return available_models if available_models else ['Model_d1.enc']  # 默认值

def _scan_available_models_d2() -> List[str]:
    """扫描可用的d2模型文件（.joblib文件）"""
    model_dir = GNAH_PATHS['MODEL_D2'].parent  # data/input目录
    available_models: List[str] = []
    if model_dir.exists():
        for file in model_dir.glob('*.joblib'):
            available_models.append(file.name)
    return available_models if available_models else ['Model_d2.joblib']  # 默认值

async def call_gnah_service_async(
    task_id: str,
    output_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """异步调用GNAH服务进行预测，支持取消"""
    api_url = get_gnah_url(GNAH_SERVICE['API_ENDPOINT'])
    
    request_data = {}
    if output_prefix:
        request_data['output_prefix'] = output_prefix
    
    try:
        print(f"调用GNAH服务: {api_url}")
        print(f"请求数据: {request_data}")
        print(f"任务ID: {task_id}")
        
        # 检查任务是否已取消
        with task_manager_lock:
            if task_id in task_manager and task_manager[task_id].get('cancelled', False):
                raise asyncio.CancelledError("任务已被取消")
        
        # 使用aiohttp异步调用
        timeout = aiohttp.ClientTimeout(total=GNAH_SERVICE['TIMEOUT'])
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
                        detail=f"GNAH服务返回错误: {error_text}"
                    )
                
                result = await response.json()
                
                if result.get('code') != 200:
                    error_msg = result.get('msg', '未知错误')
                    # 检测内存错误
                    if 'Unable to allocate' in error_msg or 'MemoryError' in error_msg or 'ArrayMemoryError' in error_msg:
                        error_msg = (
                            "内存不足错误：模型需要分配大量内存来处理数据。\n"
                            "建议解决方案：\n"
                            "1. 减少数据文件数量\n"
                            "2. 使用更小的数据区域（减少图像尺寸）\n"
                            "3. 增加系统可用内存\n"
                            "4. 考虑分批处理数据\n\n"
                            f"原始错误: {error_msg}"
                        )
                    raise HTTPException(
                        status_code=500,
                        detail=error_msg
                    )
                
                return result
        
    except asyncio.CancelledError:
        print(f"任务 {task_id} 已被取消")
        raise
    except aiohttp.ClientError as e:
        if isinstance(e, aiohttp.ServerConnectionError):
            raise HTTPException(
                status_code=503,
                detail="无法连接到GNAH服务，请确保服务已启动在5000端口"
            )
        elif isinstance(e, asyncio.TimeoutError):
            raise HTTPException(
                status_code=504,
                detail="GNAH服务响应超时"
            )
        else:
            import traceback
            error_detail = traceback.format_exc()
            print(f"调用GNAH服务失败 (ClientError): {str(e)}")
            print(f"错误详情: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=f"调用GNAH服务失败: {str(e)}"
            )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"调用GNAH服务失败: {str(e)}")
        print(f"错误详情: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=f"调用GNAH服务失败: {str(e)}"
        )

def classify_file_to_directory(filename: str) -> Optional[str]:
    """根据文件名判断应该保存到哪个目录"""
    filename_lower = filename.lower()
    
    # 检查是否包含目录名关键词
    if 'era5' in filename_lower:
        return 'ERA5'
    elif 'modis_ref' in filename_lower or 'ref' in filename_lower:
        return 'MODIS_Ref'
    elif 'modis_par' in filename_lower or 'par' in filename_lower:
        return 'MODIS_PAR'
    
    # 如果文件名中包含路径分隔符，尝试从路径判断
    if '/' in filename or '\\' in filename:
        path_parts = filename.replace('\\', '/').split('/')
        for part in path_parts:
            part_lower = part.lower()
            if 'era5' in part_lower:
                return 'ERA5'
            elif 'modis_ref' in part_lower or ('ref' in part_lower and 'modis' in part_lower):
                return 'MODIS_Ref'
            elif 'modis_par' in part_lower or ('par' in part_lower and 'modis' in part_lower):
                return 'MODIS_PAR'
    
    return None

def process_flask_result(flask_result: Dict[str, Any], task_id: str, task_dir: Path) -> Dict[str, Any]:
    """处理Flask返回的结果"""
    result_data = flask_result.get('result', {})
    
    # 获取统计信息
    static_info = result_data.get('statistic', {})
    mean_yield = result_data.get('per_unit_yield', 0.0)
    
    # 复制输出文件到任务目录
    tif_path = result_data.get('per_unit_yield_tif_file', '')
    png_path = result_data.get('per_unit_yield_rgb_png_file', '')
    json_path = result_data.get('output_json_path', '')
    
    if tif_path and Path(tif_path).exists():
        shutil.copy2(tif_path, task_dir / Path(tif_path).name)
    
    if png_path and Path(png_path).exists():
        shutil.copy2(png_path, task_dir / Path(png_path).name)
    
    if json_path and Path(json_path).exists():
        shutil.copy2(json_path, task_dir / Path(json_path).name)
    
    # 生成task_info.json
    try:
        config_from_file = read_gnah_config_from_file()
        algorithm_params_used = config_from_file.get('params', {})
        model_files_used = config_from_file.get('model_files', {})
    except Exception:
        algorithm_params_used = {}
        model_files_used = {}
    
    task_info = {
        "task_id": task_id,
        "algorithm": "gnah",
        "created_at": datetime.now().isoformat(),
        "output_path": str(task_dir),
        "static_info": {
            "mean": mean_yield,
            "mean_yield_kg_mu": mean_yield,
            **static_info
        },
        "algorithm_params_used": algorithm_params_used,
        "model_files_used": model_files_used,
        "status": "completed",
        "message": "估产完成",
        "output_files": {
            "tif": Path(tif_path).name if tif_path else None,
            "png": Path(png_path).name if png_path else None,
            "json": Path(json_path).name if json_path else None
        }
    }
    
    task_info_path = task_dir / 'task_info.json'
    with open(task_info_path, 'w', encoding='utf-8') as f:
        json.dump(task_info, f, indent=2, ensure_ascii=False)
    
    return task_info

# 主预测接口
@router.post("/gnah", tags=["gnah"])
async def predict_gnah(
    era5_files: Optional[List[UploadFile]] = File(None, description="ERA5数据文件列表（.tif文件）"),
    modis_ref_files: Optional[List[UploadFile]] = File(None, description="MODIS_Ref数据文件列表（.tif文件）"),
    modis_par_files: Optional[List[UploadFile]] = File(None, description="MODIS_PAR数据文件列表（.tif文件）"),
    all_files: Optional[List[UploadFile]] = File(None, description="所有数据文件（自动分类到对应目录）"),
    output_prefix: Optional[str] = Form(None, description="输出文件前缀")
):
    """GNAH预测接口
    
    支持两种文件上传方式：
    1. 分类上传：分别提供 era5_files, modis_ref_files, modis_par_files
    2. 自动分类：提供 all_files，系统会根据文件名自动分类到对应目录
    
    注意：文件会被保存到 GNAH_Maize_Yield/data/input/{目录}/ 中
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        task_dir = APP_PY_OUTPUT_DIR / f"{task_id}_{timestamp}"
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建任务输入目录（类似API1的处理方式）
        task_input_dir = task_dir / 'input_data'
        task_input_era5_dir = task_input_dir / 'ERA5'
        task_input_modis_ref_dir = task_input_dir / 'MODIS_Ref'
        task_input_modis_par_dir = task_input_dir / 'MODIS_PAR'
        
        for dir_path in [task_input_era5_dir, task_input_modis_ref_dir, task_input_modis_par_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化任务管理器
        with task_manager_lock:
            task_manager[task_id] = {'cancelled': False}
        
        # 获取参数配置
        config = read_gnah_config_from_file()
        current_prefix = output_prefix or config.get('params', {}).get('output_prefix', 'GNAH_Yield_Task1')
        
        # 处理文件上传：先保存到任务目录
        files_saved = {
            'ERA5': 0,
            'MODIS_Ref': 0,
            'MODIS_PAR': 0
        }
        
        # 方式1：分类上传
        if era5_files or modis_ref_files or modis_par_files:
            if era5_files:
                for file in era5_files:
                    if file.filename and file.filename.lower().endswith('.tif'):
                        filename_only = Path(file.filename).name
                        target_path = task_input_era5_dir / filename_only
                        with open(target_path, "wb") as buffer:
                            shutil.copyfileobj(file.file, buffer)
                        files_saved['ERA5'] += 1
                        print(f"✓ 保存ERA5文件到任务目录: {file.filename} -> {target_path}")
            
            if modis_ref_files:
                for file in modis_ref_files:
                    if file.filename and file.filename.lower().endswith('.tif'):
                        filename_only = Path(file.filename).name
                        target_path = task_input_modis_ref_dir / filename_only
                        with open(target_path, "wb") as buffer:
                            shutil.copyfileobj(file.file, buffer)
                        files_saved['MODIS_Ref'] += 1
                        print(f"✓ 保存MODIS_Ref文件到任务目录: {file.filename} -> {target_path}")
            
            if modis_par_files:
                for file in modis_par_files:
                    if file.filename and file.filename.lower().endswith('.tif'):
                        filename_only = Path(file.filename).name
                        target_path = task_input_modis_par_dir / filename_only
                        with open(target_path, "wb") as buffer:
                            shutil.copyfileobj(file.file, buffer)
                        files_saved['MODIS_PAR'] += 1
                        print(f"✓ 保存MODIS_PAR文件到任务目录: {file.filename} -> {target_path}")
        
        # 方式2：自动分类上传
        elif all_files:
            for file in all_files:
                if not file.filename:
                    continue
                
                filename = file.filename
                filename_only = Path(filename).name
                directory = classify_file_to_directory(filename)
                
                if directory:
                    if filename.lower().endswith('.tif'):
                        if directory == 'ERA5':
                            target_path = task_input_era5_dir / filename_only
                        elif directory == 'MODIS_Ref':
                            target_path = task_input_modis_ref_dir / filename_only
                        elif directory == 'MODIS_PAR':
                            target_path = task_input_modis_par_dir / filename_only
                        else:
                            continue
                        
                        with open(target_path, "wb") as buffer:
                            shutil.copyfileobj(file.file, buffer)
                        files_saved[directory] += 1
                        print(f"✓ 自动分类保存到任务目录: {filename} -> {target_path}")
                else:
                    print(f"⚠️ 无法分类文件，跳过: {filename}")
        
        else:
            raise HTTPException(
                status_code=400,
                detail="请至少提供一种文件上传方式（分类上传或自动分类上传）"
            )
        
        # 检查是否有文件被保存
        total_files = sum(files_saved.values())
        if total_files == 0:
            raise HTTPException(
                status_code=400,
                detail="没有有效的.tif文件被上传"
            )
        
        print(f"文件上传完成: ERA5={files_saved['ERA5']}, MODIS_Ref={files_saved['MODIS_Ref']}, MODIS_PAR={files_saved['MODIS_PAR']}")
        
        # 临时修改GNAH的config.py，将DATA_PATHS指向任务目录（避免复制文件）
        original_paths = backup_and_update_gnah_data_paths(task_input_dir)
        print(f"✓ 已临时更新GNAH配置，使用任务目录: {task_input_dir}")
        
        try:
            # 调用Flask服务
            flask_result = await call_gnah_service_async(task_id, current_prefix)
        finally:
            # 恢复原始配置
            if original_paths:
                restore_gnah_data_paths(original_paths)
                print(f"✓ 已恢复GNAH配置到原始路径")
        
        # 处理结果
        task_info = process_flask_result(flask_result, task_id, task_dir)
        
        # 清理任务管理器
        with task_manager_lock:
            if task_id in task_manager:
                del task_manager[task_id]
        
        return JSONResponse(content={
            "code": 200,
            "msg": "预测完成",
            "result": {
                "task_id": task_id,
                "static_info": task_info.get('static_info', {}),
                "output_path": str(task_dir),
                "files_saved": files_saved
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"GNAH预测失败: {str(e)}")
        print(f"错误详情: {error_detail}")
        
        # 清理任务管理器
        with task_manager_lock:
            if task_id in task_manager:
                del task_manager[task_id]
        
        raise HTTPException(
            status_code=500,
            detail=f"预测失败: {str(e)}"
        )

# 参数接口
@router.get("/parameters/gnah", tags=["gnah"])
async def get_gnah_params():
    """获取GNAH参数配置"""
    try:
        config = read_gnah_config_from_file()
        return {
            "config": current_gnah_config.model_dump(),
            "params": config.get('params', get_default_gnah_params()),
            "coefficients": config.get('coefficients', {}),
            "available_models_d1": _scan_available_models_d1(),
            "available_models_d2": _scan_available_models_d2()
        }
    except Exception as e:
        print(f"获取GNAH参数失败: {e}")
        return {
            "config": current_gnah_config.model_dump(),
            "params": get_default_gnah_params(),
            "coefficients": {},
            "available_models_d1": _scan_available_models_d1(),
            "available_models_d2": _scan_available_models_d2()
        }

@router.put("/parameters/gnah", tags=["gnah"])
async def update_gnah_params(payload: GNAHUpdateRequest):
    """更新GNAH参数配置"""
    try:
        global current_gnah_config
        errors: List[str] = []
        
        # 更新模型配置（内存和配置文件）
        if payload.config:
            model_d1_updated = False
            model_d2_updated = False
            
            if 'current_model_d1' in payload.config:
                current_gnah_config.current_model_d1 = payload.config['current_model_d1']
                current_gnah_config.model_d1 = payload.config['current_model_d1']
                model_d1_updated = True
            
            if 'current_model_d2' in payload.config:
                current_gnah_config.current_model_d2 = payload.config['current_model_d2']
                current_gnah_config.model_d2 = payload.config['current_model_d2']
                model_d2_updated = True
            
            # 更新配置文件中的模型文件路径
            if model_d1_updated or model_d2_updated:
                ok = update_gnah_model_files(
                    current_gnah_config.current_model_d1,
                    current_gnah_config.current_model_d2
                )
                if not ok:
                    errors.append("写入GNAH配置文件失败：更新模型文件(model_d1/model_d2)未成功")
        
        # 更新算法参数（配置文件）
        if payload.params:
            ok = update_gnah_config_file(payload.params)
            if not ok:
                errors.append("写入GNAH配置文件失败：更新ALGORITHM_CONFIG未成功")
        
        # 更新模型系数（配置文件）
        if payload.coefficients:
            ok = update_gnah_model_coefficients(payload.coefficients)
            if not ok:
                errors.append("写入GNAH配置文件失败：更新MODEL_COEFFICIENTS未成功")

        if errors:
            raise HTTPException(status_code=500, detail="; ".join(errors))
        
        return {
            "code": 200,
            "msg": "参数更新成功",
            "result": {
                "config": current_gnah_config.model_dump(),
                "params": payload.params or {},
                "coefficients": payload.coefficients or {}
            }
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"更新参数失败: {str(e)}")

@router.get("/parameters/gnah/defaults", tags=["gnah"])
async def get_gnah_defaults():
    """获取GNAH默认参数"""
    return {
        "config": GNAHConfig().model_dump(),
        "params": get_default_gnah_params(),
        "coefficients": get_default_model_coefficients(),
        "available_models_d1": _scan_available_models_d1(),
        "available_models_d2": _scan_available_models_d2()
    }

# 取消任务接口
@router.post("/gnah/tasks/{task_id}/cancel", tags=["gnah"])
async def cancel_gnah_task(task_id: str):
    """取消正在运行的GNAH任务"""
    with task_manager_lock:
        if task_id in task_manager:
            task_manager[task_id]['cancelled'] = True
            return {"code": 200, "msg": "任务已标记为取消"}
        else:
            raise HTTPException(status_code=404, detail="任务不存在或已完成")
