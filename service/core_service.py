import time

from fastapi import UploadFile

from model.video import Video, UploadVideo
from service import aliyun_service

from supa.db_utils import insert_video_with_supabase_sdk
from supa.upload_utils import upload_to_supabase

import subprocess
import re
import os


def extract_video_image(video, moments: str):
    """
    截取视频的指定时间点的图片
    :param video: Video 对象，包含视频文件路径和上传目录
    """
    # 创建 snapshots 文件夹
    snapshots_dir = os.path.join(video.upload_dir, "snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)

    # 初始化 snapshots 数组
    video.snapshots = []
    video.seconds = []

    # 检查视频时长是否足够
    if not video.duration:
        print("无法获取视频时长，跳过截图")
        return

    # 解析视频时长（格式为 HH:MM:SS.xx）
    hours, minutes, seconds = map(float, video.duration.split(":"))
    total_seconds = hours * 3600 + minutes * 60 + seconds

    # 定义需要截取的时间点（秒）

    timestamps = str2int(moments)
    print('timestamps------>', timestamps)

    for timestamp in timestamps:
        if timestamp > total_seconds:
            print(f"视频时长不足 {timestamp} 秒，跳过截图")
            continue
        video.seconds.append(timestamp)

        # 使用 ffmpeg 截取图片
        output_path = os.path.join(snapshots_dir, f"snapshot_{timestamp}s.jpg")
        cmd = f"ffmpeg -ss {timestamp} -i {video.file_path} -vf \"scale=960:720\" -s 960x720 -vframes 1 -q:v 2 {output_path}"
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"成功截取第 {timestamp} 秒的图片: {output_path}")
            print(f"截图cmd: {cmd}")
            video.snapshots.append(output_path)
        except subprocess.CalledProcessError as e:
            print(f"截取第 {timestamp} 秒图片失败: {e}")

def str2int(s):
    seconds = [int(i.strip()) for i in s.split(',') if i.strip()]
    seconds.sort()
    return seconds

def extract_video_segments(video):
    """
    根据 seconds 数组截取视频片段
    :param video: Video 对象，包含 file_path 和 seconds 数组
    """
    if not video.seconds:
        print("seconds 数组为空，跳过视频片段截取")
        return
    video.video_segments = []

    # 创建 result 文件夹
    result_dir = os.path.join(video.upload_dir, "result")
    os.makedirs(result_dir, exist_ok=True)

    # 截取视频片段
    for i in range(len(video.seconds) + 1):
        start_time = 0 if i == 0 else video.seconds[i - 1]
        end_time = video.seconds[i] if i < len(video.seconds) else None

        # 输出文件名
        output_path = os.path.join(result_dir, f"segment_{i + 1}.mp4")

        # 使用 ffmpeg 截取视频片段
        if end_time is not None:
            duration = end_time - start_time
            cmd = f"ffmpeg -ss {start_time} -i {video.file_path} -t {duration} -vf \"scale=960:720, format=yuv420p\" -r 30 -c:v libx264 -profile:v high -level:v 3.0 -c:a aac -b:a 51k -ar 48000 -ac 1 -movflags +faststart {output_path}"
        else:
            cmd = f"ffmpeg -ss {start_time} -i {video.file_path}  -vf \"scale=960:720, format=yuv420p\" -r 30 -c:v libx264 -profile:v high -level:v 3.0 -c:a aac -b:a 51k -ar 48000 -ac 1 -movflags +faststart {output_path}"
            # cmd = f"ffmpeg -ss {start_time} -i {video.file_path} -c copy {output_path}"

        print(f"执行视频片段截取命令: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"成功截取视频片段 {i + 1}: {output_path}")
            video.video_segments.append(output_path)

        except subprocess.CalledProcessError as e:
            print(f"截取视频片段 {i + 1} 失败: {e}")



def extract_first_frame(
        video_path: str,
        output_path: str,
        quality: int = 2,  # 图片质量（1-31，越小质量越高）
) -> bool:
    """
    使用 FFmpeg 提取视频第一帧

    Args:
        video_path: 视频文件路径（绝对路径或相对路径）
        output_path: 输出图片路径（支持 jpg/png 等格式）
        ffmpeg_path: FFmpeg 可执行文件路径（未添加环境变量时需指定）
        quality: JPEG 质量（仅对 jpg 有效），1-31，默认 2（高质量）
        width: 输出图片宽度（None 表示保持原比例）
        height: 输出图片高度（None 表示保持原比例）

    Returns:
        bool: 提取成功返回 True，失败返回 False
    """
    # 检查视频文件是否存在
    if not os.path.exists(video_path):
        print(f"错误：视频文件不存在 - {video_path}")
        return False

    # 构建命令参数
    cmd = [
        "ffmpeg",
        "-i", video_path,  # 输入视频
        "-vframes", "1",  # 只取1帧
        "-q:v", str(quality),  # 图片质量
        "-y",  # 覆盖已存在的输出文件

    ]

    # 添加输出路径
    cmd.append(output_path)

    try:
        # 执行命令，隐藏输出
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            shell=False  # Windows 系统如果路径有空格，可改为 shell=True
        )
        print(f"第一帧提取成功：{output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误：提取失败 - {e}")
        return False
    except FileNotFoundError:
        print("错误：未找到 FFmpeg，请检查是否安装并添加到环境变量")
        return False


