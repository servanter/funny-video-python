import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# 加载环境变量
load_dotenv()


def upload_to_supabase(
        local_file_path: str,  # 本地文件路径（如：uploads/1762845319/result/first_frame.jpg）
        storage_file_path: str,  # 存储到 Supabase 的路径（默认复用本地文件相对路径）
) -> tuple[bool, str]:
    # 1. 验证必填参数
    bucket_name = os.getenv("STORAGE_BUCKET_NAME")
    if not bucket_name:
        return False, "错误：未指定存储桶名称（请在 .env 配置 STORAGE_BUCKET_NAME）"

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    local_file_path = os.path.join(project_root, local_file_path)
    if not os.path.exists(local_file_path):
        return False, f"错误：本地文件不存在 - {local_file_path}"

    # 2. 初始化 Supabase 客户端
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        return False, "错误：.env 中缺少 SUPABASE_URL 或 SUPABASE_KEY"

    supabase = create_client(supabase_url, supabase_key)

    try:

        file_ext = Path(local_file_path).suffix.lower()
        if file_ext in [".jpg", ".jpeg"]:
            content_type = "image/jpeg"
        elif file_ext == ".png":
            content_type = "image/png"
        elif file_ext in [".mp4", ".mkv", ".avi", ".mov"]:
            content_type = "video/mp4"
        else:
            content_type = "application/octet-stream"

        # 5. 打开本地文件并上传（rb：二进制只读模式）
        with open(local_file_path, "rb") as file:
            response = supabase.storage.from_(bucket_name).upload(
                path=storage_file_path,  # 存储到 Supabase 的路径
                file=file,
                file_options={"content-type": content_type}
            )
        print(f"From {local_file_path} Saved to {storage_file_path}")
        return True, "success"
    except Exception as e:
        return False, f"未知错误：{str(e)}"
