from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
from utils.MaizeSM_EnKF import run_MaizeSM_EnKf  # type: ignore
from utils.MaizeSM_UKF import run_MaizeSM_UKF  # type: ignore
from utils.MaizeSM_pf import run_MaizeSM_PF  # type: ignore
# 兼容带有连字符的 NLS-4DVAR 文件名：动态按文件路径加载
import importlib.util as _importlib_util  # type: ignore
import types as _types  # type: ignore
_nls_mod = None
try:
    from utils.MaizeSM_NLS_4DVAR import run_MaizeSM_NLS4DVar  # type: ignore
except Exception:
    _nls_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils', 'MaizeSM_NLS-4DVAR.py')
    _spec = _importlib_util.spec_from_file_location('MaizeSM_NLS4DVAR_mod', _nls_path)
    if _spec and _spec.loader:
        _nls_mod = _importlib_util.module_from_spec(_spec)
        _spec.loader.exec_module(_nls_mod)  # type: ignore
        run_MaizeSM_NLS4DVar = getattr(_nls_mod, 'run_MaizeSM_NLS4DVar')  # type: ignore
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import configparser

router = APIRouter()

# 参数模型定义
class EnKFParameters(BaseModel):
    en_num: int = Field(default=25, description="集合成员数量，用于生成模型集合")
    err_lai_o: float = Field(default=0.01, description="观测误差协方差，控制观测数据的不确定性")
    err_lai: float = Field(default=1.28, description="模型误差协方差，控制模型预测的不确定性")

class UKFParameters(BaseModel):
    en_num: int = Field(default=1, description="集合成员数量")
    alpha: float = Field(default=4.0, description="UKF缩放参数，控制sigma点的分布范围")
    beta: float = Field(default=1.0, description="UKF先验分布参数，通常设为1")
    kappa: float = Field(default=0.0, description="UKF缩放参数，通常设为0")
    err_lai_o: float = Field(default=2.0, description="观测误差协方差")
    err_lai: float = Field(default=0.5, description="模型误差协方差")

class PFParameters(BaseModel):
    en_num: int = Field(default=40, description="粒子数量，影响滤波精度和计算复杂度")
    resample_threshold: int = Field(default=30, description="重采样阈值，当有效粒子数低于此值时触发重采样")
    noise_std: float = Field(default=0.15, description="粒子噪声标准差，控制粒子的随机扰动")

class NLS4DVarParameters(BaseModel):
    b_time_steps: int = Field(default=35, description="背景段长度（天），用于初始预报阶段长度")
    time_steps: int = Field(default=90, description="同化窗口长度（天）")
    en_num: int = Field(default=25, description="集合成员数量")
    i_max: int = Field(default=13, description="NLS迭代次数")
    R_scalar: float = Field(default=0.01, description="观测误差方差标量，构造R=I*R_scalar")
    nass: int = Field(default=1, description="同化窗口数量（循环次数）")

class ConfigFileParameters(BaseModel):
    control_file: str = Field(default="inputfile/ZZ2021.xls", description="控制文件相对路径")
    ET_model: str = Field(default="PT", description="蒸散模型，示例：PT")
    num_cores: str = Field(default="submax", description="并行核心数，示例：submax")

# 全局参数存储
current_params = {
    "EnKF": EnKFParameters(),
    "UKF": UKFParameters(),
    "PF": PFParameters(),
    "NLS4DVar": NLS4DVarParameters(),
    "ConfigFile": ConfigFileParameters()
}

# config.ini 路径
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inputfile', 'config.ini')
_INPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inputfile')

def _read_config_file(path: str = _CONFIG_PATH) -> ConfigFileParameters:
    parser = configparser.ConfigParser()
    # 使用不带 section 的简单 ini，手动包装一个默认段
    data: dict[str, str] = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        for line in lines:
            if '=' in line:
                k, v = line.split('=', 1)
                data[k.strip()] = v.strip()
    # 回落到默认值
    return ConfigFileParameters(
        control_file=data.get('control_file', ConfigFileParameters().control_file),
        ET_model=data.get('ET_model', ConfigFileParameters().ET_model),
        num_cores=data.get('num_cores', ConfigFileParameters().num_cores),
    )

