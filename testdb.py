import os
import socket
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
from supabase.lib.client_options import ClientOptions  # 导入超时配置类

# 加载 .env 环境变量
load_dotenv()

def insert_video_with_supabase_sdk(
        user_id: str,
        title: str,
        description: str,
        first_image_url: str,
        result_video_url: str,
        duration: str
) -> int:
    # 1. 获取并验证环境变量（打印完整URL的后缀，确认格式）
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # 打印完整URL的关键部分（确认后缀正确）
    print(f"🔍 完整 URL：{SUPABASE_URL}")  # 仅本地测试时打印，不要部署到生产！
    print(f"🔍 URL 后缀检查：{SUPABASE_URL.endswith('.supabase.co')}")  # 必须输出 True
    print(f"🔍 加载的 Key：{SUPABASE_KEY[:20]}...")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ 错误：.env 中 SUPABASE_URL 或 SUPABASE_KEY 为空")
        return -1

    # 验证 URL 格式
    if not SUPABASE_URL.startswith("https://") or not SUPABASE_URL.endswith(".supabase.co"):
        print("❌ 错误：SUPABASE_URL 格式不正确（应为 https://<项目ID>.supabase.co）")
        return -1

    # 2. 测试 DNS 解析（关键排查步骤）
    try:
        # 提取 URL 中的主机名（如 abc123xyz.supabase.co）
        host = SUPABASE_URL.replace("https://", "").split("/")[0]
        socket.gethostbyname(host)  # 测试 DNS 解析
        print(f"✅ DNS 解析成功：{host}")
    except socket.gaierror as e:
        print(f"❌ DNS 解析失败：{e} → 请检查 URL 或网络")
        return -1

    # 3. 创建 Supabase 客户端（添加超时配置，避免无限等待）
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )
    except Exception as e:
        print(f"❌ 创建客户端失败：{e}")
        return -1

    try:
        # 4. 准备数据
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "user_id": user_id,
            "title": title,
            "description": description,
            "first_image_url": first_image_url,
            "result_video_url": result_video_url,
            "update_time": current_time,
            "duration": duration
        }

        # 5. 插入数据（表名注意：Supabase 表名默认小写，若手动创建为大写需加引号）
        # 优先尝试小写表名（推荐 Supabase 表名用小写，避免大小写问题）
        table_name = "Video"  # 改为你的实际表名（小写优先）
        response = supabase.table(table_name).insert(data).execute()

        if response.data:
            new_video_id = response.data[0]["id"]
            print(f"✅ 插入成功！新视频 ID：{new_video_id}")
            return new_video_id
        else:
            print(f"❌ 插入失败：{response.error.message if response.error else '未知错误'}")
            return -1

    except Exception as e:
        print(f"❌ 插入过程错误：{e}")
        return -1

# 测试调用（本地调试用，实际使用时删除）
if __name__ == "__main__":
    insert_video_with_supabase_sdk(
        user_id="test_user_123",
        title="测试视频",
        description="测试插入功能",
        first_image_url="https://example.com/cover.jpg",
        result_video_url="https://example.com/video.mp4",
        duration="00:01:30"
    )