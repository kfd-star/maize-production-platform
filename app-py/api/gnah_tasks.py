"""
GNAH任务管理路由
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
from core.gnah_config import APP_PY_OUTPUT_DIR

router = APIRouter()

def _scan_gnah_tasks():
    """扫描output目录中的GNAH任务"""
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
                    
                    # 只返回GNAH的任务
                    if task_info.get('algorithm') == 'gnah':
                        # 确保输出路径存在
                        output_files = task_info.get('output_files', {})
                        task_info['output_path'] = str(folder)
                        task_info['output_dir'] = str(folder)
                        task_info['output_files'] = output_files
                        
                        tasks.append(task_info)
                except Exception as e:
                    print(f"读取任务信息失败 {folder}: {e}")
    
    # 按创建时间倒序排列
    tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return tasks

@router.get("/gnah/tasks", tags=["gnah_tasks"])
async def list_gnah_tasks():
    """获取所有GNAH任务列表"""
    try:
        tasks = _scan_gnah_tasks()
        return JSONResponse(content={"tasks": tasks})
    except Exception as e:
        return JSONResponse(
            content={"error": f"获取任务列表失败: {str(e)}"},
            status_code=500
        )

@router.get("/gnah/tasks/{task_id}", tags=["gnah_tasks"])
async def get_gnah_task(task_id: str):
    """获取特定GNAH任务的详细信息"""
    try:
        tasks = _scan_gnah_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(
                content={"error": "任务不存在"},
                status_code=404
            )
        
        # 添加数据摘要
        if "static_info" in task:
            static_info = task["static_info"]
            if isinstance(static_info, str):
                static_info = json.loads(static_info)
            
            task["data_summary"] = {
                "mean_yield": static_info.get("mean", 0),
                "mean_yield_kg_mu": static_info.get("mean_yield_kg_mu", 0),
                **static_info
            }
        
        return JSONResponse(content=task)
    except Exception as e:
        return JSONResponse(
            content={"error": f"获取任务详情失败: {str(e)}"},
            status_code=500
        )

@router.delete("/gnah/tasks/{task_id}", tags=["gnah_tasks"])
async def delete_gnah_task(task_id: str):
    """删除GNAH任务"""
    try:
        tasks = _scan_gnah_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(
                content={"error": "任务不存在"},
                status_code=404
            )
        
        # 删除任务目录
        task_dir = Path(task.get('output_path', ''))
        if task_dir.exists() and task_dir.is_dir():
            shutil.rmtree(task_dir)
            return JSONResponse(content={"code": 200, "msg": "任务已删除"})
        else:
            return JSONResponse(
                content={"error": "任务目录不存在"},
                status_code=404
            )
    except Exception as e:
        return JSONResponse(
            content={"error": f"删除任务失败: {str(e)}"},
            status_code=500
        )

@router.get("/gnah/download/{task_id}", tags=["gnah_tasks"])
async def download_gnah_result(task_id: str, format: str = "tif"):
    """下载GNAH任务结果文件
    
    支持的格式：
    - tif: 产量栅格数据
    - png: 渲染图像
    - json: 结果统计信息
    """
    try:
        tasks = _scan_gnah_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task_dir = Path(task.get('output_path', ''))
        output_files = task.get('output_files', {})
        
        # 根据格式选择文件
        filename = None
        if format.lower() == 'tif':
            filename = output_files.get('tif')
        elif format.lower() == 'png':
            filename = output_files.get('png')
        elif format.lower() == 'json':
            filename = output_files.get('json')
        else:
            raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")
        
        if not filename:
            raise HTTPException(status_code=404, detail=f"未找到{format}格式的输出文件")
        
        file_path = task_dir / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"下载文件失败: {str(e)}"
        )

@router.get("/gnah/tasks/{task_id}/preview", tags=["gnah_tasks"])
async def preview_gnah_result(task_id: str):
    """预览GNAH任务结果（返回PNG图片）"""
    try:
        tasks = _scan_gnah_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task_dir = Path(task.get('output_path', ''))
        output_files = task.get('output_files', {})
        
        png_filename = output_files.get('png')
        if not png_filename:
            raise HTTPException(status_code=404, detail="未找到PNG预览文件")
        
        png_path = task_dir / png_filename
        if not png_path.exists():
            raise HTTPException(status_code=404, detail=f"PNG文件不存在: {png_filename}")
        
        return FileResponse(
            path=str(png_path),
            filename=png_filename,
            media_type='image/png'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"预览文件失败: {str(e)}"
        )