def _write_config_file(cfg: ConfigFileParameters, path: str = _CONFIG_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # 写成简单的 key=value 三行，保持与现有格式兼容
    content = f"control_file={cfg.control_file}\nET_model={cfg.ET_model}\nnum_cores={cfg.num_cores}\n"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# 启动时加载 config.ini
try:
    current_params["ConfigFile"] = _read_config_file()
except Exception:
    # 读取失败则使用默认并尝试写回
    _write_config_file(current_params["ConfigFile"])

# 参数获取接口
@router.get("/parameters/EnKF", response_model=EnKFParameters, tags=["参数配置"])
async def get_EnKF_parameters():
    """获取EnKF算法当前参数配置"""
    return current_params["EnKF"]

@router.get("/parameters/UKF", response_model=UKFParameters, tags=["参数配置"])
async def get_UKF_parameters():
    """获取UKF算法当前参数配置"""
    return current_params["UKF"]

@router.get("/parameters/PF", response_model=PFParameters, tags=["参数配置"])
async def get_PF_parameters():
    """获取PF算法当前参数配置"""
    return current_params["PF"]

@router.get("/parameters/NLS4DVar", response_model=NLS4DVarParameters, tags=["参数配置"])
async def get_NLS4DVar_parameters():
    """获取NLS-4DVAR算法当前参数配置"""
    return current_params["NLS4DVar"]

@router.get("/parameters/config", response_model=ConfigFileParameters, tags=["参数配置"])
async def get_config_file_parameters():
    """获取 config.ini 当前参数配置"""
    # 以文件为准，刷新内存
    try:
        current_params["ConfigFile"] = _read_config_file()
    except Exception:
        pass
    return current_params["ConfigFile"]

@router.get("/parameters/config/control-files", tags=["参数配置"])
async def list_control_files():
    """列举可选的 control_file（位于 inputfile 目录下的 .xls/.xlsx/.csv）"""
    patterns = ["*.xls", "*.xlsx", "*.csv"]
    files: list[dict] = []
    for pat in patterns:
        for p in glob.glob(os.path.join(_INPUT_DIR, pat)):
            try:
                stat = os.stat(p)
                files.append({
                    "name": os.path.basename(p),
                    "relative_path": f"inputfile/{os.path.basename(p)}",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception:
                pass
    # 排序：按修改时间倒序
    files.sort(key=lambda x: x.get("modified", ""), reverse=True)
    return {"files": files}

# 参数更新接口
@router.put("/parameters/EnKF", response_model=EnKFParameters, tags=["参数配置"])
async def update_EnKF_parameters(params: EnKFParameters):
    """更新EnKF算法参数配置"""
    current_params["EnKF"] = params
    return current_params["EnKF"]

@router.put("/parameters/UKF", response_model=UKFParameters, tags=["参数配置"])
async def update_UKF_parameters(params: UKFParameters):
    """更新UKF算法参数配置"""
    current_params["UKF"] = params
    return current_params["UKF"]

@router.put("/parameters/PF", response_model=PFParameters, tags=["参数配置"])
async def update_PF_parameters(params: PFParameters):
    """更新PF算法参数配置"""
    current_params["PF"] = params
    return current_params["PF"]

@router.put("/parameters/NLS4DVar", response_model=NLS4DVarParameters, tags=["参数配置"])
async def update_NLS4DVar_parameters(params: NLS4DVarParameters):
    """更新NLS-4DVAR算法参数配置"""
    current_params["NLS4DVar"] = params
    return current_params["NLS4DVar"]

@router.put("/parameters/config", response_model=ConfigFileParameters, tags=["参数配置"])
async def update_config_file_parameters(params: ConfigFileParameters):
    """更新 config.ini 参数配置并持久化到文件"""
    current_params["ConfigFile"] = params
    try:
        _write_config_file(params)
    except Exception as e:
        return JSONResponse(content=jsonable_encoder({"error": str(e)}), status_code=500)
    return current_params["ConfigFile"]

@router.put("/parameters/config/control-file", tags=["参数配置"])
async def select_control_file(filename: str):
    """选择 control_file（仅允许 inputfile 目录下的文件名）并持久化"""
    # 仅接受文件名，防止路径穿越
    safe_name = os.path.basename(filename)
    candidate = os.path.join(_INPUT_DIR, safe_name)
    if not os.path.isfile(candidate):
        return JSONResponse(content=jsonable_encoder({"error": f"文件不存在: {safe_name}"}), status_code=400)
    ext = os.path.splitext(candidate)[1].lower()
    if ext not in {".xls", ".xlsx", ".csv"}:
        return JSONResponse(content=jsonable_encoder({"error": "仅支持 .xls/.xlsx/.csv 作为 control_file"}), status_code=400)
    cfg = current_params["ConfigFile"]
    cfg.control_file = f"inputfile/{safe_name}"
    current_params["ConfigFile"] = cfg
    try:
        _write_config_file(cfg)
    except Exception as e:
        return JSONResponse(content=jsonable_encoder({"error": str(e)}), status_code=500)
    return cfg

@router.get("/parameters/options", tags=["参数配置"])
async def get_options():
    """返回前端可展示的可选项：ET_model、num_cores"""
    options = {
        "ET_model": ["PT"],
        "num_cores": ["submax"]
    }
    return options

    # 预览功能已移除

# 参数说明接口
@router.get("/parameters/description", tags=["参数配置"])
async def get_parameters_description():
    """获取所有算法参数的详细说明"""
    descriptions = {
        "EnKF (集合卡尔曼滤波)": {
            "en_num": "集合成员数量：控制模型集合的大小，数量越多结果越稳定但计算量越大",
            "err_lai_o": "观测误差协方差：反映观测数据的不确定性，值越大对观测的信任度越低",
            "err_lai": "模型误差协方差：反映模型预测的不确定性，值越大对模型的信任度越低"
        },
        "UKF (无迹卡尔曼滤波)": {
            "en_num": "集合成员数量：通常设为1，因为UKF是确定性算法",
            "alpha": "缩放参数：控制sigma点的分布范围，通常设为4",
            "beta": "先验分布参数：通常设为1，用于高斯先验",
            "kappa": "缩放参数：通常设为0，用于调整sigma点分布",
            "err_lai_o": "观测误差协方差：控制观测数据的不确定性",
            "err_lai": "模型误差协方差：控制模型预测的不确定性"
        },
        "PF (粒子滤波)": {
            "en_num": "粒子数量：粒子越多精度越高但计算量越大，建议40-100",
            "resample_threshold": "重采样阈值：当有效粒子数低于此值时触发重采样，防止粒子退化",
            "noise_std": "噪声标准差：控制粒子的随机扰动，值越大探索能力越强但可能不稳定"
        },
        "NLS-4DVAR (非线性最小二乘四维变分)": {
            "b_time_steps": "背景段长度（天）：背景预报阶段的模拟天数",
            "time_steps": "同化窗口长度（天）：单个同化窗口内的模拟天数",
            "en_num": "集合成员数量：用于POD与NLS集合规模",
            "i_max": "NLS迭代次数：非线性最小二乘的迭代步数",
            "R_scalar": "观测误差方差标量：构造R=I*R_scalar",
            "nass": "同化窗口数量：同化循环次数"
        },
        "全局配置 (config.ini)": {
            "control_file": "控制文件相对路径，例如 inputfile/ZZ2021.xls 或 CSV 观测数据",
            "ET_model": "蒸散模型：当前仅开放 PT（可扩展 PM、FAO56 等）",
            "num_cores": "并行核心数：submax 表示略低于机器最大核心数以保留系统余量"
        }
    }
    return descriptions

def _clean_value(v):
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


def df_to_safe_records(df: pd.DataFrame):
    # 强制对象类型读取并逐元素清洗
    cleaned = df.applymap(_clean_value)
    return cleaned.to_dict(orient="records")


@router.post("/EnKf")
async def MaizeSM_EnKf(inputFile: UploadFile = File(...)):
    """EnKF算法接口 - 使用当前配置的参数运行算法"""
    input_dir = "./inputfile"
    output_dir = "./output"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    obs_path = os.path.join(input_dir, inputFile.filename)

    with open(obs_path, "wb") as f:
        shutil.copyfileobj(inputFile.file, f)

    try:
        # 确保最新 config.ini 已写入
        _write_config_file(current_params["ConfigFile"])
        # 使用当前配置的参数
        params = current_params["EnKF"]
        output_path = run_MaizeSM_EnKf(obs_path, params.en_num, params.err_lai_o, params.err_lai)
        csv_files = glob.glob(os.path.join(output_path, "*.csv"))
        # 排序：优先“主要输出结果汇总”再“详细输出结果”，其余在后
        def _rank(p):
            n = os.path.basename(p)
            if "主要输出结果汇总" in n:
                return (0, n)
            if "详细输出结果" in n:
                return (1, n)
            return (2, n)
        csv_files.sort(key=_rank)

        result = {"_output_dir": output_path}
        for csv_file in csv_files:
            file_name = os.path.basename(csv_file)
            try:
                df = pd.read_csv(csv_file, dtype=object, keep_default_na=True)
                result[file_name] = df_to_safe_records(df)
            except Exception as e:
                result[file_name] = {"error": str(e)}

        return JSONResponse(content=jsonable_encoder(result), status_code=200)

    except Exception as e:
        return JSONResponse(content=jsonable_encoder({"error": str(e)}), status_code=500)


@router.post("/UKF")
async def MaizeSM_UKF(inputFile: UploadFile = File(...)):
    """UKF算法接口 - 使用当前配置的参数运行算法"""
    input_dir = "./inputfile"
    output_dir = "./output"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    obs_path = os.path.join(input_dir, inputFile.filename)
    with open(obs_path, "wb") as f:
        shutil.copyfileobj(inputFile.file, f)

    try:
        _write_config_file(current_params["ConfigFile"])
        # 使用当前配置的参数
        params = current_params["UKF"]
        output_path = run_MaizeSM_UKF(obs_path, params.en_num, params.alpha, params.beta, params.kappa, params.err_lai_o, params.err_lai)
        csv_files = glob.glob(os.path.join(output_path, "*.csv"))
        def _rank(p):
            n = os.path.basename(p)
            if "主要输出结果汇总" in n:
                return (0, n)
            if "详细输出结果" in n:
                return (1, n)
            return (2, n)
        csv_files.sort(key=_rank)
        result = {"_output_dir": output_path}
        for csv_file in csv_files:
            file_name = os.path.basename(csv_file)
            try:
                df = pd.read_csv(csv_file, dtype=object, keep_default_na=True)
                result[file_name] = df_to_safe_records(df)
            except Exception as e:
                result[file_name] = {"error": str(e)}
        return JSONResponse(content=jsonable_encoder(result), status_code=200)
    except Exception as e:
        return JSONResponse(content=jsonable_encoder({"error": str(e)}), status_code=500)


@router.post("/PF")
async def MaizeSM_PF(inputFile: UploadFile = File(...)):
    """PF算法接口 - 使用当前配置的参数运行算法"""
    input_dir = "./inputfile"
    output_dir = "./output"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    obs_path = os.path.join(input_dir, inputFile.filename)
    with open(obs_path, "wb") as f:
        shutil.copyfileobj(inputFile.file, f)

    try:
        _write_config_file(current_params["ConfigFile"])
        # 使用当前配置的参数
        params = current_params["PF"]
        output_path = run_MaizeSM_PF(obs_path, params.en_num, params.resample_threshold, params.noise_std)
        csv_files = glob.glob(os.path.join(output_path, "*.csv"))
        def _rank(p):
            n = os.path.basename(p)
            if "主要输出结果汇总" in n:
                return (0, n)
            if "详细输出结果" in n:
                return (1, n)
            return (2, n)
        csv_files.sort(key=_rank)
        result = {"_output_dir": output_path}
        for csv_file in csv_files:
            file_name = os.path.basename(csv_file)
            try:
                df = pd.read_csv(csv_file, dtype=object, keep_default_na=True)
                result[file_name] = df_to_safe_records(df)
            except Exception as e:
                result[file_name] = {"error": str(e)}
        return JSONResponse(content=jsonable_encoder(result), status_code=200)
    except Exception as e:
        return JSONResponse(content=jsonable_encoder({"error": str(e)}), status_code=500)


@router.post("/NLS4DVar")
async def MaizeSM_NLS4DVar(inputFile: UploadFile = File(...)):
    """NLS-4DVAR算法接口 - 使用当前配置的参数运行算法"""
    input_dir = "./inputfile"
    output_dir = "./output"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    obs_path = os.path.join(input_dir, inputFile.filename)
    with open(obs_path, "wb") as f:
        shutil.copyfileobj(inputFile.file, f)

    try:
        _write_config_file(current_params["ConfigFile"])
        # 使用当前配置的参数
        params = current_params["NLS4DVar"]
        output_path = run_MaizeSM_NLS4DVar(
            obs_path,
            params.b_time_steps,
            params.time_steps,
            params.en_num,
            params.i_max,
            params.R_scalar,
            params.nass
        )
        csv_files = glob.glob(os.path.join(output_path, "*.csv"))
        def _rank(p):
            n = os.path.basename(p)
            if "主要输出结果汇总" in n:
                return (0, n)
            if "详细输出结果" in n:
                return (1, n)
            return (2, n)
        csv_files.sort(key=_rank)
        result = {"_output_dir": output_path}
        for csv_file in csv_files:
            file_name = os.path.basename(csv_file)
            try:
                df = pd.read_csv(csv_file, dtype=object, keep_default_na=True)
                result[file_name] = df_to_safe_records(df)
            except Exception as e:
                result[file_name] = {"error": str(e)}
        return JSONResponse(content=jsonable_encoder(result), status_code=200)
    except Exception as e:
        return JSONResponse(content=jsonable_encoder({"error": str(e)}), status_code=500)
