"""
SCYM (Maize_Yield_API2/API3) 服务配置
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

# Flask 服务配置（SCYM服务）
SCYM_SERVICE = {
    'HOST': os.getenv('SCYM_HOST', '127.0.0.1'),
    'PORT': int(os.getenv('SCYM_PORT', '5000')),
    'BASE_URL': None,  # 将在初始化时设置
    'API_ENDPOINT': '/scym/runModel',
    'STATUS_ENDPOINT': '/scym/getStatus',
    'TIMEOUT': int(os.getenv('SCYM_TIMEOUT', '3600')),  # 1小时
}

# 初始化 BASE_URL
SCYM_SERVICE['BASE_URL'] = f"http://{SCYM_SERVICE['HOST']}:{SCYM_SERVICE['PORT']}"

# SCYM项目路径配置
# 假设 Maize_Yield_API2 和 app-py 在同一父目录下
APP_PY_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_PY_ROOT.parent  # 项目根目录（corn-system-server-master）

# SCYM项目路径
SCYM_ROOT = PROJECT_ROOT / 'Maize_Yield_API2' / 'Maize_Yield_API3'

# 数据路径配置
SCYM_PATHS = {
    'INPUT_S2_DIR': SCYM_ROOT / 'data' / 'input' / 'Sentinel2',
    'INPUT_ERA5_DIR': SCYM_ROOT / 'data' / 'input' / 'ERA5',
    'INPUT_MASK_DIR': SCYM_ROOT / 'data' / 'input' / '玉米分布',
    'INPUT_ROI_DIR': SCYM_ROOT / 'data' / 'input' / 'roi',
    'OUTPUT_DIR': SCYM_ROOT / 'data' / 'output',
}

# app-py 输出目录（用于保存任务结果）
APP_PY_OUTPUT_DIR = APP_PY_ROOT / 'output'

# 确保目录存在
for path in SCYM_PATHS.values():
    if isinstance(path, Path):
        path.parent.mkdir(parents=True, exist_ok=True)

APP_PY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_scym_url(endpoint: str = None) -> str:
    """获取SCYM服务的完整URL"""
    base_url = SCYM_SERVICE['BASE_URL']
    if endpoint:
        return f"{base_url}{endpoint}"
    return base_url

def validate_service_config():
    """验证服务配置"""
    errors = []
    
    # 检查路径是否存在
    if not SCYM_ROOT.exists():
        errors.append(f"SCYM 路径不存在: {SCYM_ROOT}")
    
    # 检查输入目录
    if not SCYM_PATHS['INPUT_S2_DIR'].exists():
        errors.append(f"Sentinel-2目录不存在: {SCYM_PATHS['INPUT_S2_DIR']}")
    
    if not SCYM_PATHS['INPUT_ERA5_DIR'].exists():
        errors.append(f"ERA5目录不存在: {SCYM_PATHS['INPUT_ERA5_DIR']}")
    
    return errors

# SCYM 配置参数文件路径
SCYM_CONFIG_FILE = SCYM_ROOT / 'config.py'

def get_default_scym_coefficients() -> Dict[str, float]:
    """获取默认的SCYM模型系数"""
    return {
        'constant': -648.7124,
        'tmean': 491.0432,
        'tmean2': -11.9421,
        'rain': 5.1636,
        'rain2': -0.0032,
        'base_value': 1424.7642,
        'gcvi_constant': -5.1387,
        'gcvi_tmean': -0.1163,
        'gcvi_tmean2': 0.0035,
        'gcvi_rain': -0.0025,
        'gcvi_rain2': 0.00000175,
        'gcvi_multiplier': 1197.3193
    }

def get_default_algorithm_config() -> Dict[str, Any]:
    """获取默认的算法配置"""
    return {
        'yield_output_prefix': 'test_Cropland_Yield_2025'
    }

def read_scym_config_from_file() -> Dict[str, Any]:
    """从SCYM的config.py文件读取配置参数"""
    try:
        # 动态导入SCYM的config模块
        import sys
        config_path = str(SCYM_CONFIG_FILE.parent)
        if config_path not in sys.path:
            sys.path.insert(0, config_path)
        
        # 导入SCYM的config模块
        import importlib.util
        spec = importlib.util.spec_from_file_location("scym_config_module", SCYM_CONFIG_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载SCYM配置文件: {SCYM_CONFIG_FILE}")
        
        scym_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scym_config)
        
        # 读取配置
        coefficients = getattr(scym_config, 'SCYM_COEFFICIENTS', get_default_scym_coefficients())
        algorithm_config = getattr(scym_config, 'ALGORITHM_CONFIG', get_default_algorithm_config())
        
        return {
            'coefficients': coefficients,
            'algorithm_config': algorithm_config
        }
    except Exception as e:
        print(f"读取SCYM配置文件失败: {e}")
        # 返回默认值
        return {
            'coefficients': get_default_scym_coefficients(),
            'algorithm_config': get_default_algorithm_config()
        }

def update_scym_config_file(coefficients: Dict[str, float] = None, algorithm_config: Dict[str, Any] = None):
    """更新SCYM的config.py文件中的配置参数"""
    try:
        # 读取现有配置
        current_config = read_scym_config_from_file()
        
        # 更新配置
        if coefficients is not None:
            current_config['coefficients'].update(coefficients)
        if algorithm_config is not None:
            current_config['algorithm_config'].update(algorithm_config)
        
        # 读取config.py文件内容
        if not SCYM_CONFIG_FILE.exists():
            raise FileNotFoundError(f"SCYM配置文件不存在: {SCYM_CONFIG_FILE}")
        
        with open(SCYM_CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新SCYM_COEFFICIENTS
        if coefficients is not None:
            # 构建新的SCYM_COEFFICIENTS字典字符串
            coeff_str = "SCYM_COEFFICIENTS = {\n"
            for key, value in current_config['coefficients'].items():
                coeff_str += f"    '{key}': {value},\n"
            coeff_str += "}\n"
            
            # 替换SCYM_COEFFICIENTS部分（匹配多行字典）
            import re
            # 匹配从 SCYM_COEFFICIENTS = { 到对应的 } 之间的所有内容（包括换行）
            pattern = r"SCYM_COEFFICIENTS\s*=\s*\{[^}]*\}"
            # 使用更精确的模式，匹配嵌套的大括号
            lines = content.split('\n')
            new_lines = []
            in_coefficients = False
            coeff_start_idx = -1
            for i, line in enumerate(lines):
                if 'SCYM_COEFFICIENTS' in line and '=' in line:
                    in_coefficients = True
                    coeff_start_idx = i
                    # 添加新的定义
                    new_lines.append(coeff_str.rstrip())
                    continue
                if in_coefficients:
                    # 跳过旧定义的行，直到找到结束的 }
                    if line.strip() == '}':
                        in_coefficients = False
                    continue
                new_lines.append(line)
            content = '\n'.join(new_lines)
        
        # 更新ALGORITHM_CONFIG
        if algorithm_config is not None:
            # 构建新的ALGORITHM_CONFIG字典字符串
            algo_str = "ALGORITHM_CONFIG = {"
            for key, value in current_config['algorithm_config'].items():
                if isinstance(value, str):
                    algo_str += f"'{key}': '{value}', "
                else:
                    algo_str += f"'{key}': {value}, "
            algo_str = algo_str.rstrip(', ') + "}\n"
            
            # 替换ALGORITHM_CONFIG部分
            import re
            lines = content.split('\n')
            new_lines = []
            in_algorithm = False
            for i, line in enumerate(lines):
                if 'ALGORITHM_CONFIG' in line and '=' in line:
                    in_algorithm = True
                    # 添加新的定义
                    new_lines.append(algo_str.rstrip())
                    continue
                if in_algorithm:
                    # 跳过旧定义的行，直到找到结束的 }
                    if line.strip() == '}':
                        in_algorithm = False
                    continue
                new_lines.append(line)
            content = '\n'.join(new_lines)
        
        # 写回文件
        with open(SCYM_CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"更新SCYM配置文件失败: {e}")
        return False
