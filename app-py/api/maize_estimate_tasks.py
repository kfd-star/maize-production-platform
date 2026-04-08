"""
Maize_Yield_API1任务管理路由
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
from core.maize_estimate_config import APP_PY_OUTPUT_DIR

# 导入任务管理器（延迟导入避免循环导入）
def get_task_manager():
    from api.maize_estimate import task_manager, task_manager_lock
    return task_manager, task_manager_lock

# 可选依赖
try:
    import pandas as pd
    import geopandas as gpd
    GEO_PANDAS_AVAILABLE = True
except ImportError:
    GEO_PANDAS_AVAILABLE = False
    print("⚠️ 警告: geopandas未安装，CSV转换功能将不可用")

router = APIRouter()

def _scan_maize_estimate_tasks():
    """扫描output目录中的Maize_Yield_API1任务"""
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
                    
                    # 只返回Maize_Yield_API1的任务
                    if task_info.get('algorithm') == 'maize_estimate':
                        # 确保输出路径存在
                        geojson_file = folder / 'prediction_results.geojson'
                        if geojson_file.exists():
                            task_info['output_path'] = str(geojson_file)
                            task_info['output_dir'] = str(folder)
                            task_info['file_name'] = 'prediction_results.geojson'
                        
                        tasks.append(task_info)
                except Exception as e:
                    print(f"读取任务信息失败 {folder}: {e}")
    
    # 按创建时间倒序排列
    tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return tasks

@router.get("/maize_estimate/tasks", tags=["maize_estimate_tasks"])
async def list_maize_estimate_tasks():
    """获取所有Maize_Yield_API1任务列表"""
    try:
        tasks = _scan_maize_estimate_tasks()
        return JSONResponse(content={"tasks": tasks})
    except Exception as e:
        return JSONResponse(
            content={"error": f"获取任务列表失败: {str(e)}"},
            status_code=500
        )

@router.get("/maize_estimate/tasks/{task_id}", tags=["maize_estimate_tasks"])
async def get_maize_estimate_task(task_id: str):
    """获取特定Maize_Yield_API1任务的详细信息"""
    try:
        tasks = _scan_maize_estimate_tasks()
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
                "total_records": static_info.get("count", 0),
                "mean_yield": static_info.get("mean", 0),
                "max_yield": static_info.get("max", 0),
                "min_yield": static_info.get("min", 0)
            }
        
        return JSONResponse(content=task)
    except Exception as e:
        return JSONResponse(
            content={"error": f"获取任务详情失败: {str(e)}"},
            status_code=500
        )

@router.delete("/maize_estimate/tasks/{task_id}", tags=["maize_estimate_tasks"])
async def delete_maize_estimate_task(task_id: str):
    """删除Maize_Yield_API1任务"""
    try:
        tasks = _scan_maize_estimate_tasks()
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
            
            # 删除Flask服务的输出目录（如果存在）
            flask_output_path = task.get("flask_output_path", "")
            if flask_output_path and os.path.exists(flask_output_path):
                try:
                    shutil.rmtree(flask_output_path)
                except:
                    pass
            
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

@router.get("/maize_estimate/download/{task_id}", tags=["maize_estimate_tasks"])
async def download_maize_estimate_result(task_id: str, format: str = "geojson"):
    """下载Maize_Yield_API1任务结果文件
    
    format: geojson 或 csv
    """
    try:
        tasks = _scan_maize_estimate_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(
                content={"error": "任务不存在"},
                status_code=404
            )
        
        output_dir = Path(task["output_dir"])
        
        if format == "geojson":
            output_file = output_dir / "prediction_results.geojson"
            if not output_file.exists():
                return JSONResponse(
                    content={"error": "GeoJSON文件不存在"},
                    status_code=404
                )
            return FileResponse(
                path=str(output_file),
                filename="prediction_results.geojson",
                media_type="application/geo+json"
            )
        elif format == "csv":
            if not GEO_PANDAS_AVAILABLE:
                return JSONResponse(
                    content={"error": "geopandas未安装，无法转换CSV"},
                    status_code=500
                )
            
            # 转换GeoJSON为CSV
            geojson_file = output_dir / "prediction_results.geojson"
            if not geojson_file.exists():
                return JSONResponse(
                    content={"error": "GeoJSON文件不存在"},
                    status_code=404
                )
            
            try:
                gdf = gpd.read_file(geojson_file)
                # 移除几何列，只保留属性
                df = gdf.drop(columns=['geometry'])
                csv_file = output_dir / "yield_predictions.csv"
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                
                return FileResponse(
                    path=str(csv_file),
                    filename="yield_predictions.csv",
                    media_type="text/csv"
                )
            except Exception as e:
                return JSONResponse(
                    content={"error": f"转换CSV失败: {str(e)}"},
                    status_code=500
                )
        else:
            return JSONResponse(
                content={"error": "不支持的格式，只支持 geojson 或 csv"},
                status_code=400
            )
    except Exception as e:
        return JSONResponse(
            content={"error": f"下载文件失败: {str(e)}"},
            status_code=500
        )

@router.get("/maize_estimate/tasks/{task_id}/preview", tags=["maize_estimate_tasks"])
async def preview_maize_estimate_result(task_id: str, limit: int = 100):
    """预览Maize_Yield_API1任务结果（返回前N条记录）"""
    try:
        tasks = _scan_maize_estimate_tasks()
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return JSONResponse(
                content={"error": "任务不存在"},
                status_code=404
            )
        
        # 读取GeoJSON文件
        geojson_file = Path(task["output_dir"]) / "prediction_results.geojson"
        if not geojson_file.exists():
            return JSONResponse(
                content={"error": "结果文件不存在"},
                status_code=404
            )
        
        if not GEO_PANDAS_AVAILABLE:
            return JSONResponse(
                content={"error": "geopandas未安装，无法预览数据"},
                status_code=500
            )
        
        try:
            gdf = gpd.read_file(geojson_file)
            df = gdf.drop(columns=['geometry'])
            
            # 返回前N条记录
            preview_data = df.head(limit).to_dict(orient="records")
            
            # 计算统计信息
            yield_column = None
            for col in df.columns:
                if 'yield' in col.lower() or '产量' in col:
                    yield_column = col
                    break
            
            if yield_column is None and len(df.columns) > 0:
                yield_column = df.columns[0]
            
            summary = {}
            if yield_column:
                summary = {
                    "mean_yield": float(df[yield_column].mean()) if len(df) > 0 else 0,
                    "max_yield": float(df[yield_column].max()) if len(df) > 0 else 0,
                    "min_yield": float(df[yield_column].min()) if len(df) > 0 else 0
                }
            
            return JSONResponse(content={
                "task_id": task_id,
                "total_records": len(df),
                "preview_records": limit,
                "data": preview_data,
                "summary": summary
            })
        except Exception as e:
            return JSONResponse(
                content={"error": f"读取数据文件失败: {str(e)}"},
                status_code=500
            )
    except Exception as e:
            return JSONResponse(
                content={"error": f"预览失败: {str(e)}"},
                status_code=500
            )

@router.post("/maize_estimate/tasks/{task_id}/cancel", tags=["maize_estimate_tasks"])
async def cancel_maize_estimate_task(task_id: str):
    """取消正在运行的Maize_Yield_API1任务"""
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
