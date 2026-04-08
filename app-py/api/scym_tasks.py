"""
SCYM任务管理路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any
import os
import sys
import json
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.scym_config import APP_PY_OUTPUT_DIR

# 导入任务管理器（延迟导入避免循环导入）
def get_task_manager():
    from api.scym import task_manager, task_manager_lock
    return task_manager, task_manager_lock

router = APIRouter()

def _scan_scym_tasks():
    """扫描output目录中的SCYM任务"""
    tasks = []
    
    if not APP_PY_OUTPUT_DIR.exists():
        return tasks
    
    # 扫描所有任务目录（格式：<task_id>_<timestamp>）
    for folder in APP_PY_OUTPUT_DIR.iterdir():
        if folder.is_dir() and '_' in folder.name:
            task_info_file = folder / 'task_info.json'
            
            if task_info_file.exists():
                try:
                    with open(task_info_file, 'r', encoding='utf-8') as f:
                        task_info = json.load(f)
                    
                    # 只返回SCYM的任务
                    if task_info.get('algorithm') == 'scym':
                        # 确保输出路径存在
                        tif_files = list(folder.glob('*.tif'))
                        png_files = list(folder.glob('*.png'))
                        json_files = list(folder.glob('*.json'))
                        
                        if tif_files:
                            task_info['output_tif'] = str(tif_files[0])
                        if png_files:
                            task_info['output_png'] = str(png_files[0])
                        if json_files:
                            # 排除task_info.json
                            result_json = [f for f in json_files if f.name != 'task_info.json']
                            if result_json:
                                task_info['output_json'] = str(result_json[0])
                        
                        task_info['output_dir'] = str(folder)
                        tasks.append(task_info)
                except Exception as e:
                    print(f"读取任务信息失败 {folder}: {e}")
    
    # 按创建时间倒序排列
    tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return tasks

@router.get("/scym/tasks", tags=["scym_tasks"])
async def list_scym_tasks():
    """获取所有SCYM任务列表"""
    try:
        tasks = _scan_scym_tasks()
        return JSONResponse(content={"tasks": tasks})
    except Exception as e:
        return JSONResponse(
            content={"error": f"获取任务列表失败: {str(e)}"},
            status_code=500
        )

@router.get("/scym/tasks/{task_id}", tags=["scym_tasks"])
async def get_scym_task(task_id: str):
    """获取特定SCYM任务的详细信息"""
    try:
        tasks = _scan_scym_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(
                content={"error": "任务不存在"},
                status_code=404
            )
        
        # 解析static_info
        if "static_info" in task:
            static_info = task["static_info"]
            if isinstance(static_info, str):
                static_info = json.loads(static_info)
            
            task["data_summary"] = {
                "per_unit_yield": static_info.get("mean", 0),
                "mean_yield": static_info.get("mean", 0),
                "max_yield": static_info.get("max", 0),
                "min_yield": static_info.get("min", 0),
                "total_records": static_info.get("count", 1)
            }
        
        return JSONResponse(content=task)
    except Exception as e:
        return JSONResponse(
            content={"error": f"获取任务详情失败: {str(e)}"},
            status_code=500
        )

@router.delete("/scym/tasks/{task_id}", tags=["scym_tasks"])
async def delete_scym_task(task_id: str):
    """删除SCYM任务"""
    try:
        tasks = _scan_scym_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(
                content={"error": "任务不存在"},
                status_code=404
            )
        
        # 删除任务文件夹
        output_dir = task.get("output_dir")
        if output_dir and os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            return JSONResponse(content={"message": "任务已删除"})
        else:
            return JSONResponse(
                content={"error": "任务文件夹不存在"},
                status_code=404
            )
    except Exception as e:
        return JSONResponse(
            content={"error": f"删除任务失败: {str(e)}"},
            status_code=500
        )

@router.get("/scym/download/{task_id}", tags=["scym_tasks"])
async def download_scym_result(task_id: str, format: str = "tif"):
    """下载SCYM任务结果文件
    
    format: tif, png, json
    """
    try:
        tasks = _scan_scym_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(
                content={"error": "任务不存在"},
                status_code=404
            )
        
        output_dir = Path(task["output_dir"])
        
        if format == "tif":
            tif_file = task.get("output_tif")
            if tif_file and Path(tif_file).exists():
                return FileResponse(
                    path=tif_file,
                    filename=Path(tif_file).name,
                    media_type="image/tiff"
                )
            else:
                return JSONResponse(
                    content={"error": "TIF文件不存在"},
                    status_code=404
                )
        elif format == "png":
            png_file = task.get("output_png")
            if png_file and Path(png_file).exists():
                return FileResponse(
                    path=png_file,
                    filename=Path(png_file).name,
                    media_type="image/png"
                )
            else:
                return JSONResponse(
                    content={"error": "PNG文件不存在"},
                    status_code=404
                )
        elif format == "json":
            json_file = task.get("output_json")
            if json_file and Path(json_file).exists():
                return FileResponse(
                    path=json_file,
                    filename=Path(json_file).name,
                    media_type="application/json"
                )
            else:
                return JSONResponse(
                    content={"error": "JSON文件不存在"},
                    status_code=404
                )
        else:
            return JSONResponse(
                content={"error": "不支持的格式，只支持 tif, png, json"},
                status_code=400
            )
    except Exception as e:
        return JSONResponse(
            content={"error": f"下载文件失败: {str(e)}"},
            status_code=500
        )

@router.post("/scym/tasks/{task_id}/cancel", tags=["scym_tasks"])
async def cancel_scym_task(task_id: str):
    """取消正在运行的SCYM任务"""
    try:
        task_manager, task_manager_lock = get_task_manager()
        
        with task_manager_lock:
            if task_id not in task_manager:
                return JSONResponse(
                    content={"error": "任务不存在或已完成"},
                    status_code=404
                )
            
            task_info = task_manager[task_id]
            
            if task_info.get('status') in ['completed', 'cancelled', 'failed']:
                return JSONResponse(
                    content={"error": f"任务已{task_info.get('status')}，无法取消"},
                    status_code=400
                )
            
            # 标记任务为已取消
            task_info['cancelled'] = True
            task_info['status'] = 'cancelling'
            
            return JSONResponse(content={
                "message": "任务取消请求已发送",
                "task_id": task_id,
                "status": "cancelling"
            })
    except Exception as e:
        return JSONResponse(
            content={"error": f"取消任务失败: {str(e)}"},
            status_code=500
        )
