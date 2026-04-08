"""
GNAH_Maize_Yield 服务配置
"""
import os
import re
from pathlib import Path
from typing import Dict, Any

# Flask 服务配置（GNAH服务）
GNAH_SERVICE = {
    'HOST': os.getenv('GNAH_HOST', '127.0.0.1'),
    'PORT': int(os.getenv('GNAH_PORT', '5000')),
    'BASE_URL': None,  # 将在初始化时设置
    'API_ENDPOINT': '/gnah/runModel',
    'STATUS_ENDPOINT': '/gnah/getStatus',
    'TIMEOUT': int(os.getenv('GNAH_TIMEOUT', '3600')),  # 1小时
}

# 初始化 BASE_URL
GNAH_SERVICE['BASE_URL'] = f"http://{GNAH_SERVICE['HOST']}:{GNAH_SERVICE['PORT']}"

# GNAH项目路径配置
# 假设 GNAH_Maize_Yield 和 app-py 在同一父目录下
APP_PY_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_PY_ROOT.parent  # 项目根目录（corn-system-server-master）

# GNAH项目路径
GNAH_ROOT = PROJECT_ROOT / 'GNAH_Maize_Yield'

# 数据路径配置
GNAH_PATHS = {
    'INPUT_ERA5_DIR': GNAH_ROOT / 'data' / 'input' / 'ERA5',
    'INPUT_MODIS_REF_DIR': GNAH_ROOT / 'data' / 'input' / 'MODIS_Ref',
    'INPUT_MODIS_PAR_DIR': GNAH_ROOT / 'data' / 'input' / 'MODIS_PAR',
    'MODEL_D1': GNAH_ROOT / 'data' / 'input' / 'Model_d1.enc',
    'MODEL_D2': GNAH_ROOT / 'data' / 'input' / 'Model_d2.joblib',
    'OUTPUT_DIR': GNAH_ROOT / 'data' / 'output',
}

# app-py 输出目录（用于保存任务结果）
APP_PY_OUTPUT_DIR = APP_PY_ROOT / 'output'

# 确保目录存在
for path in GNAH_PATHS.values():
    if isinstance(path, Path):
        path.parent.mkdir(parents=True, exist_ok=True)

APP_PY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_gnah_url(endpoint: str = None) -> str:
    """获取GNAH服务的完整URL"""
    base_url = GNAH_SERVICE['BASE_URL']
    if endpoint:
        return f"{base_url}{endpoint}"
    return base_url

def validate_service_config():
    """验证服务配置"""
    errors = []
    
    # 检查路径是否存在
    if not GNAH_ROOT.exists():
        errors.append(f"GNAH 路径不存在: {GNAH_ROOT}")
    
    # 检查输入目录
    if not GNAH_PATHS['INPUT_ERA5_DIR'].exists():
        errors.append(f"ERA5目录不存在: {GNAH_PATHS['INPUT_ERA5_DIR']}")
    
    if not GNAH_PATHS['INPUT_MODIS_REF_DIR'].exists():
        errors.append(f"MODIS_Ref目录不存在: {GNAH_PATHS['INPUT_MODIS_REF_DIR']}")
    
    if not GNAH_PATHS['INPUT_MODIS_PAR_DIR'].exists():
        errors.append(f"MODIS_PAR目录不存在: {GNAH_PATHS['INPUT_MODIS_PAR_DIR']}")
    
    return errors

# GNAH 配置参数文件路径
GNAH_CONFIG_FILE = GNAH_ROOT / 'config.py'

def get_default_gnah_params() -> Dict[str, Any]:
    """获取默认的GNAH算法参数"""
    return {
        'output_prefix': 'GNAH_Yield_Task1'
    }

def get_default_model_coefficients() -> Dict[str, float]:
    """获取默认的模型系数"""
    return {
        'cc4': 5.18,
        'factor_yield1': 0.027,
        'factor_yield2': 66.666
    }

