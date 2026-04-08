from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import json
import shutil
from datetime import datetime
from fastapi.responses import JSONResponse, FileResponse
import glob

router = APIRouter()

# 任务信息模型
class MaizeYieldTaskInfo(BaseModel):
    task_id: str
    created_at: str
    output_path: str
    output_dir: str
    file_name: str
    status: str = "completed"  # completed, failed
    message: str = "预测完成"

def _scan_maize_yield_tasks():
    """扫描output目录中的玉米产量预测任务"""
    # 修复路径：应该扫描 utils/output 而不是 output
    utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils")
    output_dir = os.path.join(utils_dir, "output")
    tasks = []
    
    if not os.path.exists(output_dir):
        return tasks
    
    # 扫描所有以UUID格式开头的文件夹
    for folder in os.listdir(output_dir):
        folder_path = os.path.join(output_dir, folder)
        if os.path.isdir(folder_path) and '_' in folder:
            # 检查是否是玉米产量预测任务（包含yield_predictions.csv文件）
            csv_file = os.path.join(folder_path, "yield_predictions.csv")
            task_info_file = os.path.join(folder_path, "task_info.json")
            if os.path.exists(csv_file):
                task_info = {
                    "task_id": folder.split('_')[0],
                    "created_at": folder.split('_')[1] + '_' + folder.split('_')[2] if len(folder.split('_')) >= 3 else "",
                    "output_path": csv_file,
                    "output_dir": folder_path,
                    "file_name": "yield_predictions.csv",
                    "status": "completed",
                    "message": "预测完成"
                }
                
                # 如果存在task_info.json文件，读取其中的信息
                if os.path.exists(task_info_file):
                    try:
                        with open(task_info_file, 'r', encoding='utf-8') as f:
                            saved_info = json.load(f)
                            task_info.update(saved_info)
                    except Exception as e:
                        print(f"读取任务信息文件失败: {e}")
                
                tasks.append(task_info)
    
    # 按创建时间倒序排列
    tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return tasks

@router.get("/maize_yield/tasks")
async def list_maize_yield_tasks():
    """获取所有玉米产量预测任务列表"""
    try:
        tasks = _scan_maize_yield_tasks()
        return JSONResponse(content={"tasks": tasks})
    except Exception as e:
        return JSONResponse(content={"error": f"获取任务列表失败: {str(e)}"}, status_code=500)

@router.get("/maize_yield/tasks/{task_id}")
async def get_maize_yield_task(task_id: str):
    """获取特定玉米产量预测任务的详细信息"""
    try:
        tasks = _scan_maize_yield_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(content={"error": "任务不存在"}, status_code=404)
        
        # 使用task_info.json中的统计信息，不再读取CSV文件计算
        if "static_info" in task:
            try:
                import json
                # static_info 现在已经是对象，不需要解析
                static_info = task["static_info"]
                if isinstance(static_info, str):
                    static_info = json.loads(static_info)
                
                task["data_summary"] = {
                    "total_records": static_info.get("count", 0),
                    "mean_yield": static_info.get("mean", 0),
                    "max_yield": static_info.get("max", 0),
                    "min_yield": static_info.get("min", 0)
                }
            except Exception as e:
                task["data_error"] = f"解析统计信息失败: {str(e)}"
        else:
            task["data_error"] = "任务信息中缺少统计信息"
        
        return JSONResponse(content=task)
    except Exception as e:
        return JSONResponse(content={"error": f"获取任务详情失败: {str(e)}"}, status_code=500)

@router.delete("/maize_yield/tasks/{task_id}")
async def delete_maize_yield_task(task_id: str):
    """删除玉米产量预测任务"""
    try:
        tasks = _scan_maize_yield_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(content={"error": "任务不存在"}, status_code=404)
        
        # 删除任务文件夹
        output_dir = task["output_dir"]
        deleted_items = []
        
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            deleted_items.append(f"输出目录: {output_dir}")
        
        # 删除临时文件目录
        if "temp_dirs" in task:
            for temp_dir in task["temp_dirs"]:
                try:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                        deleted_items.append(f"临时目录: {temp_dir}")
                    else:
                        print(f"临时目录不存在: {temp_dir}")
                except Exception as e:
                    print(f"删除临时目录失败 {temp_dir}: {str(e)}")
                    # 继续处理其他目录，不中断整个删除过程
        
        if deleted_items:
            return JSONResponse(content={"message": f"任务已删除，清理了 {len(deleted_items)} 个目录"})
        else:
            return JSONResponse(content={"error": "任务文件夹不存在"}, status_code=404)
            
    except Exception as e:
        return JSONResponse(content={"error": f"删除任务失败: {str(e)}"}, status_code=500)

@router.get("/maize_yield/download/{task_id}")
async def download_maize_yield_result(task_id: str):
    """下载玉米产量预测任务结果文件"""
    try:
        tasks = _scan_maize_yield_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(content={"error": "任务不存在"}, status_code=404)
        
        output_file = task["output_path"]
        if not os.path.exists(output_file):
            return JSONResponse(content={"error": "结果文件不存在"}, status_code=404)
        
        return FileResponse(
            path=output_file,
            filename="yield_predictions.csv",
            media_type="text/csv"
        )
    except Exception as e:
        return JSONResponse(content={"error": f"下载文件失败: {str(e)}"}, status_code=500)

@router.get("/maize_yield/tasks/{task_id}/preview")
async def preview_maize_yield_result(task_id: str, limit: int = 100):
    """预览玉米产量预测任务结果（返回前N条记录）"""
    try:
        tasks = _scan_maize_yield_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(content={"error": "任务不存在"}, status_code=404)
        
        # 读取CSV文件内容
        try:
            import pandas as pd
            df = pd.read_csv(task["output_path"])
            
            # 返回前N条记录
            preview_data = df.head(limit).to_dict(orient="records")
            
            return JSONResponse(content={
                "task_id": task_id,
                "total_records": len(df),
                "preview_records": limit,
                "data": preview_data,
                "summary": {
                    "mean_yield": float(df.iloc[:, 0].mean()) if len(df) > 0 else 0,
                    "max_yield": float(df.iloc[:, 0].max()) if len(df) > 0 else 0,
                    "min_yield": float(df.iloc[:, 0].min()) if len(df) > 0 else 0
                }
            })
        except Exception as e:
            return JSONResponse(content={"error": f"读取数据文件失败: {str(e)}"}, status_code=500)
            
    except Exception as e:
        return JSONResponse(content={"error": f"预览数据失败: {str(e)}"}, status_code=500)
