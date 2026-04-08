"""
SCYM模型API路由
支持文件上传和路径输入两种方式
"""
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
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
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.scym_config import (
    SCYM_SERVICE,
    SCYM_PATHS,
    APP_PY_OUTPUT_DIR,
    get_scym_url,
    read_scym_config_from_file,
    update_scym_config_file,
    get_default_scym_coefficients,
    get_default_algorithm_config
)
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# 任务管理器：存储正在运行的任务
task_manager: Dict[str, Dict[str, Any]] = {}
task_manager_lock = threading.Lock()

async def call_scym_service_async(
    task_id: str,
    s2_dir: Optional[Path] = None,
    era5_dir: Optional[Path] = None,
    mask_path: Optional[Path] = None,
    roi_dir: Optional[Path] = None,
    output_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """异步调用SCYM服务进行预测，支持取消"""
    api_url = get_scym_url(SCYM_SERVICE['API_ENDPOINT'])
    
    request_data = {}
    if output_prefix:
        request_data['output_prefix'] = output_prefix
    # 只在路径存在且目录存在时才传递路径参数
    if s2_dir and s2_dir.exists():
        request_data['s2_dir'] = str(s2_dir)
        print(f"使用自定义Sentinel-2目录: {s2_dir}")
    if era5_dir and era5_dir.exists():
        request_data['era5_dir'] = str(era5_dir)
        print(f"使用自定义ERA5目录: {era5_dir}")
    if mask_path and mask_path.exists():
        request_data['mask_path'] = str(mask_path)
        print(f"使用自定义掩膜文件: {mask_path}")
    if roi_dir and roi_dir.exists():
        request_data['roi_dir'] = str(roi_dir)
        print(f"使用自定义ROI目录: {roi_dir}")
    
    try:
        print(f"调用SCYM服务: {api_url}")
        print(f"请求数据: {request_data}")
        print(f"任务ID: {task_id}")
        
        # 检查任务是否已取消
        with task_manager_lock:
            if task_id in task_manager and task_manager[task_id].get('cancelled', False):
                raise asyncio.CancelledError("任务已被取消")
        
        # 使用aiohttp异步调用
        timeout = aiohttp.ClientTimeout(total=SCYM_SERVICE['TIMEOUT'])
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
                        detail=f"SCYM服务返回错误: {error_text}"
                    )
                
                result = await response.json()
                
                if result.get('code') != 200:
                    error_msg = result.get('msg', '未知错误')
                    # 检测内存错误
                    if 'Unable to allocate' in error_msg or 'MemoryError' in error_msg or 'ArrayMemoryError' in error_msg:
                        error_msg = (
                            "内存不足错误：模型需要分配大量内存来处理数据。\n"
                            "建议解决方案：\n"
                            "1. 减少ERA5数据文件数量（当前有162个文件）\n"
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
                detail="无法连接到SCYM服务，请确保服务已启动在5000端口"
            )
        elif isinstance(e, asyncio.TimeoutError):
            raise HTTPException(
                status_code=504,
                detail="SCYM服务响应超时"
            )
        else:
            import traceback
            error_detail = traceback.format_exc()
            print(f"调用SCYM服务失败 (ClientError): {str(e)}")
            print(f"错误详情: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=f"调用SCYM服务失败: {str(e)}"
            )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"调用SCYM服务失败: {str(e)}")
        print(f"错误详情: {error_detail}")
        raise HTTPException(
            status_code=500,
            detail=f"调用SCYM服务失败: {str(e)}"
        )

def call_scym_service(output_prefix: Optional[str] = None) -> Dict[str, Any]:
    """同步调用SCYM服务（保留用于兼容性）"""
    api_url = get_scym_url(SCYM_SERVICE['API_ENDPOINT'])
    
    request_data = {}
    if output_prefix:
        request_data['output_prefix'] = output_prefix
    
    try:
        print(f"调用SCYM服务: {api_url}")
        print(f"请求数据: {request_data}")
        
        response = requests.post(
            api_url,
            json=request_data,
            timeout=SCYM_SERVICE['TIMEOUT']
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"SCYM服务返回错误: {response.text}"
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
            detail="无法连接到SCYM服务，请确保服务已启动在5000端口"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="SCYM服务响应超时"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"调用SCYM服务失败: {str(e)}"
        )

