"""
Maize_Yield_API1服务配置
"""
import os
import re
from pathlib import Path
from typing import Dict, Any

# Flask 服务配置（Maize_Yield_API1/predict）
MAIZE_ESTIMATE_SERVICE = {
    'HOST': os.getenv('MAIZE_ESTIMATE_HOST', '127.0.0.1'),
    'PORT': int(os.getenv('MAIZE_ESTIMATE_PORT', '8006')),
    'BASE_URL': None,  # 将在初始化时设置
    'API_ENDPOINT': '/CropParamInversionService/param_inversion',
    'STATUS_ENDPOINT': '/CropParamInversionService/status',
    'TIMEOUT': int(os.getenv('MAIZE_ESTIMATE_TIMEOUT', '3600')),  # 1小时
}

# 初始化 BASE_URL
MAIZE_ESTIMATE_SERVICE['BASE_URL'] = f"http://{MAIZE_ESTIMATE_SERVICE['HOST']}:{MAIZE_ESTIMATE_SERVICE['PORT']}"

# Maize_Yield_API1 项目路径配置
# 假设 Maize_Yield_API1 和 app-py 在同一父目录下
APP_PY_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_PY_ROOT.parent  # 项目根目录（corn-system-server-master）

# Maize_Yield_API1 路径
MAIZE_YIELD_API1_ROOT = PROJECT_ROOT / 'Maize_Yield_API1' / 'predict'

# 数据路径配置
MAIZE_ESTIMATE_PATHS = {
    'INPUT_DATA_DIR': MAIZE_YIELD_API1_ROOT / 'data' / 'input' / 'data_dir_datian',
    'INPUT_SHP_DIR': MAIZE_YIELD_API1_ROOT / 'data' / 'input' / 'shp',
    'OUTPUT_DIR': MAIZE_YIELD_API1_ROOT / 'data' / 'output',
    'MODEL_DIR': MAIZE_YIELD_API1_ROOT / 'server' / 'models',
    'DEFAULT_SHP_FILE': MAIZE_YIELD_API1_ROOT / 'data' / 'input' / 'shp' / '小区.shp',
}

# app-py 输出目录（用于保存任务结果）
APP_PY_OUTPUT_DIR = APP_PY_ROOT / 'output'

# 确保目录存在
for path in MAIZE_ESTIMATE_PATHS.values():
    if isinstance(path, Path):
        path.parent.mkdir(parents=True, exist_ok=True)

APP_PY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_maize_estimate_url(endpoint: str = None) -> str:
    """获取 Flask 服务的完整 URL"""
    base_url = MAIZE_ESTIMATE_SERVICE['BASE_URL']
    if endpoint:
        return f"{base_url}{endpoint}"
    return base_url

def validate_service_config():
    """验证服务配置"""
    errors = []
    
    # 检查路径是否存在
    if not MAIZE_YIELD_API1_ROOT.exists():
        errors.append(f"Maize_Yield_API1 路径不存在: {MAIZE_YIELD_API1_ROOT}")
    
    if not MAIZE_ESTIMATE_PATHS['MODEL_DIR'].exists():
        errors.append(f"模型目录不存在: {MAIZE_ESTIMATE_PATHS['MODEL_DIR']}")
    
    # 检查模型文件
    model_file = MAIZE_ESTIMATE_PATHS['MODEL_DIR'] / 'TL-ONEYEAR425_MUS_SLB_Time_1031.sav'
    if not model_file.exists():
        errors.append(f"模型文件不存在: {model_file}")
    
    return errors

# Maize_Yield_API1 配置文件路径
MAIZE_ESTIMATE_CONFIG_FILE = MAIZE_YIELD_API1_ROOT / 'server' / 'config.py'

def get_default_maize_estimate_params() -> Dict[str, Any]:
    """获取默认的Maize_Yield_API1参数"""
    return {
        'POPULATION_SIZE': 50,
        'MAX_GENERATIONS': 100,
        'TIMEOUT': 3600,
        'API_TIMEOUT': 3600,
        'MAX_WORKERS': 4,
    }

def read_maize_estimate_config_from_file() -> Dict[str, Any]:
    """从Maize_Yield_API1的config.py文件读取配置参数"""
    try:
        # 动态导入Maize_Yield_API1的config模块
        import sys
        config_path = str(MAIZE_ESTIMATE_CONFIG_FILE.parent)
        if config_path not in sys.path:
            sys.path.insert(0, config_path)
        
        # 导入Maize_Yield_API1的config模块
        import importlib.util
        spec = importlib.util.spec_from_file_location("maize_estimate_config_module", MAIZE_ESTIMATE_CONFIG_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载Maize_Yield_API1配置文件: {MAIZE_ESTIMATE_CONFIG_FILE}")
        
        maize_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(maize_config)
        
        # 读取配置实例
        config_instance = getattr(maize_config, 'config', None)
        if config_instance is None:
            # 如果没有config实例，返回默认值
            return get_default_maize_estimate_params()
        
        # 从config实例中提取参数
        params = {
            'POPULATION_SIZE': getattr(config_instance, 'POPULATION_SIZE', 50),
            'MAX_GENERATIONS': getattr(config_instance, 'MAX_GENERATIONS', 100),
            'TIMEOUT': getattr(config_instance, 'TIMEOUT', 3600),
            'API_TIMEOUT': getattr(config_instance, 'API_TIMEOUT', 3600),
            'MAX_WORKERS': getattr(config_instance, 'MAX_WORKERS', 4),
        }
        
        return params
    except Exception as e:
        print(f"读取Maize_Yield_API1配置文件失败: {e}")
        # 返回默认值
        return get_default_maize_estimate_params()

def update_maize_estimate_config_file(params: Dict[str, Any]):
    """更新Maize_Yield_API1的config.py文件中的配置参数"""
    try:
        if not MAIZE_ESTIMATE_CONFIG_FILE.exists():
            raise FileNotFoundError(f"Maize_Yield_API1配置文件不存在: {MAIZE_ESTIMATE_CONFIG_FILE}")
        
        # 读取config.py文件内容
        with open(MAIZE_ESTIMATE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 更新每个参数
        for param_name, param_value in params.items():
            # 查找并替换参数赋值行，例如：self.POPULATION_SIZE = 50
            for i, line in enumerate(lines):
                # 匹配参数赋值行
                if f'self.{param_name}' in line and '=' in line:
                    # 找到等号位置
                    equal_pos = line.find('=')
                    if equal_pos > 0:
                        # 保留等号前的部分，替换等号后的值
                        indent = len(line) - len(line.lstrip())
                        indent_str = ' ' * indent
                        comment = ''
                        if '#' in line:
                            comment_pos = line.find('#')
                            # 注意：line 来自 readlines()，通常自带 '\n'
                            # 如果直接拼接 comment（含 '\n'）再额外加 '\n'，会导致每次保存多一行空行
                            comment = line[comment_pos:].rstrip('\n')
                        
                        # 构建新行
                        if isinstance(param_value, str):
                            new_value = f'"{param_value}"'
                        else:
                            new_value = str(param_value)
                        
                        # 保留原有的换行符
                        has_newline = line.endswith('\n')
                        new_line = f'{indent_str}self.{param_name} = {new_value}'
                        if comment:
                            # 统一成 “空格 + 注释” 的形式，避免重复空格
                            new_line += f' {comment.lstrip()}'
                        if has_newline:
                            new_line += '\n'
                        lines[i] = new_line
                        break
        
        # 写回文件
        with open(MAIZE_ESTIMATE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"更新Maize_Yield_API1配置文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False
