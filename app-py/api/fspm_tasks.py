from fastapi import APIRouter, UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import sys
import subprocess
import json
import shutil
import threading
import time
import socket
import re
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uuid
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter()

# 任务信息模型
class FSPMTaskInfo(BaseModel):
    task_id: str
    status: str  # pending, running, completed, failed, cancelled
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 全局任务存储
fspm_tasks: Dict[str, FSPMTaskInfo] = {}

# 任务信息存储目录
TASKS_STORAGE_DIR = "./output/fspm_tasks"

def _save_task_info(task_id: str, task_info: FSPMTaskInfo):
    """保存任务信息到文件"""
    try:
        os.makedirs(TASKS_STORAGE_DIR, exist_ok=True)
        task_file = os.path.join(TASKS_STORAGE_DIR, f"{task_id}.json")
        
        # 转换为可序列化的字典
        task_dict = {
            "task_id": task_info.task_id,
            "status": task_info.status,
            "created_at": task_info.created_at.isoformat() if task_info.created_at else None,
            "started_at": task_info.started_at.isoformat() if task_info.started_at else None,
            "completed_at": task_info.completed_at.isoformat() if task_info.completed_at else None,
            "progress": task_info.progress,
            "message": task_info.message,
            "result": task_info.result,
            "error": task_info.error
        }
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_dict, f, ensure_ascii=False, indent=2)
        
        print(f"任务信息已保存: {task_file}")
    except Exception as e:
        print(f"保存任务信息失败: {e}")

def _load_task_info(task_id: str) -> Optional[FSPMTaskInfo]:
    """从文件加载任务信息"""
    try:
        task_file = os.path.join(TASKS_STORAGE_DIR, f"{task_id}.json")
        if not os.path.exists(task_file):
            return None
        
        with open(task_file, 'r', encoding='utf-8') as f:
            task_dict = json.load(f)
        
        # 转换回FSPMTaskInfo对象
        task_info = FSPMTaskInfo(
            task_id=task_dict["task_id"],
            status=task_dict["status"],
            created_at=datetime.fromisoformat(task_dict["created_at"]) if task_dict["created_at"] else None,
            started_at=datetime.fromisoformat(task_dict["started_at"]) if task_dict["started_at"] else None,
            completed_at=datetime.fromisoformat(task_dict["completed_at"]) if task_dict["completed_at"] else None,
            progress=task_dict["progress"],
            message=task_dict["message"],
            result=task_dict["result"],
            error=task_dict["error"]
        )
        
        return task_info
    except Exception as e:
        print(f"加载任务信息失败: {e}")
        return None

def _load_all_tasks():
    """启动时加载所有历史任务"""
    try:
        if not os.path.exists(TASKS_STORAGE_DIR):
            return
        
        for filename in os.listdir(TASKS_STORAGE_DIR):
            if filename.endswith('.json'):
                task_id = filename[:-5]  # 去掉.json后缀
                task_info = _load_task_info(task_id)
                if task_info:
                    fspm_tasks[task_id] = task_info
                    print(f"已加载历史任务: {task_id}")
        
        print(f"共加载了 {len(fspm_tasks)} 个历史任务")
    except Exception as e:
        print(f"加载历史任务失败: {e}")

def _delete_task_file(task_id: str):
    """删除任务信息文件"""
    try:
        task_file = os.path.join(TASKS_STORAGE_DIR, f"{task_id}.json")
        if os.path.exists(task_file):
            os.remove(task_file)
            print(f"已删除任务信息文件: {task_file}")
    except Exception as e:
        print(f"删除任务信息文件失败: {e}")

def _update_task_status(task_id: str, **kwargs):
    """更新任务状态并自动保存到文件"""
    if task_id not in fspm_tasks:
        return
    
    task = fspm_tasks[task_id]
    
    # 如果任务已被取消，不允许更新为其他状态
    if task.status == "cancelled" and "status" in kwargs:
        if kwargs["status"] != "cancelled":
            print(f"任务 {task_id} 已被取消，忽略状态更新: {kwargs}")
            return
    
    # 更新任务属性
    for key, value in kwargs.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    # 保存到文件
    _save_task_info(task_id, task)
    print(f"任务 {task_id} 状态已更新并保存: {kwargs}")

def _update_task_message(task_id: str, message: str):
    """更新任务消息并保存到文件"""
    if task_id in fspm_tasks:
        task = fspm_tasks[task_id]
        # 如果任务已被取消，不允许更新消息
        if task.status == "cancelled":
            print(f"任务 {task_id} 已被取消，忽略消息更新: {message}")
            return
        task.message = message
        _save_task_info(task_id, task)
        print(f"任务 {task_id} 消息已更新: {message}")

