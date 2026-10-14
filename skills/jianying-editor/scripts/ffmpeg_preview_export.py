"""Compose a playable MP4 from a JianYing draft timeline via system ffmpeg.

This is a preview mix of video + audio tracks. JianYing-only text, effects,
transitions and filters are not rendered.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

from utils.errors import InfraError, UserInputError
from utils.ffmpeg_bin import require_ffmpeg
from utils.formatters import find_draft_content_path, get_all_drafts, get_default_drafts_root

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
UNSAFE_NAME_CHARS = '\\/:*?"<>|'


def default_output_path(draft_name: str) -> str:
    """macOS -> ~/Movies/草稿名.mp4; Windows/Linux -> ~/Videos/草稿名.mp4."""
    safe = "".join(ch for ch in draft_name if ch not in UNSAFE_NAME_CHARS).strip() or "draft"
    home = os.path.expanduser("~")
    folder = os.path.join(home, "Movies") if sys.platform == "darwin" else os.path.join(home, "Videos")
    return os.path.join(folder, f"{safe}.mp4")


RES_SHORT_SIDE = {
    "480": 480,
    "720": 720,
    "1080": 1080,
    "2K": 1440,
    "4K": 2160,
    "8K": 4320,
}


def _us_to_s(value: Any) -> float:
    try:
        return float(value) / 1_000_000.0
    except (TypeError, ValueError):
        return 0.0


def _even(value: int) -> int:
    value = max(2, int(value))
    return value if value % 2 == 0 else value - 1


def _speed_of(segment: Dict[str, Any]) -> float:
    speed = segment.get("speed")
    if isinstance(speed, dict):
        speed = speed.get("speed", 1.0)
    try:
        numeric = float(speed)
    except (TypeError, ValueError):
        return 1.0
    return numeric if numeric > 0 else 1.0


def _material_path(material: Dict[str, Any]) -> str:
    return str(material.get("path") or material.get("media_path") or "").strip()


def _is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXTS


def find_draft_dir(name: str, drafts_root: Optional[str] = None) -> str:
    root = os.path.abspath(drafts_root or get_default_drafts_root())
    for item in get_all_drafts(root):
        if item["name"] == name:
            return item["path"]
    raise UserInputError(f"Draft not found: {name} (root={root})")


def output_size(canvas_w: int, canvas_h: int, resolution: Optional[str]) -> Tuple[int, int]:
    width, height = _even(canvas_w), _even(canvas_h)
    if not resolution:
        return width, height
    short = RES_SHORT_SIDE.get(str(resolution).upper() if resolution != "2K" else "2K")
    if short is None:
        raise UserInputError(
            f"Unsupported resolution: {resolution} (allowed: {', '.join(RES_SHORT_SIDE)})"
        )
    if height >= width:
        out_w = _even(short)
        out_h = _even(round(height / float(width) * out_w))
    else:
        out_h = _even(short)
        out_w = _even(round(width / float(height) * out_h))
    return out_w, out_h


def collect_clips(content: Dict[str, Any]) -> Dict[str, Any]:
    materials = content.get("materials") or {}
    videos = {item["id"]: item for item in materials.get("videos") or [] if item.get("id")}
    audios = {item["id"]: item for item in materials.get("audios") or [] if item.get("id")}
    canvas = content.get("canvas_config") or {}
    canvas_w = int(canvas.get("width") or 1920)
    canvas_h = int(canvas.get("height") or 1080)

    video_clips: List[Dict[str, Any]] = []
    audio_clips: List[Dict[str, Any]] = []
    text_tracks: List[str] = []
    missing: List[str] = []
    duration_s = _us_to_s(content.get("duration") or 0)

    tracks = list(content.get("tracks") or [])
    tracks.sort(key=lambda track: int(track.get("render_index") or 0))

    for track in tracks:
        track_type = str(track.get("type") or "")
        track_name = str(track.get("name") or "")
        if track_type == "text":
            text_tracks.append(track_name)
            continue
        if track_type not in {"video", "audio"}:
            continue
        for segment in track.get("segments") or []:
            if segment.get("visible") is False:
                continue
            target = segment.get("target_timerange") or {}
            source = segment.get("source_timerange") or {}
            start = _us_to_s(target.get("start") or 0)
            dur = _us_to_s(target.get("duration") or 0)
            if dur <= 0:
                continue
            src_start = _us_to_s(source.get("start") or 0)
            material = videos.get(segment.get("material_id")) or audios.get(
                segment.get("material_id")
            ) or {}
            path = _material_path(material)
            if not path:
                continue
            if not os.path.isfile(path):
                missing.append(path)
                continue
            volume = segment.get("volume")
            try:
                volume_f = 1.0 if volume is None else float(volume)
            except (TypeError, ValueError):
                volume_f = 1.0
            clip = {
                "path": path,
                "start": start,
                "duration": dur,
                "src_start": src_start,
                "volume": volume_f,
                "speed": _speed_of(segment),
                "track": track_name,
                "image": _is_image(path),
            }
            duration_s = max(duration_s, start + dur)
            if track_type == "video":
                video_clips.append(clip)
            else:
                audio_clips.append(clip)

    return {
        "canvas_w": canvas_w,
        "canvas_h": canvas_h,
        "duration_s": duration_s,
        "video_clips": video_clips,
        "audio_clips": audio_clips,
        "text_tracks": text_tracks,
        "missing": missing,
    }


def build_ffmpeg_command(
    clips: Dict[str, Any],
    output_path: str,
    ffmpeg: str,
    fps: int,
    width: int,
    height: int,
) -> List[str]:
    video_clips: List[Dict[str, Any]] = clips["video_clips"]
    audio_clips: List[Dict[str, Any]] = clips["audio_clips"]
    total = float(clips["duration_s"])
    if not video_clips:
        raise UserInputError("Draft has no video clips to export.")
    if total <= 0:
        raise UserInputError("Draft duration is 0.")

    cmd: List[str] = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    filters: List[str] = [
        f"color=c=black:s={width}x{height}:d={total:.3f}:r={fps},format=yuv420p[base0]"
    ]

    for clip in video_clips:
        if clip["image"]:
            cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{clip['duration']:.3f}", "-i", clip["path"]]
        else:
            cmd += ["-i", clip["path"]]
    for clip in audio_clips:
        cmd += ["-i", clip["path"]]

    for index, clip in enumerate(video_clips):
        speed = clip["speed"]
        src_start = clip["src_start"]
        dur = clip["duration"] * speed
        start = clip["start"]
        filters.append(
            f"[{index}:v]trim=start={src_start:.3f}:duration={dur:.3f},"
            f"setpts=(PTS-STARTPTS)/{speed:.6f},"
            f"fps={fps},scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,"
            f"setpts=PTS+{start:.3f}/TB[v{index}]"
        )
        prev = f"base{index}"
        nxt = f"base{index + 1}"
        end = start + clip["duration"]
        filters.append(
            f"[{prev}][v{index}]overlay=0:0:repeatlast=0:eof_action=pass:"
            f"enable='between(t\\,{start:.3f}\\,{end:.3f})'[{nxt}]"
        )

    vout = f"[base{len(video_clips)}]"
    filters.append(f"{vout}format=yuv420p[vout]")

    alabels: List[str] = []
    audio_base = len(video_clips)
    for index, clip in enumerate(audio_clips):
        speed = clip["speed"]
        src_start = clip["src_start"]
        dur = clip["duration"] * speed
        delay_ms = max(0, int(round(clip["start"] * 1000)))
        volume = clip["volume"]
        chain = (
            f"[{audio_base + index}:a]atrim=start={src_start:.3f}:duration={dur:.3f},"
            f"asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo"
        )
        if abs(speed - 1.0) > 0.001:
            chain += f",atempo={speed:.6f}"
        if delay_ms:
            chain += f",adelay={delay_ms}|{delay_ms}"
        if abs(volume - 1.0) > 0.001:
            chain += f",volume={volume:.4f}"
        chain += f"[a{index}]"
        filters.append(chain)
        alabels.append(f"[a{index}]")

    if not alabels:
        filters.append(f"anullsrc=r=48000:cl=stereo:d={total:.3f}[aout]")
    elif len(alabels) == 1:
        filters.append(f"{alabels[0]}apad=whole_dur={total:.3f}[aout]")
    else:
        filters.append(
            "".join(alabels)
            + f"amix=inputs={len(alabels)}:duration=longest:dropout_transition=0:normalize=0,"
            f"apad=whole_dur={total:.3f}[aout]"
        )

    cmd += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[vout]",
        "-map",
        "[aout]",
        "-t",
        f"{total:.3f}",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "medium",
        "-crf",
        "16",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        output_path,
    ]
    return cmd


def export_draft_preview(
    draft_name: str,
    output_path: str,
    drafts_root: Optional[str] = None,
    resolution: Optional[str] = None,
    framerate: Optional[str] = None,
) -> Dict[str, Any]:
    draft_dir = find_draft_dir(draft_name, drafts_root)
    content_path = find_draft_content_path(draft_dir)
    if not content_path:
        raise UserInputError(f"Missing draft_info.json: {draft_dir}")

    with open(content_path, "r", encoding="utf-8") as handle:
        content = json.load(handle)

    clips = collect_clips(content)
    if clips["missing"]:
        raise InfraError("Media files missing:\n" + "\n".join(clips["missing"][:8]))

    fps = 30
    if framerate:
        try:
            fps = int(float(framerate))
        except ValueError as exc:
            raise UserInputError(f"Unsupported framerate: {framerate}") from exc
        if fps <= 0:
            raise UserInputError(f"Unsupported framerate: {framerate}")

    width, height = output_size(clips["canvas_w"], clips["canvas_h"], resolution)
    ffmpeg = require_ffmpeg()
    output_path = os.path.abspath(os.path.expanduser(output_path))
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    cmd = build_ffmpeg_command(clips, output_path, ffmpeg, fps, width, height)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0 or not os.path.isfile(output_path):
        err = (proc.stderr or proc.stdout or "ffmpeg failed").strip()
        raise InfraError(err[-2000:] if err else "ffmpeg preview export failed")

    return {
        "draft": draft_name,
        "draft_dir": draft_dir,
        "output": output_path,
        "mode": "ffmpeg_preview",
        "width": width,
        "height": height,
        "fps": fps,
        "duration_s": clips["duration_s"],
        "video_clips": len(clips["video_clips"]),
        "audio_clips": len(clips["audio_clips"]),
        "text_tracks_skipped": clips["text_tracks"],
        "burned_text": False,
        "size_bytes": os.path.getsize(output_path),
    }
