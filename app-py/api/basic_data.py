from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import pandas as pd
import shutil
from datetime import datetime
import json
import uuid
from pathlib import Path
from typing import Tuple

# 通用Excel文件读取函数
def read_excel_file(file_path: Path, filename: str) -> Tuple[pd.ExcelFile, str]:
    """使用多引擎支持读取Excel文件"""
    excel_file = None
    engine = None
    
    # 首先尝试openpyxl引擎（适用于.xlsx文件）
    if filename.endswith('.xlsx'):
        try:
            excel_file = pd.ExcelFile(file_path, engine='openpyxl')
            engine = 'openpyxl'
        except Exception as e:
            pass
    
    # 如果openpyxl失败，尝试xlrd引擎（适用于.xls文件）
    if excel_file is None:
        try:
            excel_file = pd.ExcelFile(file_path, engine='xlrd')
            engine = 'xlrd'
        except Exception as e:
            pass
    
    # 如果都失败，尝试自动检测
    if excel_file is None:
        try:
            excel_file = pd.ExcelFile(file_path)
            engine = None  # 让pandas自动检测
        except Exception as e:
            raise Exception(f"无法解析Excel文件，请确保文件格式正确: {str(e)}")
    return excel_file, engine

# 通用Excel文件读取函数（用于读取特定工作表）
def read_excel_sheet(file_path: Path, filename: str, sheet_name: str) -> pd.DataFrame:
    """使用多引擎支持读取Excel文件的特定工作表"""
    try:
        excel_file, engine = read_excel_file(file_path, filename)
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)
        return df
    except Exception as e:
        raise Exception(f"读取工作表 {sheet_name} 失败: {str(e)}")

# 通用Excel文件写入函数
def write_excel_file(file_path: Path, filename: str, sheets_data: dict) -> None:
    """使用多引擎支持写入Excel文件"""
    # 检查原始文件格式
    original_is_xls = filename.endswith('.xls')
    
    # 对于.xls文件，检查是否已经被转换为xlsx格式
    if original_is_xls:
        # 尝试用openpyxl读取，如果成功说明已经是xlsx格式
        try:
            excel_file = pd.ExcelFile(file_path, engine='openpyxl')
            excel_file.close()  # 关闭文件句柄
            # 如果openpyxl可以读取，说明文件已经是xlsx格式，需要重命名
            print(f"检测到.xls文件但内容为xlsx格式，需要重命名: {file_path}")
            new_file_path = file_path.with_suffix('.xlsx')
            old_info_file = file_path.with_suffix('.xls.info.json')
            new_info_file = new_file_path.with_suffix('.xlsx.info.json')
            
            # 重命名文件
            file_path.rename(new_file_path)
            # 重命名info文件并更新其中的filename字段
            if old_info_file.exists():
                # 读取旧的info文件
                with open(old_info_file, 'r', encoding='utf-8') as f:
                    info_data = json.load(f)
                
                # 更新filename字段
                info_data['filename'] = new_file_path.name
                
                # 写入新的info文件
                with open(new_info_file, 'w', encoding='utf-8') as f:
                    json.dump(info_data, f, ensure_ascii=False, indent=2)
                
                # 删除旧的info文件
                old_info_file.unlink()
            
            file_path = new_file_path
            engine = 'openpyxl'
            print(f"文件已重命名为: {file_path}")
        except Exception:
            # 如果openpyxl无法读取，说明是真正的.xls格式
            # 但是xlrd不能写入，所以我们需要转换为.xlsx
            print(f"检测到真正的.xls文件，需要转换为.xlsx: {file_path}")
            new_file_path = file_path.with_suffix('.xlsx')
            old_info_file = file_path.with_suffix('.xls.info.json')
            new_info_file = new_file_path.with_suffix('.xlsx.info.json')
            
            # 重命名文件
            file_path.rename(new_file_path)
            # 重命名info文件并更新其中的filename字段
            if old_info_file.exists():
                # 读取旧的info文件
                with open(old_info_file, 'r', encoding='utf-8') as f:
                    info_data = json.load(f)
                
                # 更新filename字段
                info_data['filename'] = new_file_path.name
                
                # 写入新的info文件
                with open(new_info_file, 'w', encoding='utf-8') as f:
                    json.dump(info_data, f, ensure_ascii=False, indent=2)
                
                # 删除旧的info文件
                old_info_file.unlink()
            
            file_path = new_file_path
            engine = 'openpyxl'
            print(f"文件已重命名为: {file_path}")
    else:
        # 对于.xlsx文件，直接使用openpyxl
        engine = 'openpyxl'
    
    with pd.ExcelWriter(file_path, engine=engine) as writer:
        for sheet_name, sheet_df in sheets_data.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

