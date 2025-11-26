import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# 加载 .env 环境变量
load_dotenv()

def insert_video_with_supabase_sdk(
        user_id: str,
        title: str,
        description: str,
        first_image_url: str,
        result_video_url: str,
duration:str
) -> int:
    # 1. 获取并验证环境变量（关键：确认密钥加载正确）
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # 打印前几位密钥和URL，确认没加载错（不要打印完整密钥！）
    print(f"🔍 加载的 URL：{SUPABASE_URL[:20]}...")
    print(f"🔍 加载的 Key：{SUPABASE_KEY[:20]}...")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ 错误：.env 中 SUPABASE_URL 或 SUPABASE_KEY 为空")
        return -1

    # 2. 创建 Supabase 客户端
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # 3. 准备数据（去掉 create_time，用表的默认值）
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

        # 4. 关键：根据 SQL 查询的实际表名调整这里！
        # 示例1：如果实际表名是小写 video → table('video')
        # 示例2：如果实际表名是 "Video" → table('"Video"')
        response = supabase.table('Video').insert(data).execute()  # 先试小写！

        if response.data:
            new_video_id = response.data[0]["id"]
            print(f"✅ 插入成功！新视频 ID：{new_video_id}")
            return new_video_id
        else:
            print(f"❌ 插入失败：{response.error}")
            return -1

    except Exception as e:
        print(f"❌ 错误：{e}")
        return -1