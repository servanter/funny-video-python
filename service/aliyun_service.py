import os
import requests
import base64
from typing import List
from dataclasses import dataclass
from model.video import Video

# 阿里云API配置
DASHSCOPE_API_KEY = "sk-7621a4ada7d445ed825c22243b380e97"  # 替换为你的阿里云API Key
ALIYUN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
PROMPT="“生成抖音短视频适用的‘灵魂画手’风格线框图：基于提供的原图内容，用模拟人手绘制的自然线条呈现，线条粗细有轻微不规则变化，边缘带极淡笔触纹理（非机械平滑线条）；优先保留原图主体轮廓和关键特征，背景【纯白色】适当简化不抢镜；线条颜色用高对比度的黑色或深灰色，可在主体边缘加 1-2 处小涂鸦元素（如小爱心、小星星）增加趣味感；整体画风轻松、不刻板，符合抖音短平快的视觉传播节奏，适合直接作为短视频画面或转场素材。”"

def generate_funny_images(video: Video):
    """
    调用阿里云大模型接口并下载生成的图片
    :param video: Video 对象，包含 snapshots 和 upload_dir
    """
    if not video.snapshots:
        print("没有可用的截图，跳过处理")
        return

    # 创建 funnies 文件夹
    funnies_dir = os.path.join(video.upload_dir, "funnies")
    os.makedirs(funnies_dir, exist_ok=True)

    for snapshot_path in video.snapshots:
        # 读取图片并转换为 Base64
        with open(snapshot_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            mime_type = "image/jpeg"  # 假设图片为 JPEG 格式
            base64_data = f"data:{mime_type};base64,{base64_image}"

        # 调用阿里云接口
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
        }
        payload = {
            "model": "qwen-image-edit-plus",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": base64_data},
                            {"text": PROMPT}
                        ]
                    }
                ]
            },
            "parameters": {
                "negative_prompt": " ",
                "watermark": False
            }
        }

        try:
            response = requests.post(ALIYUN_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # 提取图片 URL 并下载
            if "output" in result and "choices" in result["output"] and len(result["output"]["choices"]) > 0:
                content = result["output"]["choices"][0].get("message", {}).get("content", [])
                if content and "image" in content[0]:
                    image_url = content[0]["image"]
                    # 生成保存路径（与 snapshots 对称）
                    snapshot_name = os.path.basename(snapshot_path)
                    funny_name = f"funny_{snapshot_name.split('_')[1]}"
                    funny_path = os.path.join(funnies_dir, funny_name)

                    # 下载图片
                    image_response = requests.get(image_url)
                    image_response.raise_for_status()
                    with open(funny_path, "wb") as f:
                        f.write(image_response.content)
                    print(f"成功下载并保存图片: {funny_path}")
                    
                    # 将 funny_path 添加到 Video 对象的 funnies 数组中
                    if video.funnies is None:
                        video.funnies = []
                    video.funnies.append(funny_path)
                else:
                    print(f"未找到图片 URL: {response.text}")
            else:
                print(f"未找到图片 URL: {response.text}")
        except Exception as e:
            print(f"调用阿里云接口失败: {e}")