def generate_funny_segments(video):
    """不变，保留原逻辑"""
    if not video.funnies:
        print("funnies 数组为空，跳过视频片段生成")
        return

    if not hasattr(video, 'funny_segments') or video.funny_segments is None:
        video.funny_segments = []

    result_dir = os.path.join(video.upload_dir, "result")
    os.makedirs(result_dir, exist_ok=True)

    for funny in video.funnies:
        funny_name = os.path.splitext(os.path.basename(funny))[0]
        output_path = os.path.join(result_dir, f"{funny_name}.mp4")

        print(f"video=====: {video.file_path}")
        cmd = generate_ffmpeg_command(video.file_path, funny, output_path)
        print(f"执行图片转视频命令: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"成功生成视频片段: {output_path}")
            video.funny_segments.append(output_path)
        except subprocess.CalledProcessError as e:
            print(f"生成视频片段失败: {e}")


def extract_video_params(original_video_path):
    """修正：Profile 提取后转为小写，适配 libx265"""
    try:
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

    # 1. 提取分辨率（不变）
    video_resolution_match = re.search(
        r"Stream #0:0.*?Video:.*?, (\d+)x(\d+),",
        output,
        re.DOTALL
    )
    if video_resolution_match:
        params["width"] = video_resolution_match.group(1)
        params["height"] = video_resolution_match.group(2)
    else:
        params["width"] = 960
        params["height"] = 720

    # 2. 提取时长（不变）
    duration_match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", output)
    if duration_match:
        hours = int(duration_match.group(1))
        minutes = int(duration_match.group(2))
        seconds = float(duration_match.group(3))
        params["duration"] = round(hours * 3600 + minutes * 60 + seconds, 1)
    else:
        params["duration"] = 7.2

    # 3. 提取帧率（不变）
    fps_match = re.search(r"Stream #0:0.*?(\d+)\s+fps", output)
    params["fps"] = fps_match.group(1) if fps_match else "30"

    # ------------------------------
    # 【关键修正】Profile 提取后转为小写（适配 libx265）
    video_codec_match = re.search(
        r"Stream #0:0.*?Video: (H\.264|hevc) \((\w+)\)",
        output,
        re.DOTALL
    )
    if video_codec_match:
        params["video_codec"] = video_codec_match.group(1)
        # 转为小写：Main → main
        params["video_profile"] = video_codec_match.group(2).lower()
    else:
        params["video_codec"] = "H.264"
        params["video_profile"] = "high"  # H.264 小写也兼容

    # 4. 提取音频参数（不变）
    audio_stream_match = re.search(r"Stream #0:1.*?Audio:.*?, (\d+)\s*kb/s", output)
    has_audio = bool(audio_stream_match)
    params["has_audio"] = has_audio

    if has_audio:
        params["audio_bitrate"] = f"{audio_stream_match.group(1)}k"
        sample_rate_match = re.search(r"Stream #0:1.*?(\d+)\s+Hz", output)
        params["audio_sample_rate"] = sample_rate_match.group(1) if sample_rate_match else "48000"
        channel_match = re.search(r"Stream #0:1.*?(mono|stereo)", output)
        params["audio_channel"] = channel_match.group(1) if channel_match else "mono"
    else:
        params["audio_sample_rate"] = ""
        params["audio_channel"] = ""
        params["audio_bitrate"] = ""

    return params


def generate_ffmpeg_command(original_video_path, extracted_img_path, output_video_path):
    """不变，保留原逻辑（参数已在 extract 中修正）"""
    params = extract_video_params(original_video_path)

    # if params["video_codec"] == "hevc":
    #     video_encoder = "libx265"
    # else:
    video_encoder = "libx264"

    if params["has_audio"]:
        cmd = (
            f'ffmpeg -loop 1 '
            f'-i "{extracted_img_path}" '
            f'-f lavfi -i anullsrc=channel_layout={params["audio_channel"]}:sample_rate={params["audio_sample_rate"]} '
            f'-t 3.0 '
            f'-r {params["fps"]} '
            f'-vf "scale={params["width"]}:{params["height"]}, format=yuv420p" '
            f'-c:v {video_encoder} '
            f'-profile:v high '  # 此时已为小写 main
            f'-level:v 3.0 '
            f'-c:a aac '
            f'-b:a {params["audio_bitrate"]} '
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
            f'-c:v {video_encoder} '
            f'-profile:v {params["video_profile"]} '
            f'-level:v 3.0 '
            f'-an '
            f'-movflags +faststart '
            f'"{output_video_path}"'
        )

    return cmd


def upload_and_save(video, title: str, description: str, user_id: int):
    # 获取必要信息
    merged_video_path = f"{video.upload_dir}/result/merged.mp4"
    duration = get_duration(merged_video_path)

    first_image_path = f"{video.upload_dir}/result/first_frame.jpg"
    extract_first_frame(merged_video_path, first_image_path)

    first_image_url = user_id + "/" + first_image_path.split("uploads/")[-1]
    result_video_url = user_id + "/" + merged_video_path.split("uploads/")[-1]

    print("first_image_url: ", first_image_url)
    print("result_video_url: ", result_video_url)
    insert_video_with_supabase_sdk(user_id=user_id, title=title, description=description,
                                   first_image_url=first_image_url, result_video_url=result_video_url, duration=duration)

    video.first_image_url = first_image_url
    video.result_video_url = result_video_url

    print("video result--------->: ", video)
    upload_to_supabase(
        local_file_path=first_image_path,
        storage_file_path=first_image_url  # 可选：自定义存储路径
    )

    upload_to_supabase(
        local_file_path=merged_video_path,
        storage_file_path=result_video_url  # 可选：自定义存储路径
    )




    pass


def test_save_file(uploaded_file:UploadFile, user_id: str, title: str, description:str):
    """
    保存上传的文件到以时间戳命名的文件夹中
    :param uploaded_file: 上传的文件对象（需支持 .name 和 .read() 方法）
    :return: 返回 Video 对象
    """
    # 生成当前时间戳
    timestamp = int(time.time())

    # # 创建上传目录路径
    upload_dir = os.path.join("uploads", str(timestamp))

    # # 确保目录存在
    os.makedirs(upload_dir, exist_ok=True)

    # # 保存上传的文件
    file_path = os.path.join(upload_dir, uploaded_file.filename)
    with open(file_path, "wb") as f:
        content = uploaded_file.file.read()
        f.write(content)
    try:
        file_name_without_ext, ext = os.path.splitext(file_path)
        output_path = f"{file_name_without_ext}_new{ext}"
        cmd = f"ffmpeg -i {file_path} -vf \"scale=960:720, format=yuv420p\" -r 30 -c:v libx264 -profile:v high -level:v 3.0 -c:a aac -b:a 51k -ar 48000 -ac 1 -movflags +faststart {output_path}"
        subprocess.run(cmd, shell=True, check=True)
        file_path=output_path
    except Exception as e:
        print(f"获取视频时长失败: {e}")
    print("file_path----->", file_path)

    video = Video(file_path='uploads/1762845319/madashuai_new.mp4', upload_dir='uploads/1762845319',
                  duration='00:00:10.17', first_image_url='uploads/1762845319/funnies/funny_4s.jpg',result_video_url='uploads/1762845319/result/segment_2.mp4', snapshots=['uploads/1762845319/snapshots/snapshot_4s.jpg',
                                                     'uploads/1762845319/snapshots/snapshot_8s.jpg'],
                  funnies=['uploads/1762845319/funnies/funny_4s.jpg', 'uploads/1762845319/funnies/funny_8s.jpg'],
                  seconds=[4, 8],
                  video_segments=['uploads/1762845319/result/segment_1.mp4', 'uploads/1762845319/result/segment_2.mp4',
                                  'uploads/1762845319/result/segment_3.mp4'],
                  funny_segments=['uploads/1762845319/result/funny_4s.mp4', 'uploads/1762845319/result/funny_8s.mp4']
                  )

    return video



def save_uploaded_file(uploaded_file:UploadFile, user_id: str, title: str, description:str, selected_moments: str):
    """
    保存上传的文件到以时间戳命名的文件夹中
    :param uploaded_file: 上传的文件对象（需支持 .name 和 .read() 方法）
    :return: 返回 Video 对象
    """
    # 生成当前时间戳
    timestamp = int(time.time())

    # # 创建上传目录路径
    upload_dir = os.path.join("uploads", str(timestamp))

    # # 确保目录存在
    os.makedirs(upload_dir, exist_ok=True)

    # # 保存上传的文件
    file_path = os.path.join(upload_dir, uploaded_file.filename)
    with open(file_path, "wb") as f:
        content = uploaded_file.file.read()
        f.write(content)
    try:
        file_name_without_ext, ext = os.path.splitext(file_path)
        output_path = f"{file_name_without_ext}_new{ext}"
        cmd = f"ffmpeg -i {file_path} -vf \"scale=960:720, format=yuv420p\" -r 30 -c:v libx264 -profile:v high -level:v 3.0 -c:a aac -b:a 51k -ar 48000 -ac 1 -movflags +faststart {output_path}"
        subprocess.run(cmd, shell=True, check=True)
        file_path=output_path
    except Exception as e:
        print(f"获取视频时长失败: {e}")
    print("file_path----->", file_path)

    # # 调用 ffmpeg 获取视频时长
    duration = get_duration(file_path)

    # # 创建 Video 对象
    video = Video(file_path=file_path, upload_dir=upload_dir, duration=duration if 'duration' in locals() else None)

    # # 调用截图方法
    extract_video_image(video, selected_moments)

    # # 调用阿里云接口
    aliyun_service.generate_funny_images(video)

    # # 调用视频片段截取方法
    extract_video_segments(video)

    # # 图片转视频
    generate_funny_segments(video)

    merge_video(video)

    # video = Video(file_path='uploads/1762845319/madashuai_new.mp4', upload_dir='uploads/1762845319',
    #               duration='00:00:10.17', snapshots=['uploads/1762845319/snapshots/snapshot_4s.jpg',
    #                                                  'uploads/1762845319/snapshots/snapshot_8s.jpg'],
    #               funnies=['uploads/1762845319/funnies/funny_4s.jpg', 'uploads/1762845319/funnies/funny_8s.jpg'],
    #               seconds=[4, 8],
    #               video_segments=['uploads/1762845319/result/segment_1.mp4', 'uploads/1762845319/result/segment_2.mp4',
    #                               'uploads/1762845319/result/segment_3.mp4'],
    #               funny_segments=['uploads/1762845319/result/funny_4s.mp4', 'uploads/1762845319/result/funny_8s.mp4'])

    print(f"视频处理完成: {video}")

    # # 上传文件
    upload_and_save(video, title, description, user_id)

    return video


def get_duration(file_path):
    # # 调用 ffmpeg 获取视频时长
    try:
        cmd = f"ffmpeg -i {file_path} 2>&1 | grep Duration | awk '{{print $2}}' | tr -d ','"
        duration = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        print(f"视频时长: {duration}")
        return duration
    except Exception as e:
        print(f"获取视频时长失败: {e}")

    return 0


def merge_video(video):
    """
    拼接视频片段和有趣视频片段，生成最终合并视频
    :param video: Video 对象，包含 video_segments 和 funny_segments 数组
    """
    if not video.video_segments or not video.funny_segments:
        print("video_segments 或 funny_segments 数组为空，跳过视频拼接")
        return

    # 创建 result 文件夹
    result_dir = os.path.join(video.upload_dir, "result")
    os.makedirs(result_dir, exist_ok=True)

    # 生成 list.txt 文件
    list_path = os.path.join(result_dir, "list.txt")
    with open(list_path, "w") as f:
        for i in range(len(video.video_segments)):
            f.write(f"file '{os.path.basename(video.video_segments[i])}'\n")
            if i < len(video.funny_segments):
                f.write(f"file '{os.path.basename(video.funny_segments[i])}'\n")

    # 拼接视频
    output_path = os.path.join(result_dir, "merged.mp4")
    cmd = f"ffmpeg -f concat -safe 0 -i {list_path} -stream_loop -1 -i bgm.mp3 -c:v libx264 -profile:v high -filter_complex \"[0:a]volume=1.0, aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono[a1]; [1:a]volume=0.5, aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono[a2]; [a1][a2]amerge=inputs=2, pan=stereo|c0<c0+c1|c1<c0+c1[aout]\" -map 0:v -map \"[aout]\" -c:a aac -profile:a aac_low -b:a 128k -ar 48000 -shortest {output_path}"
    print('拼接视频cmd:', cmd)
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"成功拼接视频: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"拼接视频失败: {e}")