router = APIRouter()

# 数据分类配置
DATA_CATEGORIES = {
    'climate': '气象数据',
    'soil': '土壤数据', 
    'fertilization': '施肥数据',
    'future': '未来数据',
    'irrigation': '灌溉数据',
    'multi_site': '多站点数据',
    'nitrogen_limited': '氮限制数据',
    'potential_bj': '潜力数据-北京',
    'potential_fz': '潜力数据-抚州',
    'sowing': '播种数据',
    'variety': '品种数据',
    'water_limited': '水分限制数据',
    '2023': '2023年数据'
}

from pathlib import Path

# 数据存储根目录（Excel）
DATA_ROOT = Path("data/basic_data")
DATA_ROOT.mkdir(parents=True, exist_ok=True)

# 为每个分类创建目录（Excel）
for category in DATA_CATEGORIES.keys():
    (DATA_ROOT / category).mkdir(exist_ok=True)

# ---------------- JSON 基础数据（前端 public/data/BaseData）配置 ----------------
# JSON 数据根目录：相对于当前 backend 工程目录推断到 corn-system/public/data/BaseData
BACKEND_BASE_DIR = Path(__file__).resolve().parent.parent  # app-py
PROJECT_ROOT = BACKEND_BASE_DIR.parent  # corn-system-server-master
JSON_BASE_ROOT = PROJECT_ROOT / "corn-system" / "public" / "data" / "BaseData"

# 分类到目录名的映射（目录位于 JSON_BASE_ROOT 下）
JSON_CATEGORY_DIRS: Dict[str, str] = {
    "climate": "management_climate",
    "soil": "management_soil",
    "sowing": "management_sowing",
    "variety": "management_variety",
    "fertilization": "management_fertilization",
    "future": "management_future",
    "irrigation": "management_irrigation",
    "multi_site": "management_multi_site",
    "nitrogen_limited": "management_nitrogen_limited",
    "potential_bj": "management_potential_bj",
    "potential_fz": "management_potential_fz",
    "water_limited": "management_water_limited",
    "water_limited_fz": "management_water_limited_fz",
    "2023": "2023",  # 2023 直接作为子目录
}