@router.post("/scym/predict", tags=["scym"])
async def predict_scym(
    output_prefix: Optional[str] = Form(None, description="输出文件前缀"),
    # 可选：文件上传方式
    s2_files: Optional[List[UploadFile]] = File(None, description="Sentinel-2影像文件列表"),
    era5_files: Optional[List[UploadFile]] = File(None, description="ERA5气象数据文件列表"),
    mask_file: Optional[UploadFile] = File(None, description="玉米分布掩膜文件"),
    roi_files: Optional[List[UploadFile]] = File(None, description="ROI Shapefile文件列表")
):
    """SCYM模型预测接口
    
    支持两种方式：
    1. 文件上传方式：上传所有必需的输入文件（Sentinel-2、ERA5、掩膜、ROI）
    2. 使用默认路径：使用SCYM项目目录下的默认数据路径
    
    注意：如果上传文件，需要确保SCYM服务能够访问这些文件。
    当前实现会将文件保存到SCYM的默认输入目录。
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        task_dir = APP_PY_OUTPUT_DIR / f"{task_id}_{timestamp}"
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # 注册任务
        with task_manager_lock:
            task_manager[task_id] = {
                'cancelled': False,
                'status': 'running',
                'created_at': datetime.now().isoformat()
            }
        
        # 处理文件上传（如果提供）
        task_input_s2_dir = None
        task_input_era5_dir = None
        task_input_mask_path = None
        task_input_roi_dir = None
        
        if s2_files or era5_files or mask_file or roi_files:
            print("使用文件上传方式处理输入文件")
            
            # 创建任务输入目录（用于保存上传的文件）
            task_input_dir = task_dir / 'input_data'
            task_input_s2_dir = task_input_dir / 'Sentinel2'
            task_input_era5_dir = task_input_dir / 'ERA5'
            task_input_mask_dir = task_input_dir / '玉米分布'
            task_input_roi_dir = task_input_dir / 'roi'
            
            task_input_s2_dir.mkdir(parents=True, exist_ok=True)
            task_input_era5_dir.mkdir(parents=True, exist_ok=True)
            task_input_mask_dir.mkdir(parents=True, exist_ok=True)
            task_input_roi_dir.mkdir(parents=True, exist_ok=True)
            
            # 直接保存到任务目录，不复制到SCYM固定目录
            if s2_files:
                print(f"处理 {len(s2_files)} 个Sentinel-2文件")
                for file in s2_files:
                    if file.filename and file.filename.lower().endswith('.tif'):
                        filename_only = Path(file.filename).name
                        # 只保存到任务目录
                        task_target = task_input_s2_dir / filename_only
                        with open(task_target, "wb") as buffer:
                            shutil.copyfileobj(file.file, buffer)
                        print(f"✓ 上传Sentinel-2文件: {file.filename} -> {filename_only} (任务目录: {task_input_s2_dir})")
            
            if era5_files:
                print(f"处理 {len(era5_files)} 个ERA5文件")
                for file in era5_files:
                    if file.filename and file.filename.lower().endswith('.tif'):
                        filename_only = Path(file.filename).name
                        # 只保存到任务目录
                        task_target = task_input_era5_dir / filename_only
                        with open(task_target, "wb") as buffer:
                            shutil.copyfileobj(file.file, buffer)
                        print(f"✓ 上传ERA5文件: {file.filename} -> {filename_only} (任务目录: {task_input_era5_dir})")
            
            if mask_file:
                print("处理玉米分布掩膜文件")
                if mask_file.filename and mask_file.filename.lower().endswith('.tif'):
                    # 只保存到任务目录
                    task_input_mask_path = task_input_mask_dir / 'maize_mask.tif'
                    with open(task_input_mask_path, "wb") as buffer:
                        shutil.copyfileobj(mask_file.file, buffer)
                    print(f"✓ 上传掩膜文件: {mask_file.filename} -> maize_mask.tif (任务目录: {task_input_mask_dir})")
            
            if roi_files:
                print(f"处理 {len(roi_files)} 个ROI文件")
                for file in roi_files:
                    if file.filename:
                        ext = Path(file.filename).suffix.lower()
                        filename_lower = file.filename.lower()
                        # 支持所有Shapefile相关文件
                        if ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.sbn', '.sbx', '.xml'] or \
                           filename_lower.endswith('.shp.xml'):
                            filename_only = Path(file.filename).name
                            # 只保存到任务目录
                            task_target = task_input_roi_dir / filename_only
                            with open(task_target, "wb") as buffer:
                                shutil.copyfileobj(file.file, buffer)
                            print(f"✓ 上传ROI文件: {file.filename} -> {filename_only} (任务目录: {task_input_roi_dir})")
        
        # 验证必需的文件是否存在（如果上传了文件）
        if task_input_s2_dir or task_input_era5_dir or task_input_mask_path:
            if task_input_s2_dir and not task_input_s2_dir.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"Sentinel-2目录不存在: {task_input_s2_dir}"
                )
            if task_input_era5_dir and not task_input_era5_dir.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"ERA5目录不存在: {task_input_era5_dir}"
                )
            if task_input_mask_path and not task_input_mask_path.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"掩膜文件不存在: {task_input_mask_path}"
                )
            # 检查目录中是否有文件
            if task_input_s2_dir and len(list(task_input_s2_dir.glob('*.tif'))) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Sentinel-2目录中没有找到.tif文件: {task_input_s2_dir}"
                )
            if task_input_era5_dir and len(list(task_input_era5_dir.glob('*.tif'))) == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"ERA5目录中没有找到.tif文件: {task_input_era5_dir}"
                )
            
            # 检查ERA5文件数量，如果过多则给出警告
            if task_input_era5_dir:
                era5_file_count = len(list(task_input_era5_dir.glob('*.tif')))
                if era5_file_count > 100:
                    print(f"⚠️ 警告: ERA5文件数量较多 ({era5_file_count}个)，可能需要大量内存。")
                    print(f"   如果遇到内存不足错误，建议减少文件数量或使用更小的数据区域。")
        
        # 调用SCYM服务，直接传递任务目录路径
        try:
            print(f"准备调用SCYM服务，任务ID: {task_id}")
            print(f"Sentinel-2目录: {task_input_s2_dir}")
            print(f"ERA5目录: {task_input_era5_dir}")
            print(f"掩膜文件: {task_input_mask_path}")
            print(f"ROI目录: {task_input_roi_dir}")
            
            result = await call_scym_service_async(
                task_id=task_id,
                s2_dir=task_input_s2_dir,
                era5_dir=task_input_era5_dir,
                mask_path=task_input_mask_path,
                roi_dir=task_input_roi_dir,
                output_prefix=output_prefix or f"scym_{task_id}"
            )
            
            # 检查任务是否被取消
            with task_manager_lock:
                if task_id in task_manager and task_manager[task_id].get('cancelled', False):
                    del task_manager[task_id]
                    raise HTTPException(
                        status_code=499,
                        detail="任务已被取消"
                    )
            
            # 处理结果
            result_data = result.get('result', {})
            
            # 复制结果文件到任务目录
            tif_source = Path(result_data.get('per_unit_yield_tif_file', ''))
            png_source = Path(result_data.get('per_unit_yield_rgb_png_file', ''))
            json_source = Path(result_data.get('output_json_path', ''))
            
            if tif_source.exists():
                shutil.copy2(tif_source, task_dir / tif_source.name)
                print(f"✓ 复制TIF结果: {tif_source.name}")
            if png_source.exists():
                shutil.copy2(png_source, task_dir / png_source.name)
                print(f"✓ 复制PNG结果: {png_source.name}")
            if json_source.exists():
                shutil.copy2(json_source, task_dir / json_source.name)
                print(f"✓ 复制JSON结果: {json_source.name}")
            
            # 解析统计信息
            per_unit_yield = result_data.get('per_unit_yield', 0)
            static_info = {
                "mean": float(per_unit_yield),
                "count": 1,  # SCYM返回的是平均单产
                "max": float(per_unit_yield),
                "min": float(per_unit_yield)
            }
            
            # 生成task_info.json
            task_info = {
                "task_id": task_id,
                "algorithm": "scym",
                "model_name": "SCYM",
                "created_at": datetime.now().isoformat(),
                "output_path": str(task_dir),
                "per_unit_yield": per_unit_yield,
                "static_info": json.dumps(static_info),
                "status": "completed",
                "message": "预测完成"
            }
            
            task_info_path = task_dir / 'task_info.json'
            with open(task_info_path, 'w', encoding='utf-8') as f:
                json.dump(task_info, f, indent=2, ensure_ascii=False)
            
            # 更新任务状态
            with task_manager_lock:
                if task_id in task_manager:
                    task_manager[task_id]['status'] = 'completed'
            
            return {
                "code": 200,
                "msg": "预测完成",
                "result": {
                    "task_id": task_id,
                    "output_path": str(task_dir),
                    "per_unit_yield": per_unit_yield,
                    "static_info": static_info
                }
            }
            
        except asyncio.CancelledError:
            with task_manager_lock:
                if task_id in task_manager:
                    task_manager[task_id]['status'] = 'cancelled'
            raise HTTPException(
                status_code=499,
                detail="任务已被取消"
            )
        except HTTPException:
            with task_manager_lock:
                if task_id in task_manager:
                    task_manager[task_id]['status'] = 'failed'
            raise
        except HTTPException as e:
            # 如果是HTTPException，直接传递错误信息
            with task_manager_lock:
                if task_id in task_manager:
                    task_manager[task_id]['status'] = 'failed'
                    task_manager[task_id]['message'] = e.detail
            raise
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            error_msg = str(e)
            
            # 检测内存错误
            if 'Unable to allocate' in error_msg or 'MemoryError' in error_msg or 'ArrayMemoryError' in error_msg:
                error_msg = (
                    "内存不足错误：模型需要分配大量内存来处理数据。\n"
                    "建议解决方案：\n"
                    "1. 减少ERA5数据文件数量\n"
                    "2. 使用更小的数据区域（减少图像尺寸）\n"
                    "3. 增加系统可用内存\n"
                    "4. 考虑分批处理数据\n\n"
                    f"原始错误: {error_msg}"
                )
            
            print(f"预测失败: {error_msg}")
            print(f"错误详情: {error_detail}")
            with task_manager_lock:
                if task_id in task_manager:
                    task_manager[task_id]['status'] = 'failed'
                    task_manager[task_id]['message'] = error_msg
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
            
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"处理请求失败: {str(e)}")
        print(f"错误详情: {error_detail}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"处理请求失败: {str(e)}"
        )

# 参数模型定义
class SCYMCoefficients(BaseModel):
    constant: float = Field(default=-648.7124, description="常数项")
    tmean: float = Field(default=491.0432, description="平均温度系数")
    tmean2: float = Field(default=-11.9421, description="平均温度平方系数")
    rain: float = Field(default=5.1636, description="降雨系数")
    rain2: float = Field(default=-0.0032, description="降雨平方系数")
    base_value: float = Field(default=1424.7642, description="基础值")
    gcvi_constant: float = Field(default=-5.1387, description="GCVI常数项")
    gcvi_tmean: float = Field(default=-0.1163, description="GCVI平均温度系数")
    gcvi_tmean2: float = Field(default=0.0035, description="GCVI平均温度平方系数")
    gcvi_rain: float = Field(default=-0.0025, description="GCVI降雨系数")
    gcvi_rain2: float = Field(default=0.00000175, description="GCVI降雨平方系数")
    gcvi_multiplier: float = Field(default=1197.3193, description="GCVI乘数")

class SCYMAlgorithmConfig(BaseModel):
    yield_output_prefix: str = Field(default="test_Cropland_Yield_2025", description="产量输出文件前缀")

class SCYMParameters(BaseModel):
    coefficients: Optional[SCYMCoefficients] = None
    algorithm_config: Optional[SCYMAlgorithmConfig] = None

# 全局参数存储（内存中）
current_scym_params: Optional[SCYMParameters] = None

# 获取参数
@router.get("/parameters/scym", tags=["scym"])
async def get_scym_params():
    """获取SCYM的当前参数"""
    try:
        # 从配置文件读取
        config_data = read_scym_config_from_file()
        
        # 如果内存中没有参数，从配置文件加载
        global current_scym_params
        if current_scym_params is None:
            current_scym_params = SCYMParameters(
                coefficients=SCYMCoefficients(**config_data['coefficients']),
                algorithm_config=SCYMAlgorithmConfig(**config_data['algorithm_config'])
            )
        else:
            # 更新内存中的参数（从配置文件同步）
            current_scym_params.coefficients = SCYMCoefficients(**config_data['coefficients'])
            current_scym_params.algorithm_config = SCYMAlgorithmConfig(**config_data['algorithm_config'])
        
        return {
            "coefficients": current_scym_params.coefficients.model_dump() if current_scym_params.coefficients else None,
            "algorithm_config": current_scym_params.algorithm_config.model_dump() if current_scym_params.algorithm_config else None
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取参数失败: {str(e)}"}
        )

# 更新参数
@router.put("/parameters/scym", tags=["scym"])
async def update_scym_params(params: SCYMParameters):
    """更新SCYM的参数"""
    try:
        global current_scym_params
        
        # 更新内存中的参数
        if current_scym_params is None:
            current_scym_params = SCYMParameters()
        
        if params.coefficients is not None:
            current_scym_params.coefficients = params.coefficients
            # 更新配置文件
            update_scym_config_file(
                coefficients=params.coefficients.model_dump()
            )
        
        if params.algorithm_config is not None:
            current_scym_params.algorithm_config = params.algorithm_config
            # 更新配置文件
            update_scym_config_file(
                algorithm_config=params.algorithm_config.model_dump()
            )
        
        return {"message": "参数更新成功"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"参数更新失败: {str(e)}"}
        )

# 获取默认参数
@router.get("/parameters/scym/defaults", tags=["scym"])
async def get_scym_defaults():
    """获取SCYM的默认参数"""
    try:
        return {
            "coefficients": get_default_scym_coefficients(),
            "algorithm_config": get_default_algorithm_config()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"获取默认参数失败: {str(e)}"}
        )
