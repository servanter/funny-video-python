from dataclasses import dataclass
from typing import List

@dataclass
class Video:
    """
    视频信息类
    """
    file_path: str
    upload_dir: str
    first_image_url: str = ""
    result_video_url: str = ""
    duration: str = None
    snapshots: List[str] = None
    funnies: List[str] = None
    seconds: List[int] = None
    video_segments: List[str] = None
    funny_segments: List[str] = None

@dataclass
class UploadVideo:
    result_video_url: str
    first_image_url:str
    duration: str
    title: str
    description: str
    user_id: int