def read_gnah_config_from_file() -> Dict[str, Any]:
    """从GNAH的config.py文件读取配置参数和当前模型文件信息"""
    try:
        # 动态导入GNAH的config模块
        import sys
        import importlib.util

        config_path = str(GNAH_CONFIG_FILE.parent)
        if config_path not in sys.path:
            sys.path.insert(0, config_path)
        
        spec = importlib.util.spec_from_file_location("gnah_config_module", GNAH_CONFIG_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载GNAH配置文件: {GNAH_CONFIG_FILE}")
        
        gnah_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gnah_config)
        
        # 读取配置
        algorithm_config = getattr(gnah_config, 'ALGORITHM_CONFIG', get_default_gnah_params())
        model_coefficients = getattr(gnah_config, 'MODEL_COEFFICIENTS', get_default_model_coefficients())

        # 读取当前使用的模型文件（从 DATA_PATHS 中解析文件名）
        model_files: Dict[str, str] = {}
        data_paths = getattr(gnah_config, 'DATA_PATHS', None)
        if isinstance(data_paths, dict):
            for key in ('model_d1', 'model_d2'):
                value = data_paths.get(key)
                if value is not None:
                    # value 可能是 Path 或其它类型，统一转为字符串再取文件名
                    model_files[key] = os.path.basename(str(value))
        
        return {
            'params': algorithm_config,
            'coefficients': model_coefficients,
            'model_files': model_files,
        }
    except Exception as e:
        print(f"读取GNAH配置文件失败: {e}")
        # 返回默认值
        return {
            'params': get_default_gnah_params(),
            'coefficients': get_default_model_coefficients(),
            'model_files': {},
        }

