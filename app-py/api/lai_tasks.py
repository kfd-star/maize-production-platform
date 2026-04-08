from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import json
import shutil
from datetime import datetime
from fastapi.responses import JSONResponse, FileResponse
import glob
import numpy as np
import pandas as pd

router = APIRouter()

def _clean_value(v):
    """清理数据值，处理NaN、Infinity等无效值"""
    # None / pandas NA
    if v is None or v is pd.NA:
        return None
    # pandas Timestamp / numpy datetime64
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    if isinstance(v, np.datetime64):
        try:
            return pd.to_datetime(v).isoformat()
        except Exception:
            return None
    # strings like 'inf', 'nan', etc.
    if isinstance(v, str):
        s = v.strip()
        if s.lower() in {"nan", "na", "null", "none", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity", ""}:
            return None
        return s
    # numeric types
    if isinstance(v, (np.floating, float)):
        if np.isnan(v) or not np.isfinite(v):
            return None
        return float(v)
    if isinstance(v, (np.integer, int)):
        return int(v)
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    return v

def _clean_task_data(task_data):
    """递归清理任务数据中的无效值"""
    if isinstance(task_data, dict):
        return {k: _clean_task_data(v) for k, v in task_data.items()}
    elif isinstance(task_data, list):
        return [_clean_task_data(item) for item in task_data]
    else:
        return _clean_value(task_data)

# 任务信息模型
class LAITaskInfo(BaseModel):
    task_id: str
    algorithm: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "pending"  # pending, running, finished, failed, canceled
    progress: int = 0
    message: str = "任务已创建"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    input_file: Optional[str] = None
    output_dir: Optional[str] = None

def _scan_lai_tasks():
    """扫描lai_tasks目录中的LAI同化任务"""
    tasks_dir = "./output/lai_tasks"
    tasks = []
    
    if not os.path.exists(tasks_dir):
        return tasks
    
    # 扫描所有JSON文件
    for filename in os.listdir(tasks_dir):
        if filename.endswith('.json'):
            task_file = os.path.join(tasks_dir, filename)
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_info = json.load(f)
                
                # 清理任务数据中的无效值
                cleaned_task_info = _clean_task_data(task_info)
                tasks.append(cleaned_task_info)
            except Exception as e:
                print(f"读取任务文件失败 {task_file}: {e}")
                # 如果读取失败，尝试创建一个基本的任务信息
                try:
                    basic_task_info = {
                        "task_id": filename[:-5],  # 去掉.json后缀
                        "algorithm": "Unknown",
                        "status": "error",
                        "created_at": "1970-01-01T00:00:00",
                        "message": f"任务文件读取失败: {str(e)}",
                        "error": str(e)
                    }
                    tasks.append(basic_task_info)
                except Exception:
                    pass  # 如果连基本任务信息都创建失败，跳过这个文件
    
    # 按创建时间倒序排列
    tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return tasks

@router.get("/lai/tasks")
async def get_lai_tasks():
    """获取所有LAI同化任务列表"""
    try:
        tasks = _scan_lai_tasks()
        return JSONResponse(content={"tasks": tasks})
    except Exception as e:
        return JSONResponse(content={"error": f"获取任务列表失败: {str(e)}"}, status_code=500)

@router.get("/lai/tasks/{task_id}")
async def get_lai_task(task_id: str):
    """获取特定LAI同化任务的详细信息"""
    try:
        tasks = _scan_lai_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(content={"error": "任务不存在"}, status_code=404)
        
        # 确保任务数据已经清理
        cleaned_task = _clean_task_data(task)
        return JSONResponse(content=cleaned_task)
    except Exception as e:
        return JSONResponse(content={"error": f"获取任务详情失败: {str(e)}"}, status_code=500)

@router.delete("/lai/tasks/{task_id}")
async def delete_lai_task(task_id: str):
    """删除LAI同化任务及其相关文件"""
    try:
        tasks_dir = "./output/lai_tasks"
        task_file = os.path.join(tasks_dir, f"{task_id}.json")
        
        # 读取任务信息
        task_info = None
        if os.path.exists(task_file):
            with open(task_file, 'r', encoding='utf-8') as f:
                task_info = json.load(f)
        
        # 删除任务信息文件
        if os.path.exists(task_file):
            os.remove(task_file)
            print(f"已删除任务信息文件: {task_file}")
        
        # 删除输出文件目录
        output_dirs_to_delete = []
        
        # 检查任务信息中的output_dir字段
        if task_info and task_info.get("output_dir"):
            output_dirs_to_delete.append(task_info["output_dir"])
        
        # 检查result中的_output_dir字段
        if task_info and task_info.get("result") and task_info["result"].get("_output_dir"):
            output_dirs_to_delete.append(task_info["result"]["_output_dir"])
        
        # 删除所有找到的输出目录
        for output_dir in output_dirs_to_delete:
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
                print(f"已删除输出文件目录: {output_dir}")
        
        # 删除输入文件（如果存在）
        if task_info and task_info.get("input_file"):
            input_file = task_info["input_file"]
            if os.path.exists(input_file):
                try:
                    os.remove(input_file)
                    print(f"已删除输入文件: {input_file}")
                except Exception as e:
                    print(f"删除输入文件失败: {e}")
        
        return JSONResponse(content={"message": "任务及其相关文件已删除"})
    except Exception as e:
        return JSONResponse(content={"error": f"删除任务失败: {str(e)}"}, status_code=500)

@router.get("/lai/download/{task_id}")
async def download_lai_result(task_id: str, file_type: str = "summary"):
    """下载LAI同化任务结果文件"""
    try:
        tasks = _scan_lai_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(content={"error": "任务不存在"}, status_code=404)
        
        if task["status"] != "finished" or not task.get("result"):
            return JSONResponse(content={"error": "任务未完成或没有结果文件"}, status_code=400)
        
        # 查找结果文件目录
        output_dirs = []
        if task.get("output_dir"):
            output_dirs.append(task["output_dir"])
        if task.get("result") and task["result"].get("_output_dir"):
            output_dirs.append(task["result"]["_output_dir"])
        
        if not output_dirs:
            return JSONResponse(content={"error": "结果文件不存在"}, status_code=404)
        
        # 查找CSV文件
        csv_files = []
        for output_dir in output_dirs:
            if os.path.exists(output_dir):
                csv_files.extend(glob.glob(os.path.join(output_dir, "*.csv")))
        
        if not csv_files:
            return JSONResponse(content={"error": "没有找到结果CSV文件"}, status_code=404)
        
        # 根据file_type选择文件
        target_file = None
        if file_type == "summary":
            # 优先选择"主要输出结果汇总"文件
            for csv_file in csv_files:
                if "主要输出结果汇总" in os.path.basename(csv_file) or "汇总" in os.path.basename(csv_file):
                    target_file = csv_file
                    break
            if not target_file:
                target_file = csv_files[0]  # 如果没有找到主要文件，使用第一个
        elif file_type == "detailed":
            # 选择"详细输出结果"文件
            for csv_file in csv_files:
                if "详细输出结果" in os.path.basename(csv_file) or "详细" in os.path.basename(csv_file):
                    target_file = csv_file
                    break
            if not target_file and len(csv_files) > 1:
                target_file = csv_files[1]  # 使用第二个文件
            elif not target_file:
                target_file = csv_files[0]  # 如果没有找到详细文件，使用第一个
        else:
            target_file = csv_files[0]  # 默认使用第一个文件
        
        return FileResponse(
            path=target_file,
            filename=os.path.basename(target_file),
            media_type="text/csv"
        )
    except Exception as e:
        return JSONResponse(content={"error": f"下载失败: {str(e)}"}, status_code=500)

@router.get("/lai/tasks/{task_id}/preview")
async def preview_lai_result(task_id: str, limit: int = 100):
    """预览LAI同化任务结果（前N条记录）"""
    try:
        tasks = _scan_lai_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(content={"error": "任务不存在"}, status_code=404)
        
        if task["status"] != "finished" or not task.get("result"):
            return JSONResponse(content={"error": "任务未完成或没有结果数据"}, status_code=400)
        
        # 返回结果数据的前N条记录
        result_data = task.get("result", {})
        if "data" in result_data:
            data = result_data["data"]
            if isinstance(data, list):
                preview_data = data[:limit]
                return JSONResponse(content={"data": preview_data, "total": len(data)})
        
        return JSONResponse(content={"error": "没有可预览的数据"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": f"预览失败: {str(e)}"}, status_code=500)