@router.get("/json_files")
async def get_json_files(category: str = Query(..., description="JSON 数据分类")):
    """
    按分类获取 JSON 基础数据文件列表（来自前端 public/data/BaseData 目录）。
    返回相对于 BaseData 的路径，供前端直接拼接为 /data/BaseData/<path>.json 使用。
    """
    # 只允许我们定义过的分类，避免误访问其他目录
    if category not in JSON_CATEGORY_DIRS:
        raise HTTPException(status_code=400, detail=f"不支持的JSON数据分类: {category}")

    # 根目录存在性检查
    if not JSON_BASE_ROOT.exists():
        # 不抛 500，返回空列表并给出提示信息，方便前端调试
        return JSONResponse(content={
            "category": category,
            "base_dir": str(JSON_BASE_ROOT),
            "files": [],
            "message": "JSON 基础数据根目录不存在，请检查部署路径或目录结构"
        })

    sub_dir_name = JSON_CATEGORY_DIRS[category]
    target_dir = (JSON_BASE_ROOT / sub_dir_name).resolve()

    # 安全检查：防止目录穿越
    try:
        target_dir.relative_to(JSON_BASE_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法目录访问")

    if not target_dir.exists() or not target_dir.is_dir():
        # 目录不存在同样返回空列表
        return JSONResponse(content={
            "category": category,
            "directory": sub_dir_name,
            "files": [],
            "message": "分类目录不存在或不是文件夹"
        })

    # 递归遍历该分类目录下的所有 .json 文件
    files: List[str] = []
    for file_path in target_dir.rglob("*.json"):
        # 将路径转换为相对于 BaseData 的相对路径，并统一为正斜杠
        rel_path = file_path.relative_to(JSON_BASE_ROOT)
        files.append(str(rel_path).replace("\\", "/"))

    # 排序一下，保证前端展示稳定
    files.sort()

    return JSONResponse(content={
        "category": category,
        "directory": sub_dir_name,
        "files": files
    })


@router.post("/json_files/upload")
async def upload_json_file(
    file: UploadFile = File(...),
    category: str = Form(...)
):
    """上传 JSON 基础数据文件到指定分类目录"""
    if category not in JSON_CATEGORY_DIRS:
        raise HTTPException(status_code=400, detail=f"不支持的JSON数据分类: {category}")

    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="只支持上传 .json 文件")

    # 读取文件内容
    content = await file.read()
    max_size = 20 * 1024 * 1024  # 20MB 限制
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="文件大小超过20MB限制")

    try:
        # 验证 JSON 格式
        json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无效的JSON文件: {str(e)}")

    # 目标路径
    target_dir = (JSON_BASE_ROOT / JSON_CATEGORY_DIRS[category]).resolve()
    try:
        target_dir.relative_to(JSON_BASE_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法目录访问")

    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = (target_dir / file.filename).resolve()
    try:
        target_path.relative_to(JSON_BASE_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法文件路径")

    # 保存文件（覆盖同名）
    with open(target_path, "wb") as f:
        f.write(content)

    # 返回相对于 BaseData 的路径，方便前端直接拼接 /data/BaseData/<path>
    relative_path = str(target_path.relative_to(JSON_BASE_ROOT)).replace("\\", "/")

    return JSONResponse(content={
        "message": "JSON 文件上传成功",
        "filename": file.filename,
        "relative_path": relative_path,
        "category": category
    })


@router.post("/json_files/save")
async def save_json_file(request: SaveJsonRequest):
    """保存（覆盖）已有的 JSON 基础数据文件"""
    if request.category not in JSON_CATEGORY_DIRS:
        raise HTTPException(status_code=400, detail=f"不支持的JSON数据分类: {request.category}")

    if not request.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="文件名必须以 .json 结尾")

    # 如果前端传的是 get_json_files 返回的相对路径（可能含子目录），直接以 BaseData 为根
    if "/" in request.filename or "\\" in request.filename:
        target_path = (JSON_BASE_ROOT / request.filename).resolve()
    else:
        target_dir = (JSON_BASE_ROOT / JSON_CATEGORY_DIRS[request.category]).resolve()
        try:
            target_dir.relative_to(JSON_BASE_ROOT)
        except ValueError:
            raise HTTPException(status_code=400, detail="非法目录访问")
        target_path = (target_dir / request.filename).resolve()

    try:
        target_path.relative_to(JSON_BASE_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法文件路径")

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在，无法保存")

    try:
        # 将数据写入文件，使用 UTF-8 并保持格式
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(request.data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

    return JSONResponse(content={
        "message": "保存成功",
        "filename": request.filename,
        "category": request.category
    })


@router.delete("/json_files/{category}/{file_path:path}")
async def delete_json_file(category: str, file_path: str):
    """删除指定的 JSON 基础数据文件"""
    if category not in JSON_CATEGORY_DIRS:
        raise HTTPException(status_code=400, detail=f"不支持的JSON数据分类: {category}")

    if not file_path.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="文件名必须以 .json 结尾")

    # 如果前端传的是带子目录的相对路径，则直接按 BaseData 根计算
    if "/" in file_path or "\\" in file_path:
        target_path = (JSON_BASE_ROOT / file_path).resolve()
    else:
        target_dir = (JSON_BASE_ROOT / JSON_CATEGORY_DIRS[category]).resolve()
        try:
            target_dir.relative_to(JSON_BASE_ROOT)
        except ValueError:
            raise HTTPException(status_code=400, detail="非法目录访问")
        target_path = (target_dir / file_path).resolve()

    try:
        target_path.relative_to(JSON_BASE_ROOT)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法文件路径")

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        target_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

    return JSONResponse(content={
        "message": "删除成功",
        "filename": file_path,
        "category": category
    })

# 请求模型
class RowEditRequest(BaseModel):
    row_index: int
    sheet_name: str
    new_row: List[str]
    file_name_prefix: str

class RowDeleteRequest(BaseModel):
    row_index: int
    sheet_name: str
    file_name_prefix: str

class RowAddRequest(BaseModel):
    sheet_name: str
    new_row: List[str]
    file_name_prefix: str

class ColumnRenameRequest(BaseModel):
    sheet_name: str
    old_column_name: str
    new_column_name: str
    file_name_prefix: str

class ColumnDeleteRequest(BaseModel):
    sheet_name: str
    column_name: str
    file_name_prefix: str

class SaveFileRequest(BaseModel):
    sheet_name: str
    columns: List[str]
    data: List[List[str]]
    file_name_prefix: str

# JSON 保存请求
class SaveJsonRequest(BaseModel):
    category: str
    filename: str
    data: Any  # 直接存储 JSON 序列化结果（二维数组）

# 文件上传接口
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(...)
):
    """上传Excel文件到指定分类"""
    if category not in DATA_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"不支持的数据分类: {category}")
    
    # 检查文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
    
    # 检查文件大小 (50MB限制)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过50MB限制")
    
    try:
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = str(uuid.uuid4())[:8]
        safe_filename = f"{file_id}_{timestamp}_{file.filename}"
        
        # 保存文件
        category_dir = DATA_ROOT / category
        file_path = category_dir / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 解析Excel文件获取工作表信息
        try:
            # 使用通用函数读取Excel文件
            excel_file, engine = read_excel_file(file_path, file.filename)
            
            sheets_info = {
                "filename": safe_filename,
                "sheets": excel_file.sheet_names,
                "category": category,
                "upload_time": datetime.now().isoformat(),
                "file_size": file_path.stat().st_size,
                "engine_used": engine
            }
            
            # 保存文件信息
            info_file = category_dir / f"{safe_filename}.info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(sheets_info, f, ensure_ascii=False, indent=2)
            
            return JSONResponse(content={
                "message": "文件上传成功",
                "filename": safe_filename,
                "sheets": excel_file.sheet_names,
                "category": DATA_CATEGORIES[category]
            })
            
        except Exception as e:
            # 如果解析失败，删除已上传的文件
            if file_path.exists():
                file_path.unlink()
            # 直接抛出400错误，不要被外层捕获
            raise HTTPException(status_code=400, detail=f"Excel文件解析失败: {str(e)}")
            
    except HTTPException:
        # 重新抛出HTTP异常，不要被外层捕获
        raise
    except Exception as e:
        # 其他异常才返回500错误
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

