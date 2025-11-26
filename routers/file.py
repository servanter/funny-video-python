from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path
from service.core_service import save_uploaded_file, test_save_file

# 创建文件相关的路由实例
router = APIRouter(
    prefix="/file",  # 所有接口前缀为 /file/xxx
    tags=["文件模块"]
)

# 配置文件存储目录（可以抽成单独的配置文件，这里简化）
UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# 上传文件接口
@router.post("/upload", summary="上传文件")
async def upload_file(file: UploadFile, user_id: str, title: str, description: str):
    result = save_uploaded_file(file, user_id, title, description)
    return {"message": "上传成功", "result": result}

# 上传文件接口
@router.post("/test_save", summary="上传文件")
async def test_save(file: UploadFile, user_id: str, title: str, description: str):
    result = test_save_file(file, user_id, title, description)
    return {"message": "上传成功", "result": result}


# 下载文件接口
@router.get("/download/{filename}", summary="下载文件")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(path=file_path, filename=filename)

# 列出文件接口
@router.get("/list", summary="列出所有文件")
async def list_files():
    files = [f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
    return {"files": files}