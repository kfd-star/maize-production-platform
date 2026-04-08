from __future__ import annotations

import os
import shutil
import uuid
import threading
import traceback
from datetime import datetime
from typing import Dict, Optional, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from multiprocessing import Queue
import subprocess
import sys
import json


router = APIRouter()


class TaskInfo:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.process: Optional[Any] = None  # subprocess.Popen
        self.status: str = "pending"  # pending|running|finished|failed|canceled
        self.created_at: str = datetime.now().isoformat(timespec="seconds")
        self.updated_at: str = self.created_at
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.queue: Optional[Queue] = None  # 不再使用，但保留字段兼容


_TASKS: Dict[str, TaskInfo] = {}
_LOCK = threading.Lock()

# 任务信息存储目录
TASKS_STORAGE_DIR = "./output/lai_tasks"

def _save_task_info_to_file(task_id: str, algorithm: str, params: dict, input_file: str):
    """保存任务信息到文件"""
    try:
        os.makedirs(TASKS_STORAGE_DIR, exist_ok=True)
        task_file = os.path.join(TASKS_STORAGE_DIR, f"{task_id}.json")
        
        task_info = {
            "task_id": task_id,
            "algorithm": algorithm,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "progress": 0,
            "message": "任务已创建，等待执行...",
            "result": None,
            "error": None,
            "parameters": params,
            "input_file": input_file,
            "output_dir": None
        }
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)
        
        print(f"任务信息已保存: {task_file}")
    except Exception as e:
        print(f"保存任务信息失败: {e}")

def _update_task_info_file(task_id: str, **kwargs):
    """更新任务信息文件"""
    try:
        task_file = os.path.join(TASKS_STORAGE_DIR, f"{task_id}.json")
        if not os.path.exists(task_file):
            return
        
        with open(task_file, 'r', encoding='utf-8') as f:
            task_info = json.load(f)
        
        # 更新字段
        for key, value in kwargs.items():
            task_info[key] = value
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)
        
        print(f"任务信息已更新: {task_file}")
    except Exception as e:
        print(f"更新任务信息失败: {e}")


def _run_worker_subprocess(algo: str, obs_path: str, params: dict = None) -> subprocess.Popen:
    """启动独立 Python 进程运行 worker_runner.py 并返回 Popen。"""
    py = sys.executable or "python"
    worker = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'worker_runner.py')
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    # 构建命令行参数
    cmd = [py, worker, algo, obs_path]
    
    # 如果有参数，序列化为JSON并传递
    if params:
        params_json = json.dumps(params)
        cmd.append(params_json)
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    return proc


def _start_consumer(task: TaskInfo):
    """在后台线程消费子进程结果，更新任务状态。"""
    def _consume():
        try:
            # 等待 worker 结束并解析输出
            out, err = task.process.communicate()
            data: Dict[str, Any]
            if task.process.returncode == 0 and out:
                try:
                    data = json.loads(out.strip())
                except Exception:
                    data = {"ok": False, "error": out}
            else:
                data = {"ok": False, "error": err or out or f"exit {task.process.returncode}"}
            with _LOCK:
                # 检查任务是否已被取消，如果已取消则不更新状态
                if task.status == "canceled":
                    print(f"任务 {task.task_id} 已被取消，跳过状态更新")
                    return
                
                task.updated_at = datetime.now().isoformat(timespec="seconds")
                if data.get("ok"):
                    task.status = "finished"
                    task.result = data.get("data")
                    # 更新任务信息文件
                    _update_task_info_file(task.task_id, 
                                         status="finished", 
                                         progress=100,
                                         message="任务执行完成",
                                         result=data.get("data"),
                                         completed_at=datetime.now().isoformat(),
                                         updated_at=task.updated_at)
                else:
                    task.status = "failed"
                    task.error = data.get("error")
                    # 更新任务信息文件
                    _update_task_info_file(task.task_id, 
                                         status="failed", 
                                         progress=0,
                                         message=f"任务执行失败: {data.get('error', '未知错误')}",
                                         error=data.get("error"),
                                         completed_at=datetime.now().isoformat(),
                                         updated_at=task.updated_at)
        except Exception as e:
            with _LOCK:
                # 检查任务是否已被取消，如果已取消则不更新状态
                if task.status == "canceled":
                    print(f"任务 {task.task_id} 已被取消，跳过异常状态更新")
                    return
                
                task.updated_at = datetime.now().isoformat(timespec="seconds")
                task.status = "failed"
                task.error = str(e)
                _update_task_info_file(task.task_id, 
                                     status="failed", 
                                     progress=0,
                                     message=f"任务执行异常: {str(e)}",
                                     error=str(e),
                                     completed_at=datetime.now().isoformat(),
                                     updated_at=task.updated_at)

    t = threading.Thread(target=_consume, daemon=True)
    t.start()