def _update_task_progress(task_id: str, progress: int):
    """更新任务进度并保存到文件"""
    if task_id in fspm_tasks:
        task = fspm_tasks[task_id]
        # 如果任务已被取消，不允许更新进度
        if task.status == "cancelled":
            print(f"任务 {task_id} 已被取消，忽略进度更新: {progress}%")
            return
        task.progress = progress
        _save_task_info(task_id, task)
        print(f"任务 {task_id} 进度已更新: {progress}%")

def _run_fspm_task(task_id: str, plant_mesh_path: str, meteo_path: str, canopy_path: str, 
                  output_path: str, process_path: str, params: Dict[str, Any]):
    """在后台线程中运行FSPM任务"""
    try:
        # 更新任务状态
        _update_task_status(task_id, 
                           status="running",
                           started_at=datetime.now(),
                           message="正在启动FSPM服务器...",
                           progress=10)
        
        # 确保输出目录存在
        os.makedirs(output_path, exist_ok=True)
        os.makedirs(process_path, exist_ok=True)
        
        # 启动main.exe作为HTTP服务器
        fspm_exe_path = "../FSPM_Corn_Growth/dmb_API/000/main.exe"
        print(f"开始启动FSPM任务 {task_id}")
        print(f"FSPM可执行文件路径: {fspm_exe_path}")
        
        # 检查main.exe是否存在
        if not os.path.exists(fspm_exe_path):
            print(f"FSPM可执行文件不存在: {fspm_exe_path}")
            raise Exception(f"FSPM可执行文件不存在: {fspm_exe_path}")
        print("FSPM可执行文件存在")
        
        # 检查端口8000是否被占用
        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        
        print("检查端口8000是否被占用...")
        if is_port_in_use(8000):
            print("端口8000被占用，开始清理...")
            # 尝试清理占用8000端口的进程
            try:
                
                # 使用netstat查找占用8000端口的进程
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                
                pids_to_kill = []
                for line in lines:
                    if ':8000' in line and 'LISTENING' in line:
                        # 提取PID
                        match = re.search(r'(\d+)\s*$', line.strip())
                        if match:
                            pid = int(match.group(1))
                            pids_to_kill.append(pid)
                
                # 终止占用端口的进程
                for pid in pids_to_kill:
                    try:
                        print(f"发现占用8000端口的进程 PID: {pid}, 正在终止...")
                        subprocess.run(['taskkill', '/PID', str(pid), '/F'], check=True)
                    except subprocess.CalledProcessError:
                        print(f"无法终止进程 PID: {pid}")
                
                # 等待端口释放
                time.sleep(3)
                
                # 再次检查端口
                if is_port_in_use(8000):
                    raise Exception("端口8000仍被占用，请手动关闭占用该端口的程序")
                    
            except Exception as e:
                raise Exception(f"端口8000已被占用，清理失败: {str(e)}")
        
        # 检查main.exe是否存在
        if not os.path.exists(fspm_exe_path):
            raise Exception(f"main.exe文件不存在: {fspm_exe_path}")
        
        # 检查工作目录
        work_dir = os.path.dirname(fspm_exe_path)
        if not os.path.exists(work_dir):
            raise Exception(f"工作目录不存在: {work_dir}")
        
        _update_task_message(task_id, f"启动main.exe: {fspm_exe_path}")
        print(f"启动main.exe: {fspm_exe_path}")
        print(f"工作目录: {work_dir}")
        
        server_process = subprocess.Popen(
            [fspm_exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=work_dir  # 设置工作目录
        )
        print(f"main.exe进程已启动，PID: {server_process.pid}")
        
        # 等待服务器启动，检查是否成功启动
        _update_task_status(task_id, message="正在等待FSPM服务器启动...", progress=15)
        print("开始等待FSPM服务器启动...")
        
        # 等待服务器启动，最多等待30秒
        server_started = False
        error_details = []
        
        # 先等待5秒让main.exe完全启动
        _update_task_message(task_id, "正在等待FSPM服务器完全启动...")
        print("等待5秒让main.exe完全启动...")
        time.sleep(5)
        print("5秒等待完成，开始检查服务器状态...")
        
        # 然后每2秒检查一次，最多检查15次（30秒）
        for i in range(15):
            # 检查进程是否还在运行
            if server_process.poll() is not None:
                # 进程已退出，获取输出
                try:
                    stdout, stderr = server_process.communicate(timeout=1)
                    error_details.append(f"main.exe进程已退出，返回码: {server_process.returncode}")
                    error_details.append(f"进程输出: {stdout}")
                    error_details.append(f"进程错误: {stderr}")
                except:
                    error_details.append(f"main.exe进程已退出，返回码: {server_process.returncode}")
                break
            
            try:
                # 尝试连接服务器检查是否启动（检查run_fspm端点）
                test_response = requests.get("http://127.0.0.1:8000/run_fspm", timeout=2)
                if test_response.status_code == 200:
                    server_started = True
                    _update_task_message(task_id, "FSPM服务器启动成功")
                    break
            except Exception as e:
                error_details.append(f"尝试 {i+1}: {str(e)}")
                _update_task_message(task_id, f"正在等待FSPM服务器启动... ({i+1}/15)")
                time.sleep(2)
                continue
        
        if not server_started:
            # 获取进程输出用于调试
            try:
                stdout, stderr = server_process.communicate(timeout=3)
                error_details.append(f"进程输出: {stdout}")
                error_details.append(f"进程错误: {stderr}")
            except Exception as e:
                error_details.append(f"无法获取进程输出: {str(e)}")
            
            # 检查进程是否还在运行
            if server_process.poll() is None:
                error_details.append("main.exe进程仍在运行但无法连接")
            else:
                error_details.append(f"main.exe进程已退出，返回码: {server_process.returncode}")
            
            server_process.terminate()
            raise Exception(f"FSPM服务器启动失败或超时（等待30秒）。详细信息: {'; '.join(error_details)}")
        
        _update_task_status(task_id, message="正在执行FSPM算法...", progress=20)
        
        # 通过HTTP请求调用算法
        base_url = "http://127.0.0.1:8000/run_fspm"
        http_params = {
            "fn_plantMesh": plant_mesh_path,
            "fn_meteorological_data": meteo_path,
            "fn_canopy_PosAzimuthHeights_data": canopy_path,
            "fn_output_results": output_path,
            "path_process": process_path
        }
        
        # 添加用户修改的参数
        for key, value in params.items():
            if key not in ["fn_plantMesh", "fn_meteorological_data", "fn_canopy_PosAzimuthHeights_data", 
                          "fn_output_results", "path_process"]:
                http_params[key] = value
        
        # 发送HTTP请求
        try:
            _update_task_status(task_id, message="正在发送算法执行请求...", progress=25)
            print(f"任务 {task_id} 进度更新为25%")
            
            # 打印调试信息
            print(f"FSPM请求参数: {http_params}")
            print(f"请求URL: {base_url}")
            
            print("发送HTTP请求到main.exe...")
            _update_task_message(task_id, "正在发送HTTP请求...")
            print(f"任务 {task_id} 消息更新为: 正在发送HTTP请求...")
            
            # 使用较短的超时时间，因为main.exe会立即开始处理
            response = requests.get(base_url, params=http_params, timeout=30)  # 30秒超时
            print(f"HTTP请求完成，状态码: {response.status_code}")
            
            _update_task_status(task_id, message="HTTP请求完成，FSPM算法正在执行中...", progress=30)
            print(f"任务 {task_id} 进度更新为30%")
            
            response.raise_for_status()
            
            # 打印响应信息
            print(f"FSPM响应状态: {response.status_code}")
            print(f"FSPM响应内容: {response.text[:500]}...")  # 只打印前500个字符
            
            # 等待main.exe处理完成
            _update_task_status(task_id, message="FSPM算法正在执行中，请耐心等待...", progress=50)
            
            # 检查输出文件是否生成
            results_file = os.path.join(output_path, "results.csv")
            max_wait_time = 1800  # 最多等待30分钟
            wait_interval = 15    # 每15秒检查一次
            total_waits = max_wait_time // wait_interval
            
            print(f"开始等待FSPM算法完成，输出文件路径: {results_file}")
            algorithm_completed = False
            
            try:
                for i in range(total_waits):
                    # 检查任务是否被取消
                    if fspm_tasks[task_id].status == "cancelled":
                        print(f"任务 {task_id} 已被取消，停止等待")
                        break
                    
                    print(f"检查第 {i+1}/{total_waits} 次，进程状态: {server_process.poll()}")
                    
                    # 检查进程是否还在运行
                    if server_process.poll() is not None:
                        print(f"进程已退出，返回码: {server_process.returncode}")
                        # 进程已退出，检查是否有输出文件
                        if os.path.exists(results_file):
                            print(f"找到输出文件: {results_file}")
                            algorithm_completed = True
                        break
                    
                    # 检查输出文件是否存在
                    if os.path.exists(results_file):
                        file_size = os.path.getsize(results_file)
                        print(f"输出文件存在，大小: {file_size} 字节")
                        # 检查文件大小，确保不是空文件
                        if file_size > 0:
                            algorithm_completed = True
                            print("算法执行完成！")
                            break
                    
                    # 更新进度
                    progress = min(50 + (i * 40 // total_waits), 90)
                    _update_task_status(task_id, progress=progress, message=f"FSPM算法正在执行中... ({i+1})")
                    
                    time.sleep(wait_interval)
            except Exception as e:
                print(f"等待过程中出现异常: {e}")
                # 即使出现异常，也检查是否有输出文件
                if os.path.exists(results_file) and os.path.getsize(results_file) > 0:
                    algorithm_completed = True
                    print("异常情况下发现输出文件，标记为完成")
            
            if algorithm_completed:
                _update_task_status(task_id,
                                   status="completed",
                                   message="FSPM算法执行完成",
                                   progress=100)
                
                # 构建结果
                result = {
                    "status": "success",
                    "message": "FSPM模型运行完成",
                    "parameters": http_params,
                    "response_text": response.text,
                    "output_path": output_path,
                    "output_file": results_file,
                    "input_files": {
                        "plant_mesh_file": os.path.basename(plant_mesh_path),
                        "meteorological_file": os.path.basename(meteo_path),
                        "canopy_file": os.path.basename(canopy_path)
                    },
                    "algorithm_params": {
                        "cultivar": params.get("cultivar", "JK968"),
                        "density": params.get("density", 4000),
                        "row_distance": params.get("row_distance", 60),
                        "num_rows": params.get("num_rows", 2),
                        "plants_per_row": params.get("plants_per_row", 3),
                        "plant_azimuth_range": params.get("plant_azimuth_range", 15),
                        "roi_num_plants": params.get("roi_num_plants", 4),
                        "date_planting": params.get("date_planting", "2021/06/26"),
                        "date_start": params.get("date_start", "2021/06/30"),
                        "date_end": params.get("date_end", "2021/09/01"),
                        "longitude": params.get("longitude", 116.3),
                        "latitude": params.get("latitude", 39.5),
                        "double_side_facet": params.get("double_side_facet", False),
                        "canopy_recon_mode": params.get("canopy_recon_mode", "True"),
                        "use_measured_heights": params.get("use_measured_heights", "False")
                    }
                }
            else:
                _update_task_status(task_id, status="failed", message="FSPM算法执行超时", progress=100)
                raise Exception("FSPM算法执行超时，未生成输出文件")
            
            # 尝试读取输出CSV文件
            results_file = os.path.join(output_path, "results.csv")
            if os.path.exists(results_file):
                try:
                    import pandas as pd
                    df = pd.read_csv(results_file)
                    result["data"] = df.to_dict(orient="records")
                    result["data_summary"] = {
                        "total_days": len(df),
                        "date_range": f"{df['date'].iloc[0]} 到 {df['date'].iloc[-1]}" if len(df) > 0 else "无数据",
                        "max_height": float(df['height(cm)'].max()) if len(df) > 0 else 0,
                        "max_npp": float(df['NPP(g/plant)'].max()) if len(df) > 0 else 0,
                        "avg_npp": float(df['NPP(g/plant)'].mean()) if len(df) > 0 else 0
                    }
                except Exception as e:
                    result["data_error"] = f"读取结果文件失败: {str(e)}"
            
            fspm_tasks[task_id].result = result
            _save_task_info(task_id, fspm_tasks[task_id])
            
        except requests.exceptions.Timeout as e:
            print(f"HTTP请求超时: {e}")
            print("HTTP请求超时，但main.exe可能仍在处理，继续等待输出文件...")
            _update_task_status(task_id, message="HTTP请求超时，但算法可能仍在执行中...", progress=30)
            print(f"任务 {task_id} 消息更新为: HTTP请求超时，但算法可能仍在执行中...")
            
            # 继续等待输出文件，不标记为失败
            results_file = os.path.join(output_path, "results.csv")
            max_wait_time = 1800  # 最多等待30分钟
            wait_interval = 15    # 每15秒检查一次
            total_waits = max_wait_time // wait_interval
            
            print(f"开始等待FSPM算法完成，输出文件路径: {results_file}")
            algorithm_completed = False
            
            try:
                for i in range(total_waits):
                    # 检查任务是否被取消
                    if fspm_tasks[task_id].status == "cancelled":
                        print(f"任务 {task_id} 已被取消，停止等待")
                        break
                    
                    print(f"检查第 {i+1}/{total_waits} 次，进程状态: {server_process.poll()}")
                    
                    # 检查进程是否还在运行
                    if server_process.poll() is not None:
                        print(f"进程已退出，返回码: {server_process.returncode}")
                        # 进程已退出，检查是否有输出文件
                        if os.path.exists(results_file):
                            print(f"找到输出文件: {results_file}")
                            algorithm_completed = True
                        break
                    
                    # 检查输出文件是否存在
                    if os.path.exists(results_file):
                        file_size = os.path.getsize(results_file)
                        print(f"输出文件存在，大小: {file_size} 字节")
                        # 检查文件大小，确保不是空文件
                        if file_size > 0:
                            algorithm_completed = True
                            print("算法执行完成！")
                            break
                    
                    # 更新进度
                    progress = min(30 + (i * 60 // total_waits), 90)
                    _update_task_status(task_id, progress=progress, message=f"FSPM算法正在执行中... ({i+1})")
                    
                    time.sleep(wait_interval)
            except Exception as e2:
                print(f"等待过程中出现异常: {e2}")
                # 即使出现异常，也检查是否有输出文件
                if os.path.exists(results_file) and os.path.getsize(results_file) > 0:
                    algorithm_completed = True
                    print("异常情况下发现输出文件，标记为完成")
            
            if algorithm_completed:
                _update_task_status(task_id, status="completed", message="FSPM算法执行完成", progress=100)
                print(f"任务 {task_id} 标记为完成: 发现输出文件")
                
                # 构建结果数据
                result = {
                    "status": "success",
                    "message": "FSPM模型运行完成",
                    "parameters": http_params,
                    "response_text": "HTTP请求超时，但算法执行成功",
                    "output_path": output_path,
                    "output_file": results_file,
                    "input_files": {
                        "plant_mesh_file": os.path.basename(plant_mesh_path),
                        "meteorological_file": os.path.basename(meteo_path),
                        "canopy_file": os.path.basename(canopy_path)
                    },
                    "algorithm_params": {
                        "cultivar": params.get("cultivar", "JK968"),
                        "density": params.get("density", 4000),
                        "row_distance": params.get("row_distance", 60),
                        "num_rows": params.get("num_rows", 2),
                        "plants_per_row": params.get("plants_per_row", 3),
                        "plant_azimuth_range": params.get("plant_azimuth_range", 15),
                        "roi_num_plants": params.get("roi_num_plants", 4),
                        "date_planting": params.get("date_planting", "2021/06/26"),
                        "date_start": params.get("date_start", "2021/06/30"),
                        "date_end": params.get("date_end", "2021/09/01"),
                        "longitude": params.get("longitude", 116.3),
                        "latitude": params.get("latitude", 39.5),
                        "double_side_facet": params.get("double_side_facet", False),
                        "canopy_recon_mode": params.get("canopy_recon_mode", "True"),
                        "use_measured_heights": params.get("use_measured_heights", "False")
                    }
                }
                
                # 尝试读取输出CSV文件
                if os.path.exists(results_file):
                    try:
                        import pandas as pd
                        df = pd.read_csv(results_file)
                        result["data"] = df.to_dict(orient="records")
                        result["data_summary"] = {
                            "total_days": len(df),
                            "date_range": f"{df['date'].iloc[0]} 到 {df['date'].iloc[-1]}" if len(df) > 0 else "无数据",
                            "max_height": float(df['height(cm)'].max()) if len(df) > 0 else 0,
                            "max_npp": float(df['NPP(g/plant)'].max()) if len(df) > 0 else 0,
                            "avg_npp": float(df['NPP(g/plant)'].mean()) if len(df) > 0 else 0
                        }
                    except Exception as e:
                        result["data_error"] = f"读取结果文件失败: {str(e)}"
                
                fspm_tasks[task_id].result = result
                _save_task_info(task_id, fspm_tasks[task_id])
                print(f"任务 {task_id} 结果数据已保存")
            else:
                _update_task_status(task_id, status="failed", message="FSPM算法执行超时", progress=100)
                print(f"任务 {task_id} 标记为失败: FSPM算法执行超时")
        except requests.exceptions.ConnectionError as e:
            print(f"HTTP连接错误: {e}")
            # 检查任务是否被取消
            if fspm_tasks[task_id].status == "cancelled":
                print(f"任务 {task_id} 已被取消，不标记为失败")
                return
            _update_task_status(task_id, status="failed", message=f"HTTP连接错误: {str(e)}", progress=0)
            print(f"任务 {task_id} 标记为失败: HTTP连接错误")
        except requests.exceptions.RequestException as e:
            print(f"HTTP请求失败: {e}")
            # 检查任务是否被取消
            if fspm_tasks[task_id].status == "cancelled":
                print(f"任务 {task_id} 已被取消，不标记为失败")
                return
            _update_task_status(task_id, status="failed", message=f"HTTP请求失败: {str(e)}", progress=0)
            print(f"任务 {task_id} 标记为失败: HTTP请求失败")
        except Exception as e:
            print(f"FSPM执行异常: {e}")
            print(f"异常类型: {type(e).__name__}")
            import traceback
            print(f"异常堆栈: {traceback.format_exc()}")
            
            # 检查任务是否被取消
            if fspm_tasks[task_id].status == "cancelled":
                print(f"任务 {task_id} 已被取消，不标记为失败")
                return
            
            # 即使出现异常，也检查是否有输出文件
            try:
                results_file = os.path.join(output_path, "results.csv")
                if os.path.exists(results_file) and os.path.getsize(results_file) > 0:
                    print("异常情况下发现输出文件，标记为完成")
                    _update_task_status(task_id, status="completed", message="FSPM算法执行完成", progress=100)
                    print(f"任务 {task_id} 标记为完成: 发现输出文件")
                else:
                    _update_task_status(task_id, status="failed", message=f"执行失败: {str(e)}", progress=0)
                    print(f"任务 {task_id} 标记为失败: {str(e)}")
            except Exception as e2:
                print(f"检查输出文件时出现异常: {e2}")
                _update_task_status(task_id, status="failed", message=f"执行失败: {str(e)}", progress=0)
                print(f"任务 {task_id} 标记为失败: {str(e)}")
        finally:
            # 关闭服务器进程
            try:
                if server_process.poll() is None:  # 进程仍在运行
                    fspm_tasks[task_id].message = "正在关闭FSPM服务器..."
                    print(f"任务 {task_id} 正在关闭FSPM服务器...")
                    server_process.terminate()
                    try:
                        server_process.wait(timeout=5)
                        fspm_tasks[task_id].message = "FSPM服务器已关闭"
                        print(f"任务 {task_id} FSPM服务器已关闭")
                    except subprocess.TimeoutExpired:
                        # 如果5秒内没有关闭，强制杀死
                        server_process.kill()
                        server_process.wait()
                        fspm_tasks[task_id].message = "FSPM服务器已强制关闭"
                        print(f"任务 {task_id} FSPM服务器已强制关闭")
            except Exception as e:
                print(f"关闭FSPM服务器时出错: {e}")
                try:
                    server_process.kill()
                    fspm_tasks[task_id].message = "FSPM服务器已关闭"
                except:
                    fspm_tasks[task_id].message = "FSPM服务器关闭异常"
            
            # 确保任务状态正确设置
            if fspm_tasks[task_id].status != "completed" and fspm_tasks[task_id].status != "failed":
                # 检查是否有输出文件来判断是否成功
                results_file = os.path.join(output_path, "results.csv")
                if os.path.exists(results_file) and os.path.getsize(results_file) > 0:
                    _update_task_status(task_id, status="completed", message="FSPM算法执行完成", progress=100)
                else:
                    _update_task_status(task_id, status="failed", message="FSPM算法执行失败", progress=0)
        
        fspm_tasks[task_id].completed_at = datetime.now()
        _save_task_info(task_id, fspm_tasks[task_id])
        
    except Exception as e:
        _update_task_status(task_id, status="failed", message="FSPM算法执行异常", error=str(e))
        fspm_tasks[task_id].completed_at = datetime.now()
        _save_task_info(task_id, fspm_tasks[task_id])

@router.post("/fspm/start")
async def start_fspm_task(
    plant_mesh_file: UploadFile = File(...),
    meteorological_file: UploadFile = File(...),
    canopy_file: UploadFile = File(...)
):
    """启动FSPM任务"""
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务信息
        task_info = FSPMTaskInfo(
            task_id=task_id,
            status="pending",
            created_at=datetime.now(),
            message="任务已创建，等待执行..."
        )
        fspm_tasks[task_id] = task_info
        
        # 保存任务信息到文件
        _save_task_info(task_id, task_info)
        
        # 创建临时目录存储上传的文件
        temp_dir = f"./temp/fspm/{task_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存上传的文件
        plant_mesh_path = os.path.abspath(os.path.join(temp_dir, plant_mesh_file.filename))
        meteo_path = os.path.abspath(os.path.join(temp_dir, meteorological_file.filename))
        canopy_path = os.path.abspath(os.path.join(temp_dir, canopy_file.filename))
        
        with open(plant_mesh_path, "wb") as f:
            shutil.copyfileobj(plant_mesh_file.file, f)
        
        with open(meteo_path, "wb") as f:
            shutil.copyfileobj(meteorological_file.file, f)
        
        with open(canopy_path, "wb") as f:
            shutil.copyfileobj(canopy_file.file, f)
        
        # 生成输出路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.abspath(os.path.join("./output/fspm", f"{task_id}_{timestamp}"))
        os.makedirs(output_path, exist_ok=True)
        process_path = os.path.abspath(os.path.join(output_path, "ProcessFiles"))
        os.makedirs(process_path, exist_ok=True)
        
        # 获取当前参数（现在直接读取paras.json文件）
        from api.fspm_parameters import _load_parameters
        params = _load_parameters()
        
        # 更新paras.json文件中的文件路径
        paras_file_path = os.path.abspath("../FSPM_Corn_Growth/dmb_API/000/config/paras.json")
        try:
            # 读取现有的paras.json文件
            if os.path.exists(paras_file_path):
                with open(paras_file_path, "r", encoding="utf-8") as f:
                    paras_data = json.load(f)
            else:
                paras_data = {}
            
            # 只更新文件路径，参数已经在用户保存时更新了
            paras_data.update({
                "fn_plantMesh": plant_mesh_path,
                "fn_meteorological_data": meteo_path,
                "fn_canopy_PosAzimuthHeights_data": canopy_path,
                "path_process": process_path,
                "fn_output_results": os.path.join(output_path, "results.csv")
            })
            
            # 保存更新后的paras.json
            with open(paras_file_path, "w", encoding="utf-8") as f:
                json.dump(paras_data, f, indent=4, ensure_ascii=False)
            
            print(f"已更新FSPM文件路径: {paras_file_path}")
            
        except Exception as e:
            print(f"更新FSPM文件路径失败: {e}")
            # 继续执行，使用默认参数
        
        # 在后台线程中启动任务
        thread = threading.Thread(
            target=_run_fspm_task,
            args=(task_id, plant_mesh_path, meteo_path, canopy_path, output_path, process_path, params)
        )
        thread.daemon = True
        thread.start()
        
        return JSONResponse(content={
            "task_id": task_id,
            "message": "FSPM任务已启动",
            "status": "pending"
        })
        
    except Exception as e:
        return JSONResponse(content={"error": f"启动任务失败: {str(e)}"}, status_code=500)

@router.get("/fspm/status/{task_id}")
async def get_fspm_task_status(task_id: str):
    """获取FSPM任务状态"""
    if task_id not in fspm_tasks:
        return JSONResponse(content={"error": "任务不存在"}, status_code=404)
    
    task = fspm_tasks[task_id]
    task_dict = {
        "task_id": task.task_id,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "progress": task.progress,
        "message": task.message,
        "result": task.result,
        "error": task.error
    }
    
    return JSONResponse(content=task_dict)

@router.post("/fspm/cancel/{task_id}")
async def cancel_fspm_task(task_id: str):
    """取消FSPM任务"""
    if task_id not in fspm_tasks:
        return JSONResponse(content={"error": "任务不存在"}, status_code=404)
    
    task = fspm_tasks[task_id]
    
    # 如果任务已完成，无法取消
    if task.status == "completed":
        return JSONResponse(content={"message": "任务已完成，无法取消"}, status_code=400)
    
    # 如果任务已经取消，直接返回
    if task.status == "cancelled":
        return JSONResponse(content={"message": "任务已经取消"})
    
    # 立即更新任务状态为取消（无论当前状态是什么）
    task.status = "cancelled"
    task.message = "用户已取消"
    task.completed_at = datetime.now()
    print(f"任务 {task_id} 立即标记为已取消")
    
    # 尝试终止main.exe进程
    try:
        # 查找并终止占用8000端口的进程
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        pids_to_kill = []
        for line in lines:
            if ':8000' in line and 'LISTENING' in line:
                # 提取PID
                match = re.search(r'(\d+)\s*$', line.strip())
                if match:
                    pid = int(match.group(1))
                    pids_to_kill.append(pid)
        
        # 终止占用端口的进程
        for pid in pids_to_kill:
            try:
                print(f"取消任务时终止进程 PID: {pid}")
                subprocess.run(['taskkill', '/PID', str(pid), '/F'], check=True)
            except subprocess.CalledProcessError:
                print(f"无法终止进程 PID: {pid}")
        
        task.message = "用户已取消，FSPM服务器已关闭"
        print(f"任务 {task_id} 消息更新为: 用户已取消，FSPM服务器已关闭")
    except Exception as e:
        print(f"取消任务时终止进程失败: {e}")
        task.message = "用户已取消，但FSPM服务器可能仍在运行"
        print(f"任务 {task_id} 消息更新为: 用户已取消，但FSPM服务器可能仍在运行")
    
    return JSONResponse(content={"message": "任务已取消"})

@router.get("/fspm/tasks")
async def list_fspm_tasks():
    """获取所有FSPM任务列表"""
    tasks = []
    for task_id, task in fspm_tasks.items():
        tasks.append({
            "task_id": task_id,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "progress": task.progress,
            "message": task.message
        })
    
    # 按创建时间倒序排列
    tasks.sort(key=lambda x: x["created_at"] or "", reverse=True)
    
    return JSONResponse(content={"tasks": tasks})

@router.delete("/fspm/tasks/{task_id}")
async def delete_fspm_task(task_id: str):
    """删除FSPM任务及其相关文件"""
    if task_id not in fspm_tasks:
        return JSONResponse(content={"error": "任务不存在"}, status_code=404)
    
    task = fspm_tasks[task_id]
    
    # 如果任务正在运行，先取消
    if task.status == "running":
        await cancel_fspm_task(task_id)
    
    # 删除相关文件
    try:
        # 删除临时文件目录
        temp_dir = f"./temp/fspm/{task_id}"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"已删除临时文件目录: {temp_dir}")
        
        # 删除输出文件目录
        if task.result and "output_path" in task.result:
            output_path = task.result["output_path"]
            if os.path.exists(output_path):
                shutil.rmtree(output_path)
                print(f"已删除输出文件目录: {output_path}")
        
        # 如果没有result信息，尝试通过任务ID查找输出目录
        if not (task.result and "output_path" in task.result):
            # 查找以task_id开头的输出目录
            output_base_dir = "./output/fspm"
            if os.path.exists(output_base_dir):
                for folder in os.listdir(output_base_dir):
                    if folder.startswith(task_id):
                        folder_path = os.path.join(output_base_dir, folder)
                        if os.path.isdir(folder_path):
                            shutil.rmtree(folder_path)
                            print(f"已删除输出文件目录: {folder_path}")
                            break
        
    except Exception as e:
        print(f"删除文件时出错: {e}")
        # 即使文件删除失败，也继续删除任务记录
    
    # 删除任务记录
    del fspm_tasks[task_id]
    
    # 删除任务信息文件
    _delete_task_file(task_id)
    
    return JSONResponse(content={"message": "任务及其相关文件已删除"})

@router.get("/fspm/download/{task_id}")
async def download_fspm_result(task_id: str):
    """下载FSPM任务结果文件"""
    if task_id not in fspm_tasks:
        return JSONResponse(content={"error": "任务不存在"}, status_code=404)
    
    task = fspm_tasks[task_id]
    
    if task.status != "completed" or not task.result:
        return JSONResponse(content={"error": "任务未完成或没有结果文件"}, status_code=400)
    
    output_file = task.result.get("output_file")
    if not output_file or not os.path.exists(output_file):
        return JSONResponse(content={"error": "结果文件不存在"}, status_code=404)
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=output_file,
        filename=f"results_{task_id}.csv",
        media_type="text/csv"
    )

@router.get("/fspm/download/process/{task_id}")
async def download_fspm_process_files(task_id: str):
    """下载FSPM任务ProcessFiles文件夹"""
    if task_id not in fspm_tasks:
        return JSONResponse(content={"error": "任务不存在"}, status_code=404)
    
    task = fspm_tasks[task_id]
    
    if task.status != "completed" or not task.result:
        return JSONResponse(content={"error": "任务未完成或没有结果文件"}, status_code=400)
    
    # 从任务结果中获取ProcessFiles路径
    process_path = None
    if task.result.get("parameters"):
        process_path = task.result["parameters"].get("path_process")
    
    if not process_path or not os.path.exists(process_path):
        return JSONResponse(content={"error": "ProcessFiles文件夹不存在"}, status_code=404)
    
    try:
        import zipfile
        
        # 在ProcessFiles同一目录下创建压缩包
        zip_filename = f"ProcessFiles_{task_id}.zip"
        zip_path = os.path.join(os.path.dirname(process_path), zip_filename)
        
        # 检查是否已经存在压缩包
        if os.path.exists(zip_path):
            print(f"使用已存在的压缩包: {zip_path}")
        else:
            print(f"创建新的压缩包: {zip_path}")
            # 压缩ProcessFiles文件夹
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 检查ProcessFiles文件夹中是否有文件
                file_count = 0
                for root, dirs, files in os.walk(process_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算相对路径，确保在zip中的路径结构正确
                        arcname = os.path.relpath(file_path, os.path.dirname(process_path))
                        zipf.write(file_path, arcname)
                        file_count += 1
                        print(f"添加文件到压缩包: {arcname}")
                
                if file_count == 0:
                    print("警告: ProcessFiles文件夹为空")
                else:
                    print(f"成功压缩 {file_count} 个文件到 {zip_path}")
        
        # 检查压缩包大小
        zip_size = os.path.getsize(zip_path)
        print(f"压缩包大小: {zip_size} 字节")
        
        if zip_size == 0:
            return JSONResponse(content={"error": "压缩包为空，ProcessFiles文件夹可能没有文件"}, status_code=500)
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "Content-Length": str(zip_size),
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        print(f"压缩ProcessFiles文件夹失败: {str(e)}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return JSONResponse(content={"error": f"压缩ProcessFiles文件夹失败: {str(e)}"}, status_code=500)

@router.post("/fspm/cleanup")
async def cleanup_fspm_ports():
    """清理占用8000端口的进程"""
    try:
        
        # 使用netstat查找占用8000端口的进程
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        pids_to_kill = []
        for line in lines:
            if ':8000' in line and 'LISTENING' in line:
                # 提取PID
                match = re.search(r'(\d+)\s*$', line.strip())
                if match:
                    pid = int(match.group(1))
                    pids_to_kill.append(pid)
        
        killed_processes = []
        for pid in pids_to_kill:
            try:
                subprocess.run(['taskkill', '/PID', str(pid), '/F'], check=True)
                killed_processes.append(pid)
            except subprocess.CalledProcessError:
                pass
        
        return JSONResponse(content={
            "message": f"清理完成，终止了 {len(killed_processes)} 个进程",
            "killed_pids": killed_processes
        })
        
    except Exception as e:
        return JSONResponse(content={"error": f"清理失败: {str(e)}"}, status_code=500)

# 模块加载时自动加载历史任务
_load_all_tasks()