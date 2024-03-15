import mido
from midi2audio import FluidSynth
import wave
import subprocess
import os
from pretty_midi import PrettyMIDI, Note, note_number_to_name
from PyQt5.QtWidgets import QMessageBox

# 初始化全局变量
sound_font = r"D:\\dev\\midi2srt\\sf2\\CREATIVE_8MBGM.SF2"  # 在这里初始化 sound_font 全局变量

def ticks_to_seconds(ticks, ticks_per_beat, tempo):
    # MIDI ticks转换为秒
    return ticks / ticks_per_beat * (tempo / 1000000.0)

def midi_to_wav(midi_file_path, output_wav_path, sound_font):
    command = [
        "fluidsynth",
        "-ni",
        sound_font,
        midi_file_path,
        "-F", output_wav_path,
        "-r", "44100"
    ]
    subprocess.run(command, check=True)

# 获取WAV文件的总时长
def get_wav_duration(wav_file_path):
    with wave.open(wav_file_path, 'r') as w:
        frames = w.getnframes()
        rate = w.getframerate()
        duration = frames / float(rate)
        return duration

# 解析MIDI文件获取音符事件
def parse_midi_notes(midi_file_path):
    midi_data = PrettyMIDI(midi_file_path)
    notes_events = []
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            start_time = note.start
            end_time = note.end
            note_number = note.pitch
            note_name = note_number_to_name(note_number)  # 使用pretty_midi的函数获取音符名称
            notes_events.append((note_name, start_time, end_time))
    return notes_events

# 将音符事件与WAV文件同步并生成SRT内容
def adjust_and_generate_srt_lines(notes_events):
    # 首先按照开始时间对事件进行排序
    notes_events.sort(key=lambda x: x[1])
    adjusted_notes_events = []
    last_end_time = 0
    for note_name, start_time, end_time in notes_events:
        # 如果当前音符开始时间早于上一个音符的结束时间,则合并时间段
        if start_time < last_end_time:
            start_time = last_end_time
        # 如果有时间间隙,将上一个音符的结束时间调整到当前音符的开始时间
        if start_time > last_end_time and adjusted_notes_events:
            adjusted_notes_events[-1] = (adjusted_notes_events[-1][0], adjusted_notes_events[-1][1], start_time)
        adjusted_notes_events.append((note_name, start_time, end_time))
        last_end_time = end_time

    # 生成SRT内容
    srt_lines = []
    current_index = 1
    for note_name, start_time, end_time in adjusted_notes_events:
        start_str = format_time(start_time)
        end_str = format_time(end_time)
        srt_lines.append(f"{current_index}\n{start_str} --> {end_str}\n{note_name}\n\n")
        current_index += 1
    return srt_lines

def format_time(time_in_seconds):
    hours = int(time_in_seconds // 3600)
    minutes = int((time_in_seconds % 3600) // 60)
    seconds = time_in_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

def generate_srt(midi_file_path, output_directory_path):
    if not midi_file_path or not output_directory_path:
        raise ValueError("请确保选择了MIDI文件和输出目录")

    # 获取MIDI文件的基本名称(不包括扩展名)
    base_name = os.path.splitext(os.path.basename(midi_file_path))[0]

    # 将MIDI转换为WAV音频文件,并保存在与MIDI文件相同的目录下
    wav_temp_path = os.path.join(os.path.dirname(midi_file_path), f"{base_name}.wav")
    midi_to_wav(midi_file_path, wav_temp_path, sound_font)

    # 获取WAV文件的总时长
    wav_duration = get_wav_duration(wav_temp_path)

    # 解析MIDI文件获取音符事件
    notes_events = parse_midi_notes(midi_file_path)

    # 生成SRT内容,包括调整重叠和间隙
    srt_lines = adjust_and_generate_srt_lines(notes_events)

    # 生成SRT内容并保存到输出目录,使用MIDI文件基本名称作为SRT文件名
    srt_filename = f"{base_name}.srt"
    output_full_path = os.path.join(output_directory_path, srt_filename)

    # 写入SRT文件
    with open(output_full_path, 'w', encoding='utf-8') as f:
        f.writelines(srt_lines)

    # 清理临时WAV文件(可选)
    # os.remove(wav_temp_path)

    QMessageBox.information(None, "成功", f"SRT文件已保存到: {output_full_path}")

__all__ = ['midi_to_wav', 'get_wav_duration', 'parse_midi_notes', 'adjust_and_generate_srt_lines', 'generate_srt']