@router.post("/tasks")
async def start_task(
    algo: str = Query(..., description="算法: EnKF|UKF|PF|NLS4DVar"),
    inputFile: UploadFile = File(..., description="观测CSV文件")
):
    algo = algo.strip()
    if algo not in {"EnKF", "UKF", "PF", "NLS4DVar"}:
        raise HTTPException(status_code=400, detail="不支持的算法")

    os.makedirs("./inputfile", exist_ok=True)
    obs_path = os.path.join("./inputfile", inputFile.filename)
    with open(obs_path, "wb") as f:
        shutil.copyfileobj(inputFile.file, f)

    # 获取当前配置的参数
    from api.MaizeSM import current_params
    params = current_params.get(algo, {})
    
    # 将Pydantic模型转换为字典
    if hasattr(params, 'dict'):
        params_dict = params.dict()
    elif hasattr(params, 'model_dump'):
        params_dict = params.model_dump()
    else:
        params_dict = {}

    task_id = str(uuid.uuid4())
    # 启动独立 worker 子进程（避免 Windows 下多进程导入/包路径问题）
    proc = _run_worker_subprocess(algo, obs_path, params_dict)

    info = TaskInfo(task_id)
    info.process = proc
    info.queue = None
    info.status = "running"
    info.updated_at = datetime.now().isoformat(timespec="seconds")
    
    # 保存任务信息到文件（包含参数）
    _save_task_info_to_file(task_id, algo, params_dict, obs_path)

    with _LOCK:
        _TASKS[task_id] = info

    _start_consumer(info)

    return JSONResponse(content=jsonable_encoder({
        "task_id": task_id,
        "status": info.status,
        "created_at": info.created_at,
    }), status_code=202)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    with _LOCK:
        info = _TASKS.get(task_id)
        if not info:
            raise HTTPException(status_code=404, detail="任务不存在")
        payload = {
            "task_id": info.task_id,
            "status": info.status,
            "created_at": info.created_at,
            "updated_at": info.updated_at,
            "result": info.result,
            "error": info.error,
        }
    return JSONResponse(content=jsonable_encoder(payload), status_code=200)


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    with _LOCK:
        info = _TASKS.get(task_id)
        if not info:
            raise HTTPException(status_code=404, detail="任务不存在")
        if info.status in {"finished", "failed", "canceled"}:
            return JSONResponse(content={"task_id": task_id, "status": info.status}, status_code=200)

        proc = info.process
        if proc is not None:
            try:
                # 对于 subprocess.Popen，使用 poll() 判断是否仍在运行
                if getattr(proc, 'poll', None) is not None:
                    if proc.poll() is None:
                        try:
                            proc.terminate()
                        except Exception:
                            pass
                        # 再次检查，必要时强杀
                        try:
                            if proc.poll() is None:
                                proc.kill()
                        except Exception:
                            pass
                else:
                    # 兜底：如果是其他类型进程对象
                    if hasattr(proc, 'terminate'):
                        try:
                            proc.terminate()
                        except Exception:
                            pass
            except Exception:
                pass
        
        # 立即更新内存状态
        info.status = "canceled"
        info.updated_at = datetime.now().isoformat(timespec="seconds")
        
        # 立即更新文件状态，防止消费者线程覆盖
        _update_task_info_file(task_id, 
                             status="canceled", 
                             progress=0,
                             message="用户已取消任务",
                             completed_at=datetime.now().isoformat(),
                             updated_at=info.updated_at)

    return JSONResponse(content=jsonable_encoder({
        "task_id": task_id,
        "status": "canceled",
    }), status_code=200)