def update_gnah_config_file(params: Dict[str, Any]):
    """更新GNAH的config.py文件中的算法参数"""
    try:
        if not GNAH_CONFIG_FILE.exists():
            raise FileNotFoundError(f"GNAH配置文件不存在: {GNAH_CONFIG_FILE}")
        
        # 读取文件内容
        with open(GNAH_CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 更新ALGORITHM_CONFIG
        for param_name, param_value in params.items():
            for i, line in enumerate(lines):
                if f'ALGORITHM_CONFIG' in line and f'"{param_name}"' in line and '=' in line:
                    # 找到对应的行，更新值
                    equal_pos = line.find('=')
                    if equal_pos > 0:
                        indent = len(line) - len(line.lstrip())
                        indent_str = ' ' * indent
                        comment = ''
                        if '#' in line:
                            comment_pos = line.find('#')
                            comment = line[comment_pos:].rstrip('\n')
                        
                        if isinstance(param_value, str):
                            new_value = f'"{param_value}"'
                        else:
                            new_value = str(param_value)
                        
                        new_line = f'{indent_str}"{param_name}": {new_value}'
                        if comment:
                            new_line += f' {comment.lstrip()}'
                        new_line += '\n'
                        lines[i] = new_line
                        break
                elif f'ALGORITHM_CONFIG' in line and '{' in line:
                    # 查找字典内的参数
                    j = i + 1
                    while j < len(lines) and '}' not in lines[j]:
                        if f'"{param_name}"' in lines[j] or f"'{param_name}'" in lines[j]:
                            # 找到参数行，更新值
                            line_to_update = lines[j]
                            equal_pos = line_to_update.find(':')
                            if equal_pos > 0:
                                indent = len(line_to_update) - len(line_to_update.lstrip())
                                indent_str = ' ' * indent
                                comment = ''
                                if '#' in line_to_update:
                                    comment_pos = line_to_update.find('#')
                                    comment = line_to_update[comment_pos:].rstrip('\n')
                                
                                if isinstance(param_value, str):
                                    new_value = f'"{param_value}"'
                                else:
                                    new_value = str(param_value)
                                
                                new_line = f'{indent_str}"{param_name}": {new_value}'
                                if comment:
                                    new_line += f' {comment.lstrip()}'
                                new_line += ',\n' if j < len(lines) - 1 and '}' not in lines[j+1] else '\n'
                                lines[j] = new_line
                                break
                        j += 1
        
        # 写回文件
        with open(GNAH_CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"更新GNAH配置文件失败: {e}")
        return False

def update_gnah_model_files(model_d1: str, model_d2: str):
    """更新GNAH的config.py文件中的模型文件路径"""
    try:
        if not GNAH_CONFIG_FILE.exists():
            raise FileNotFoundError(f"GNAH配置文件不存在: {GNAH_CONFIG_FILE}")
        
        # 读取文件内容
        with open(GNAH_CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 更新DATA_PATHS中的模型文件路径
        for i, line in enumerate(lines):
            # 查找DATA_PATHS字典
            if 'DATA_PATHS' in line and '{' in line:
                # 在DATA_PATHS字典内查找model_d1和model_d2
                j = i + 1
                while j < len(lines) and '}' not in lines[j]:
                    line_content = lines[j]
                    # 更新model_d1
                    if '"model_d1"' in line_content or "'model_d1'" in line_content:
                        colon_pos = line_content.find(':')
                        if colon_pos > 0:
                            indent = len(line_content) - len(line_content.lstrip())
                            indent_str = ' ' * indent
                            comment = ''
                            if '#' in line_content:
                                comment_pos = line_content.find('#')
                                comment = line_content[comment_pos:].rstrip('\n')
                            
                            new_line = f'{indent_str}"model_d1": INPUT_DIR / "{model_d1}"'
                            if comment:
                                new_line += f' {comment.lstrip()}'
                            new_line += ',\n' if j < len(lines) - 1 and '}' not in lines[j+1] else '\n'
                            lines[j] = new_line
                    
                    # 更新model_d2
                    elif '"model_d2"' in line_content or "'model_d2'" in line_content:
                        colon_pos = line_content.find(':')
                        if colon_pos > 0:
                            indent = len(line_content) - len(line_content.lstrip())
                            indent_str = ' ' * indent
                            comment = ''
                            if '#' in line_content:
                                comment_pos = line_content.find('#')
                                comment = line_content[comment_pos:].rstrip('\n')
                            
                            new_line = f'{indent_str}"model_d2": INPUT_DIR / "{model_d2}"'
                            if comment:
                                new_line += f' {comment.lstrip()}'
                            new_line += ',\n' if j < len(lines) - 1 and '}' not in lines[j+1] else '\n'
                            lines[j] = new_line
                    j += 1
                break
        
        # 写回文件
        with open(GNAH_CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"更新GNAH模型文件路径失败: {e}")
        return False

def update_gnah_model_coefficients(coefficients: Dict[str, float]):
    """更新GNAH的config.py文件中的模型系数"""
    try:
        if not GNAH_CONFIG_FILE.exists():
            raise FileNotFoundError(f"GNAH配置文件不存在: {GNAH_CONFIG_FILE}")
        
        # 读取文件内容
        with open(GNAH_CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        updated = False

        # 1) 处理单行写法：MODEL_COEFFICIENTS = {...}
        for i, line in enumerate(lines):
            if 'MODEL_COEFFICIENTS' in line and '=' in line and '{' in line and '}' in line:
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                comment = ''
                if '#' in line:
                    comment_pos = line.find('#')
                    comment = ' ' + line[comment_pos:].rstrip('\n')

                ordered_keys = ['cc4', 'factor_yield1', 'factor_yield2']
                kv_parts = []
                for k in ordered_keys:
                    if k in coefficients:
                        kv_parts.append(f"\"{k}\": {coefficients[k]}")
                for k, v in coefficients.items():
                    if k not in ordered_keys:
                        kv_parts.append(f"\"{k}\": {v}")

                lines[i] = f"{indent_str}MODEL_COEFFICIENTS = {{{', '.join(kv_parts)}}}{comment}\n"
                updated = True
                break

        # 2) 回退：处理多行字典块（逐项更新）
        if not updated:
            for coeff_name, coeff_value in coefficients.items():
                for i, line in enumerate(lines):
                    if 'MODEL_COEFFICIENTS' in line and '{' in line:
                        j = i + 1
                        while j < len(lines) and '}' not in lines[j]:
                            line_content = lines[j]
                            if f'"{coeff_name}"' in line_content or f"'{coeff_name}'" in line_content:
                                colon_pos = line_content.find(':')
                                if colon_pos > 0:
                                    indent = len(line_content) - len(line_content.lstrip())
                                    indent_str = ' ' * indent
                                    comment = ''
                                    if '#' in line_content:
                                        comment_pos = line_content.find('#')
                                        comment = line_content[comment_pos:].rstrip('\n')

                                    is_last = j + 1 < len(lines) and '}' in lines[j + 1]
                                    new_line = f'{indent_str}"{coeff_name}": {coeff_value}'
                                    if comment:
                                        new_line += f' {comment.lstrip()}'
                                    new_line += ',\n' if not is_last else '\n'
                                    lines[j] = new_line
                                    updated = True
                                    break
                            j += 1
                        break

        if not updated:
            print("更新GNAH模型系数失败: 未在配置文件中定位到可更新的 MODEL_COEFFICIENTS")
            return False
        
        # 写回文件
        with open(GNAH_CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✓ 模型系数已更新: {coefficients}")
        return True
    except Exception as e:
        print(f"更新GNAH模型系数失败: {e}")
        return False

def backup_and_update_gnah_data_paths(task_input_dir: Path) -> Dict[str, str]:
    """备份并临时更新GNAH的config.py中的DATA_PATHS，指向任务目录
    
    Returns:
        Dict[str, str]: 备份的原始路径，用于恢复
    """
    try:
        if not GNAH_CONFIG_FILE.exists():
            raise FileNotFoundError(f"GNAH配置文件不存在: {GNAH_CONFIG_FILE}")
        
        # 读取文件内容
        with open(GNAH_CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 备份原始路径
        original_paths = {}
        task_era5_dir = task_input_dir / 'ERA5'
        task_modis_ref_dir = task_input_dir / 'MODIS_Ref'
        task_modis_par_dir = task_input_dir / 'MODIS_PAR'
        
        # 更新DATA_PATHS中的输入目录路径
        for i, line in enumerate(lines):
            if 'DATA_PATHS' in line and '{' in line:
                j = i + 1
                while j < len(lines) and '}' not in lines[j]:
                    line_content = lines[j]
                    
                    # 更新era5_dir
                    if '"era5_dir"' in line_content or "'era5_dir'" in line_content:
                        colon_pos = line_content.find(':')
                        if colon_pos > 0:
                            # 备份原始路径
                            original_paths['era5_dir'] = line_content
                            
                            indent = len(line_content) - len(line_content.lstrip())
                            indent_str = ' ' * indent
                            comment = ''
                            if '#' in line_content:
                                comment_pos = line_content.find('#')
                                comment = line_content[comment_pos:].rstrip('\n')
                            
                            # 使用Path对象，转换为字符串格式（使用repr确保路径中的反斜杠被正确转义）
                            task_era5_str = repr(str(task_era5_dir))
                            new_line = f'{indent_str}"era5_dir": Path({task_era5_str})'
                            if comment:
                                new_line += f' {comment.lstrip()}'
                            new_line += ',\n' if j < len(lines) - 1 and '}' not in lines[j+1] else '\n'
                            lines[j] = new_line
                    
                    # 更新ref_dir
                    elif '"ref_dir"' in line_content or "'ref_dir'" in line_content:
                        colon_pos = line_content.find(':')
                        if colon_pos > 0:
                            original_paths['ref_dir'] = line_content
                            
                            indent = len(line_content) - len(line_content.lstrip())
                            indent_str = ' ' * indent
                            comment = ''
                            if '#' in line_content:
                                comment_pos = line_content.find('#')
                                comment = line_content[comment_pos:].rstrip('\n')
                            
                            task_modis_ref_str = repr(str(task_modis_ref_dir))
                            new_line = f'{indent_str}"ref_dir": Path({task_modis_ref_str})'
                            if comment:
                                new_line += f' {comment.lstrip()}'
                            new_line += ',\n' if j < len(lines) - 1 and '}' not in lines[j+1] else '\n'
                            lines[j] = new_line
                    
                    # 更新par_dir
                    elif '"par_dir"' in line_content or "'par_dir'" in line_content:
                        colon_pos = line_content.find(':')
                        if colon_pos > 0:
                            original_paths['par_dir'] = line_content
                            
                            indent = len(line_content) - len(line_content.lstrip())
                            indent_str = ' ' * indent
                            comment = ''
                            if '#' in line_content:
                                comment_pos = line_content.find('#')
                                comment = line_content[comment_pos:].rstrip('\n')
                            
                            task_modis_par_str = repr(str(task_modis_par_dir))
                            new_line = f'{indent_str}"par_dir": Path({task_modis_par_str})'
                            if comment:
                                new_line += f' {comment.lstrip()}'
                            new_line += ',\n' if j < len(lines) - 1 and '}' not in lines[j+1] else '\n'
                            lines[j] = new_line
                    j += 1
                break
        
        # 写回文件
        with open(GNAH_CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return original_paths
    except Exception as e:
        print(f"临时更新GNAH数据路径失败: {e}")
        return {}

def restore_gnah_data_paths(original_paths: Dict[str, str]):
    """恢复GNAH的config.py中的DATA_PATHS到原始值"""
    try:
        if not GNAH_CONFIG_FILE.exists() or not original_paths:
            return False
        
        # 读取文件内容
        with open(GNAH_CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 恢复原始路径
        for i, line in enumerate(lines):
            if 'DATA_PATHS' in line and '{' in line:
                j = i + 1
                while j < len(lines) and '}' not in lines[j]:
                    line_content = lines[j]
                    
                    # 恢复era5_dir
                    if '"era5_dir"' in line_content or "'era5_dir'" in line_content:
                        if 'era5_dir' in original_paths:
                            lines[j] = original_paths['era5_dir']
                    
                    # 恢复ref_dir
                    elif '"ref_dir"' in line_content or "'ref_dir'" in line_content:
                        if 'ref_dir' in original_paths:
                            lines[j] = original_paths['ref_dir']
                    
                    # 恢复par_dir
                    elif '"par_dir"' in line_content or "'par_dir'" in line_content:
                        if 'par_dir' in original_paths:
                            lines[j] = original_paths['par_dir']
                    j += 1
                break
        
        # 写回文件
        with open(GNAH_CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"恢复GNAH数据路径失败: {e}")
        return False
