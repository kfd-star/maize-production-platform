from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
try:
    from api.MaizeSM import router as MaizeSM_EnKf  # 导入你的MaizeSM路由
    MAIZESM_AVAILABLE = True
except ImportError:
    print("⚠️  警告: MaizeSM模块导入失败，将跳过原有算法")
    MAIZESM_AVAILABLE = False

from api.maize_yield import router as MaizeYield_router  # 导入玉米产量预测路由
from api.maize_yield_tasks import router as MaizeYield_Tasks_router  # 导入玉米产量预测任务路由
from api.fspm import router as FSPM_router  # 导入FSPM路由
from api.fspm_tasks import router as FSPM_Tasks_router  # 导入FSPM任务路由
from api.tasks import router as Tasks_router  # 导入LAI任务路由
from api.lai_tasks import router as LAI_Tasks_router  # 导入LAI任务历史路由
from api.fspm_parameters import router as FSPM_Parameters_router  # 导入FSPM参数路由
from api.basic_data import router as BasicData_router  # 导入基础数据管理路由
from api.maize_estimate import router as MaizeEstimate_router  # 导入Maize_Yield_API1路由
from api.maize_estimate_tasks import router as MaizeEstimate_Tasks_router  # 导入Maize_Yield_API1任务路由
from api.scym import router as SCYM_router  # 导入SCYM路由
from api.scym_tasks import router as SCYM_Tasks_router  # 导入SCYM任务路由
from api.gnah import router as GNAH_router  # 导入GNAH路由
from api.gnah_tasks import router as GNAH_Tasks_router  # 导入GNAH任务路由

app = FastAPI(title="MaizeSM 数据同化服务", 
              description="提供EnKF、UKF、PF、NLS-4DVAR等算法的数据同化服务和玉米产量预测服务",
              version="1.0.0",
              # 增加文件上传大小限制
              max_request_size=100 * 1024 * 1024)  # 100MB

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 挂载你的MaizeSM路由（如果可用）
if MAIZESM_AVAILABLE:
    app.include_router(MaizeSM_EnKf, prefix="/api", tags=["maize"])
    print("✅ MaizeSM路由挂载成功")
else:
    print("❌ MaizeSM路由挂载失败，跳过")

# 挂载玉米产量预测路由
app.include_router(MaizeYield_router, prefix="/api", tags=["maize_yield"])
print("✅ 玉米产量预测路由挂载成功")

# 挂载玉米产量预测任务路由
app.include_router(MaizeYield_Tasks_router, prefix="/api", tags=["maize_yield_tasks"])
print("✅ 玉米产量预测任务路由挂载成功")

# 挂载FSPM路由
app.include_router(FSPM_router, prefix="/api", tags=["fspm"])
print("✅ FSPM路由挂载成功")

# 挂载FSPM任务路由
app.include_router(FSPM_Tasks_router, prefix="/api", tags=["fspm_tasks"])
print("✅ FSPM任务路由挂载成功")

# 挂载LAI任务路由
app.include_router(Tasks_router, prefix="/api", tags=["lai_tasks"])
print("✅ LAI任务路由挂载成功")

# 挂载LAI任务历史路由
app.include_router(LAI_Tasks_router, prefix="/api", tags=["lai_tasks_history"])
print("✅ LAI任务历史路由挂载成功")

# 挂载FSPM参数路由
app.include_router(FSPM_Parameters_router, prefix="/api", tags=["fspm_parameters"])
print("✅ FSPM参数路由挂载成功")

# 挂载基础数据管理路由
app.include_router(BasicData_router, prefix="/api", tags=["basic_data"])
print("✅ 基础数据管理路由挂载成功")

# 挂载Maize_Yield_API1路由
app.include_router(MaizeEstimate_router, prefix="/api", tags=["maize_estimate"])
print("✅ Maize_Yield_API1路由挂载成功")

# 挂载Maize_Yield_API1任务路由
app.include_router(MaizeEstimate_Tasks_router, prefix="/api", tags=["maize_estimate_tasks"])
print("✅ Maize_Yield_API1任务路由挂载成功")

# 挂载SCYM路由
app.include_router(SCYM_router, prefix="/api", tags=["scym"])
print("✅ SCYM路由挂载成功")

# 挂载SCYM任务路由
app.include_router(SCYM_Tasks_router, prefix="/api", tags=["scym_tasks"])
print("✅ SCYM任务路由挂载成功")

# 挂载GNAH路由
app.include_router(GNAH_router, prefix="/api", tags=["gnah"])
print("✅ GNAH路由挂载成功")

# 挂载GNAH任务路由
app.include_router(GNAH_Tasks_router, prefix="/api", tags=["gnah_tasks"])
print("✅ GNAH任务路由挂载成功")

@app.get("/")
async def root():
    """根路径重定向到文档页面"""
    return RedirectResponse(url="/docs")

@app.get("/parameters")
async def parameters_page():
    """参数配置页面重定向"""
    return RedirectResponse(url="/static/parameters.html")

# 启动方式：支持 python main.py
if __name__ == "__main__":
    import uvicorn
    
    print("🌽 启动 MaizeSM 数据同化服务...")
    print("📖 API文档: http://127.0.0.1:8001/docs")
    print("⚙️  参数配置: http://127.0.0.1:8001/parameters")
    print("🚀 服务启动中，请稍候...")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
