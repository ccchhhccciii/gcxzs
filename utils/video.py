import re
import random
import threading
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

def parse_subtitles(subtitle_file):
    """
    解析字幕文件,提取每一行的序号、时间段和文本内容。
    返回一个包含所有字幕信息的列表。
    """
    subtitles = []
    with open(subtitle_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    subtitle_pattern = re.compile(
        r"(\d+)\n(\d\d:\d\d:\d\d,\d\d\d) --\> (\d\d:\d\d:\d\d,\d\d\d)\n(.*?)\n",
        re.DOTALL
    )
    for match in re.finditer(subtitle_pattern, ''.join(lines)):
        index, start_time, end_time, text = match.groups()
        start_hours, start_minutes, start_seconds_ms = start_time.split(':')
        end_hours, end_minutes, end_seconds_ms = end_time.split(':')
        start_seconds, start_milliseconds = map(int, start_seconds_ms.split(','))
        end_seconds, end_milliseconds = map(int, end_seconds_ms.split(','))
        start_time_ms = int(start_hours) * 3600000 + int(start_minutes) * 60000 + start_seconds * 1000 + start_milliseconds
        end_time_ms = int(end_hours) * 3600000 + int(end_minutes) * 60000 + end_seconds * 1000 + end_milliseconds
        duration_ms = end_time_ms - start_time_ms
        subtitles.append({
            'index': int(index),
            'start_time': start_time,
            'end_time': end_time,
            'text': text.strip(),
            'duration_ms': duration_ms
        })
    return subtitles

def group_videos(video_dir):
    """
    将视频文件根据文件名前缀分组,确保每组中不包含连续的素材片段。
    并按照视频长度对每个组进行降序排序。
    返回一个字典,其中键为文件名前缀,值为该前缀对应的视频文件路径列表。
    """
    video_groups = {}
    for video_file in os.listdir(video_dir):
        if video_file.endswith(('.mp4', '.avi', '.mov')):
            prefix = video_file.split('_')[0]
            if prefix not in video_groups:
                video_groups[prefix] = []
            video_path = os.path.join(video_dir, video_file)
            video_groups[prefix].append((video_path, VideoFileClip(video_path).duration))
    for group in video_groups.values():
        group.sort(key=lambda x: x[1], reverse=True)
    return {prefix: [item[0] for item in group] for prefix, group in video_groups.items()}

def generate_video(subtitles, video_dir, output_file, fps=30, target_resolution_str='1280x720', progress_callback=None, temp_dir="temp"):
    random.seed(os.urandom(4))  # 设置随机种子,确保每次调用函数时结果不同
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    height, width = map(int, target_resolution_str.split('x'))
    video_groups = group_videos(video_dir)
    clips = []
    total_duration = 0
    for i, subtitle in enumerate(subtitles):
        duration = subtitle['duration_ms'] / 1000
        available_groups = [group for group in video_groups.values() if group]
        clip = None
        while available_groups:
            group = random.choice(available_groups)
            if group:
                video_file = group.pop(0)
                video = VideoFileClip(video_file, target_resolution=(width, height))
                if video.duration >= duration:
                    clip = video.subclip(0, duration)
                    break
                else:
                    matched_clip = None
                    for other_group in available_groups:
                        if other_group:
                            other_video_file = other_group.pop(0)
                            other_video = VideoFileClip(other_video_file, target_resolution=(width, height))
                            if other_video.duration >= duration:
                                matched_clip = other_video.subclip(0, duration)
                                break
                    if matched_clip:
                        clip = matched_clip
                        break
                    video.close()
            available_groups.remove(group)
        if clip is None:
            raise ValueError("无法找到足够长的视频片段")
        clips.append(clip)
        total_duration += duration
        if progress_callback:
            progress_callback(i + 1, len(subtitles))
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_file, fps=fps, logger=None)
    for clip in clips:
        clip.close()

def start_generate_video(subtitles, video_dir, output_file, fps, target_resolution_str):
    progress_callback = lambda current, total: update_progress_bar(current, total)
    thread = threading.Thread(target=generate_video, args=(subtitles, video_dir, output_file, fps, target_resolution_str, progress_callback))
    thread.start()
    # 在这里可以显示一个进度条或进度指示器
    thread.join()
    # 视频生成完成后的界面更新逻辑
    print("视频生成线程结束")

def update_progress_bar(current, total):
    # 在这里更新进度条的进度
    progress = current / total * 100
    print(f"视频生成进度: {progress}%")

# 示例用法
if __name__ == "__main__":
    subtitle_file = "path/to/subtitle/file.srt"
    video_dir = "path/to/video/directory"
    output_file = "path/to/output/video.mp4"
    fps = 30
    target_resolution_str = "1280x720"
    subtitles = parse_subtitles(subtitle_file)
    start_generate_video(subtitles, video_dir, output_file, fps, target_resolution_str)