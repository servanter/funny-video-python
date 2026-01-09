#!/usr/bin/env python3
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supa.db_utils import insert_video_with_supabase_sdk

def main():
    """测试插入视频记录"""
    print("🚀 开始测试插入视频记录...")
    
    # 测试数据
    test_data = {
        "user_id": "test_user_001",
        "title": "测试搞笑视频",
        "description": "这是一个测试用的搞笑视频描述",
        "first_image_url": "https://example.com/test-image.jpg",
        "result_video_url": "https://example.com/test-video.mp4",
        "duration": "00:30"
    }
    
    print(f"📝 准备插入数据：")
    print(f"   用户ID: {test_data['user_id']}")
    print(f"   标题: {test_data['title']}")
    print(f"   描述: {test_data['description']}")
    print(f"   图片URL: {test_data['first_image_url']}")
    print(f"   视频URL: {test_data['result_video_url']}")
    print(f"   时长: {test_data['duration']}")
    print()
    
    # 调用插入函数
    result = insert_video_with_supabase_sdk(
        user_id=test_data["user_id"],
        title=test_data["title"],
        description=test_data["description"],
        first_image_url=test_data["first_image_url"],
        result_video_url=test_data["result_video_url"],
        duration=test_data["duration"]
    )
    
    if result > 0:
        print(f"🎉 测试成功！插入的记录ID: {result}")
    else:
        print("❌ 测试失败！")
    
    return result

if __name__ == "__main__":
    main()