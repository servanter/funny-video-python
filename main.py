from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 导入拆分后的路由
from routers import hello, file

# 创建主应用
app = FastAPI(title="拆分路由示例")

# 配置跨域（和之前一样）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（核心：把两个路由模块挂载到主应用）
app.include_router(hello.router)  # 注册 hello 模块的路由
app.include_router(file.router)   # 注册 文件模块的路由

# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)