# 获取文件列表
@router.get("/files")
async def get_files(category: Optional[str] = None):
    """获取文件列表，可按分类筛选"""
    try:
        files_list = []
        
        if category and category in DATA_CATEGORIES:
            # 获取指定分类的文件
            category_dir = DATA_ROOT / category
            if category_dir.exists():
                # 查找所有Excel文件（.xlsx和.xls）
                for file_path in category_dir.glob("*.xlsx"):
                    info_file = file_path.with_suffix('.xlsx.info.json')
                    if info_file.exists():
                        with open(info_file, 'r', encoding='utf-8') as f:
                            file_info = json.load(f)
                            files_list.append(file_info)
                
                for file_path in category_dir.glob("*.xls"):
                    info_file = file_path.with_suffix('.xls.info.json')
                    if info_file.exists():
                        with open(info_file, 'r', encoding='utf-8') as f:
                            file_info = json.load(f)
                            files_list.append(file_info)
        else:
            # 获取所有分类的文件
            for cat in DATA_CATEGORIES.keys():
                category_dir = DATA_ROOT / cat
                if category_dir.exists():
                    # 查找所有Excel文件（.xlsx和.xls）
                    for file_path in category_dir.glob("*.xlsx"):
                        info_file = file_path.with_suffix('.xlsx.info.json')
                        if info_file.exists():
                            with open(info_file, 'r', encoding='utf-8') as f:
                                file_info = json.load(f)
                                files_list.append(file_info)
                    
                    for file_path in category_dir.glob("*.xls"):
                        info_file = file_path.with_suffix('.xls.info.json')
                        if info_file.exists():
                            with open(info_file, 'r', encoding='utf-8') as f:
                                file_info = json.load(f)
                                files_list.append(file_info)
        
        # 按上传时间排序
        files_list.sort(key=lambda x: x.get('upload_time', ''), reverse=True)
        
        return JSONResponse(content={
            "files": files_list,
            "categories": DATA_CATEGORIES
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

# 获取文件内容
@router.get("/getFiles")
async def get_file_content(
    name: str = Query(..., description="文件名"),
    category: str = Query(..., description="数据分类")
):
    """获取Excel文件内容"""
    if category not in DATA_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"不支持的数据分类: {category}")
    
    try:
        category_dir = DATA_ROOT / category
        file_path = category_dir / name
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取Excel文件，使用多引擎支持
        try:
            excel_file, engine = read_excel_file(file_path, name)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Excel文件解析失败: {str(e)}")
        
        # 获取所有工作表的数据
        sheets_data = {}
        for sheet_name in excel_file.sheet_names:
            try:
                df = read_excel_sheet(file_path, name, sheet_name)
                # 转换为字典格式
                sheets_data[sheet_name] = {
                    "columns": df.columns.tolist(),
                    "data": df.fillna('').astype(str).to_dict('records')
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"读取工作表 {sheet_name} 失败: {str(e)}")
        
        return JSONResponse(content={
            "filename": name,
            "category": category,
            "sheets": sheets_data
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

# 验证文件格式
@router.get("/validate_file")
async def validate_file(
    fileName: str = Query(..., description="文件名"),
    algorithm: str = Query(..., description="算法类型"),
    category: str = Query(..., description="数据分类")
):
    """验证文件格式和内容"""
    if category not in DATA_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"不支持的数据分类: {category}")
    
    try:
        category_dir = DATA_ROOT / category
        file_path = category_dir / fileName
        
        if not file_path.exists():
            return JSONResponse(content={
                "valid": False,
                "error": "文件不存在"
            })
        
        # 读取Excel文件
        excel_file, engine = read_excel_file(file_path, fileName)
        first_sheet = excel_file.sheet_names[0]
        df = read_excel_sheet(file_path, fileName, first_sheet)
        
        # 基本验证
        if df.empty:
            return JSONResponse(content={
                "valid": False,
                "error": "文件为空"
            })
        
        # 返回第一行数据用于预览
        first_row = df.iloc[0].fillna('').astype(str).to_dict()
        
        return JSONResponse(content={
            "valid": True,
            "data": [first_row],
            "columns": df.columns.tolist(),
            "sheet_name": first_sheet
        })
        
    except Exception as e:
        return JSONResponse(content={
            "valid": False,
            "error": f"文件验证失败: {str(e)}"
        })

# 编辑行数据
@router.post("/edit")
async def edit_row(request: RowEditRequest):
    """编辑表格行数据"""
    try:
        # 根据文件名前缀找到对应的文件
        category_dir = DATA_ROOT
        file_path = None
        
        # 在所有分类中查找文件
        for cat in DATA_CATEGORIES.keys():
            cat_dir = category_dir / cat
            for file in cat_dir.glob(f"{request.file_name_prefix}*"):
                if file.suffix in ['.xlsx', '.xls']:
                    file_path = file
                    break
            if file_path:
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取Excel文件
        excel_file, engine = read_excel_file(file_path, file_path.name)
        
        # 读取指定工作表
        if request.sheet_name not in excel_file.sheet_names:
            raise HTTPException(status_code=400, detail="工作表不存在")
        
        df = read_excel_sheet(file_path, file_path.name, request.sheet_name)
        
        # 检查行索引
        if request.row_index < 0 or request.row_index >= len(df):
            raise HTTPException(status_code=400, detail="行索引超出范围")
        
        # 更新数据
        for i, value in enumerate(request.new_row):
            if i < len(df.columns):
                # 处理空值，确保空字符串被正确保存
                df.iloc[request.row_index, i] = value if value is not None else ''
        
        # 读取所有工作表数据到内存中
        all_sheets_data = {}
        for sheet in excel_file.sheet_names:
            if sheet == request.sheet_name:
                all_sheets_data[sheet] = df
            else:
                all_sheets_data[sheet] = read_excel_sheet(file_path, file_path.name, sheet)
        
        # 保存文件
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for sheet_name, sheet_df in all_sheets_data.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return JSONResponse(content={
            "message": "行替换成功",
            "row_index": request.row_index,
            "sheet_name": request.sheet_name
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编辑失败: {str(e)}")

# 删除行数据
@router.post("/delete")
async def delete_row(request: RowDeleteRequest):
    """删除表格行数据"""
    try:
        # 根据文件名前缀找到对应的文件
        category_dir = DATA_ROOT
        file_path = None
        
        # 在所有分类中查找文件
        for cat in DATA_CATEGORIES.keys():
            cat_dir = category_dir / cat
            for file in cat_dir.glob(f"{request.file_name_prefix}*"):
                if file.suffix in ['.xlsx', '.xls']:
                    file_path = file
                    break
            if file_path:
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取Excel文件
        excel_file, engine = read_excel_file(file_path, file_path.name)
        
        # 读取指定工作表
        if request.sheet_name not in excel_file.sheet_names:
            raise HTTPException(status_code=400, detail="工作表不存在")
        
        df = read_excel_sheet(file_path, file_path.name, request.sheet_name)
        
        # 检查行索引
        if request.row_index < 0 or request.row_index >= len(df):
            raise HTTPException(status_code=400, detail="行索引超出范围")
        
        # 删除行
        df = df.drop(df.index[request.row_index]).reset_index(drop=True)
        
        # 读取所有工作表数据到内存中
        all_sheets_data = {}
        for sheet in excel_file.sheet_names:
            if sheet == request.sheet_name:
                all_sheets_data[sheet] = df
            else:
                all_sheets_data[sheet] = read_excel_sheet(file_path, file_path.name, sheet)
        
        # 保存文件
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for sheet_name, sheet_df in all_sheets_data.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return JSONResponse(content={
            "message": "行删除成功",
            "row_index": request.row_index,
            "sheet_name": request.sheet_name
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# 添加行数据
@router.post("/add")
async def add_row(request: RowAddRequest):
    """添加新的表格行数据"""
    try:
        # 根据文件名前缀找到对应的文件
        category_dir = DATA_ROOT
        file_path = None
        
        # 在所有分类中查找文件
        for cat in DATA_CATEGORIES.keys():
            cat_dir = category_dir / cat
            for file in cat_dir.glob(f"{request.file_name_prefix}*"):
                if file.suffix in ['.xlsx', '.xls']:
                    file_path = file
                    break
            if file_path:
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取Excel文件
        excel_file, engine = read_excel_file(file_path, file_path.name)
        
        # 读取指定工作表
        if request.sheet_name not in excel_file.sheet_names:
            raise HTTPException(status_code=400, detail="工作表不存在")
        
        df = read_excel_sheet(file_path, file_path.name, request.sheet_name)
        
        # 创建新行数据
        new_row_data = {}
        for i, value in enumerate(request.new_row):
            if i < len(df.columns):
                new_row_data[df.columns[i]] = value
        
        # 添加新行
        new_row_df = pd.DataFrame([new_row_data])
        df = pd.concat([df, new_row_df], ignore_index=True)
        
        # 读取所有工作表数据到内存中
        all_sheets_data = {}
        for sheet in excel_file.sheet_names:
            if sheet == request.sheet_name:
                all_sheets_data[sheet] = df
            else:
                all_sheets_data[sheet] = read_excel_sheet(file_path, file_path.name, sheet)
        
        # 保存文件
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for sheet_name, sheet_df in all_sheets_data.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return JSONResponse(content={
            "message": "行添加成功",
            "sheet_name": request.sheet_name,
            "new_row_index": len(df) - 1
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")

# 修改列名
@router.post("/rename_column")
async def rename_column(request: ColumnRenameRequest):
    """修改表格列名"""
    try:
        # 根据文件名前缀找到对应的文件
        category_dir = DATA_ROOT
        file_path = None
        
        # 在所有分类中查找文件
        for cat in DATA_CATEGORIES.keys():
            cat_dir = category_dir / cat
            for file in cat_dir.glob(f"{request.file_name_prefix}*"):
                if file.suffix in ['.xlsx', '.xls']:
                    file_path = file
                    break
            if file_path:
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取Excel文件
        excel_file, engine = read_excel_file(file_path, file_path.name)
        
        # 读取指定工作表
        if request.sheet_name not in excel_file.sheet_names:
            raise HTTPException(status_code=400, detail="工作表不存在")
        
        df = read_excel_sheet(file_path, file_path.name, request.sheet_name)
        
        # 检查旧列名是否存在
        if request.old_column_name not in df.columns:
            raise HTTPException(status_code=400, detail="列名不存在")
        
        # 检查新列名是否已存在
        if request.new_column_name in df.columns and request.new_column_name != request.old_column_name:
            raise HTTPException(status_code=400, detail="新列名已存在")
        
        # 重命名列
        df = df.rename(columns={request.old_column_name: request.new_column_name})
        
        # 读取所有工作表数据到内存中
        all_sheets_data = {}
        for sheet in excel_file.sheet_names:
            if sheet == request.sheet_name:
                all_sheets_data[sheet] = df
            else:
                all_sheets_data[sheet] = read_excel_sheet(file_path, file_path.name, sheet)
        
        # 保存文件
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for sheet_name, sheet_df in all_sheets_data.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return JSONResponse(content={
            "message": "列名修改成功",
            "old_column_name": request.old_column_name,
            "new_column_name": request.new_column_name,
            "sheet_name": request.sheet_name
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列名修改失败: {str(e)}")

# 删除列
@router.post("/delete_column")
async def delete_column(request: ColumnDeleteRequest):
    """删除表格列"""
    try:
        # 根据文件名前缀找到对应的文件
        category_dir = DATA_ROOT
        file_path = None
        
        # 在所有分类中查找文件
        for cat in DATA_CATEGORIES.keys():
            cat_dir = category_dir / cat
            for file in cat_dir.glob(f"{request.file_name_prefix}*"):
                if file.suffix in ['.xlsx', '.xls']:
                    file_path = file
                    break
            if file_path:
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 读取Excel文件
        excel_file, engine = read_excel_file(file_path, file_path.name)
        
        # 读取指定工作表
        if request.sheet_name not in excel_file.sheet_names:
            raise HTTPException(status_code=400, detail="工作表不存在")
        
        df = read_excel_sheet(file_path, file_path.name, request.sheet_name)
        
        # 检查列名是否存在
        if request.column_name not in df.columns:
            raise HTTPException(status_code=400, detail="列名不存在")
        
        # 删除列
        df = df.drop(columns=[request.column_name])
        
        # 读取所有工作表数据到内存中
        all_sheets_data = {}
        for sheet in excel_file.sheet_names:
            if sheet == request.sheet_name:
                all_sheets_data[sheet] = df
            else:
                all_sheets_data[sheet] = read_excel_sheet(file_path, file_path.name, sheet)
        
        # 保存文件
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for sheet_name, sheet_df in all_sheets_data.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return JSONResponse(content={
            "message": "列删除成功",
            "deleted_column_name": request.column_name,
            "sheet_name": request.sheet_name
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列删除失败: {str(e)}")

# 保存整个文件
@router.post("/save_file")
async def save_file(request: SaveFileRequest):
    """保存整个文件，替换原文件"""
    try:
        # 根据文件名前缀找到对应的文件
        category_dir = DATA_ROOT
        file_path = None
        
        # 在所有分类中查找文件
        for cat in DATA_CATEGORIES.keys():
            cat_dir = category_dir / cat
            for file in cat_dir.glob(f"{request.file_name_prefix}*"):
                if file.suffix in ['.xlsx', '.xls']:
                    file_path = file
                    break
            if file_path:
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 创建新的DataFrame
        df = pd.DataFrame(request.data, columns=request.columns)
        
        # 读取原文件的所有工作表
        try:
            excel_file, engine = read_excel_file(file_path, file_path.name)
            all_sheets_data = {}
            
            # 保存其他工作表的数据
            for sheet in excel_file.sheet_names:
                if sheet != request.sheet_name:
                    try:
                        all_sheets_data[sheet] = read_excel_sheet(file_path, file_path.name, sheet)
                    except Exception as e:
                        # 如果某个工作表读取失败，记录错误但继续处理其他工作表
                        print(f"警告: 读取工作表 {sheet} 失败: {str(e)}")
                        continue
            
            # 添加当前工作表的数据
            all_sheets_data[request.sheet_name] = df
            
            # 关闭文件句柄
            excel_file.close()
            
        except Exception as e:
            # 如果完全无法读取原文件，只保存当前工作表
            print(f"警告: 无法读取原文件，只保存当前工作表: {str(e)}")
            all_sheets_data = {request.sheet_name: df}
        
        # 保存文件，使用我们的通用写入函数
        write_excel_file(file_path, file_path.name, all_sheets_data)
        
        return JSONResponse(content={
            "message": "文件保存成功",
            "sheet_name": request.sheet_name,
            "rows_count": len(request.data),
            "columns_count": len(request.columns)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

# 删除文件
@router.delete("/file/{category}/{filename}")
async def delete_file(category: str, filename: str):
    """删除指定文件"""
    if category not in DATA_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"不支持的数据分类: {category}")
    
    try:
        category_dir = DATA_ROOT / category
        file_path = category_dir / filename
        info_file = category_dir / f"{filename}.info.json"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除文件和信息文件
        file_path.unlink()
        if info_file.exists():
            info_file.unlink()
        
        return JSONResponse(content={
            "message": "文件删除成功",
            "filename": filename
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

# 获取数据分类信息
@router.get("/categories")
async def get_categories():
    """获取所有数据分类信息"""
    return JSONResponse(content={
        "categories": DATA_CATEGORIES,
        "total": len(DATA_CATEGORIES)
    })
