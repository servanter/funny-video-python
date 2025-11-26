import subprocess
import re
import os

def extract_video_params(original_video_path):
    """仅用ffmpeg提取视频参数，重点修正分辨率和音频比特率提取"""
    try:
        # 执行ffmpeg -i，获取stderr输出（元数据在这里）
        result = subprocess.run(
            ["ffmpeg", "-i", original_video_path],
            capture_output=True,
            text=True
        )
        output = result.stderr
        if not output:
            raise ValueError("无法获取视频信息，文件可能损坏或路径错误")
    except Exception as e:
        raise ValueError(f"执行ffmpeg失败：{str(e)}")

    params = {}

    # ------------------------------
    # 1. 修正：提取视频分辨率（精准定位视频流中的宽高）
    # 匹配规则：针对 "Video: ..., 720x1280, ..." 格式
    video_resolution_match = re.search(
        r"Stream #0:0.*?Video:.*?, (\d+)x(\d+),",  # 限定在Video字段后、逗号前的分辨率
        output,
        re.DOTALL
    )
    if video_resolution_match:
        params["width"] = video_resolution_match.group(1)    # 720
        params["height"] = video_resolution_match.group(2)   # 1280
    else:
        raise ValueError("无法提取视频分辨率，请检查视频格式")


    # 2. 提取视频时长（不变）
    duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", output)
    if duration_match:
        hours = int(duration_match.group(1))
        minutes = int(duration_match.group(2))
        seconds = float(duration_match.group(3))
        params["duration"] = round(hours * 3600 + minutes * 60 + seconds, 1)
    else:
        params["duration"] = 7.2  # 默认7.2秒（匹配你的视频时长）


    # 3. 提取视频帧率（不变）
    fps_match = re.search(r"Stream #0:0.*?(\d+)\s+fps", output)
    params["fps"] = fps_match.group(1) if fps_match else "30"


    # 4. 提取视频Profile（不变）
    profile_match = re.search(r"Stream #0:0.*?H\.264 \((\w+)\)", output)
    params["video_profile"] = profile_match.group(1) if profile_match else "high"


    # ------------------------------
    # 5. 修正：提取音频比特率（兼容数字与kb/s间的空格）
    # 匹配规则：针对 "49 kb/s" 或 "49kb/s" 格式
    audio_stream_match = re.search(r"Stream #0:1.*?Audio:.*?, (\d+)\s*kb/s", output)
    has_audio = bool(audio_stream_match)
    params["has_audio"] = has_audio

    if has_audio:
        # 提取音频比特率（如49 → 49k）
        params["audio_bitrate"] = f"{audio_stream_match.group(1)}k"
        # 提取音频采样率
        sample_rate_match = re.search(r"Stream #0:1.*?(\d+)\s+Hz", output)
        params["audio_sample_rate"] = sample_rate_match.group(1) if sample_rate_match else "48000"
        # 提取音频声道
        channel_match = re.search(r"Stream #0:1.*?(mono|stereo)", output)
        params["audio_channel"] = channel_match.group(1) if channel_match else "mono"
    else:
        # 无音频时置空
        params["audio_sample_rate"] = ""
        params["audio_channel"] = ""
        params["audio_bitrate"] = ""

    return params


def generate_ffmpeg_command(original_video_path, extracted_img_path, output_video_path):
    """生成完整ffmpeg命令（参数已修正）"""
    params = extract_video_params(original_video_path)

    if params["has_audio"]:
        cmd = (
            f'ffmpeg -loop 1 '
            f'-i "{extracted_img_path}" '
            f'-f lavfi -i anullsrc=channel_layout={params["audio_channel"]}:sample_rate={params["audio_sample_rate"]} '
            f'-t {params["duration"]} '
            f'-r {params["fps"]} '
            f'-vf "scale={params["width"]}:{params["height"]}, format=yuv420p" '  # 修正后的scale参数
            f'-c:v libx264 '
            f'-profile:v {params["video_profile"]} '
            f'-level:v 3.0 '
            f'-c:a aac '
            f'-b:a {params["audio_bitrate"]} '  # 修正后的音频比特率
            f'-movflags +faststart '
            f'"{output_video_path}"'
        )
    else:
        cmd = (
            f'ffmpeg -loop 1 '
            f'-i "{extracted_img_path}" '
            f'-t {params["duration"]} '
            f'-r {params["fps"]} '
            f'-vf "scale={params["width"]}:{params["height"]}, format=yuv420p" '
            f'-c:v libx264 '
            f'-profile:v {params["video_profile"]} '
            f'-level:v 3.0 '
            f'-an '
            f'-movflags +faststart '
            f'"{output_video_path}"'
        )

    return cmd


# ------------------------------
# 使用示例（替换为你的实际路径）
# ------------------------------
if __name__ == "__main__":
    original_video = "uploads/1761241469/65480800.mp4"  # 你的原始视频路径
    extracted_img = "uploads/1761241469/funnies/funny_3s.jpg"  # 截取的图片路径
    output_video = "uploads/1761241469/generated_video.mp4"   # 生成的视频路径

    if not os.path.exists(original_video):
        print(f"错误：原始视频不存在 → {original_video}")
    else:
        try:
            ffmpeg_cmd = generate_ffmpeg_command(original_video, extracted_img, output_video)
            print("✅ 生成的ffmpeg命令（已修正分辨率和音频比特率）：")
            print("-" * 80)
            print(ffmpeg_cmd)
            print("-" * 80)

            # 如需直接执行命令，取消下面两行注释
            # subprocess.run(ffmpeg_cmd, shell=True, check=True)
            # print(f"\n✅ 视频生成完成 → {output_video}")
        except Exception as e:
            print(f"\n❌ 处理失败：{str(e)}")