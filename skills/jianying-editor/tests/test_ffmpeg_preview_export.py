# ruff: noqa: E402

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

current_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(current_dir)
scripts_path = os.path.join(skill_root, "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from ffmpeg_preview_export import (  # noqa: E402
    build_ffmpeg_command,
    collect_clips,
    default_output_path,
    export_draft_preview,
    output_size,
)
from utils.ffmpeg_bin import find_tool, install_hint  # noqa: E402


def _us(seconds: float) -> int:
    return int(round(seconds * 1_000_000))


class TestFfmpegPreviewExport(unittest.TestCase):
    def test_default_output_path_uses_movies_on_mac(self):
        with patch("ffmpeg_preview_export.sys.platform", "darwin"):
            path = default_output_path("热点监控_说一句")
        self.assertEqual(os.path.basename(path), "热点监控_说一句.mp4")
        self.assertIn("Movies", path)

        with patch("ffmpeg_preview_export.sys.platform", "win32"):
            path = default_output_path("最终版视频")
        self.assertEqual(os.path.basename(path), "最终版视频.mp4")
        self.assertIn("Videos", path)

    def test_install_hint_gives_platform_commands(self):
        with patch("utils.ffmpeg_bin.sys.platform", "darwin"):
            text = install_hint()
        self.assertIn("brew install ffmpeg", text)
        self.assertIn("https://brew.sh", text)
        self.assertIn("ffmpeg -version", text)

        with patch("utils.ffmpeg_bin.sys.platform", "win32"):
            text = install_hint()
        self.assertIn("winget install Gyan.FFmpeg", text)
        self.assertIn("ffmpeg -version", text)

    def test_output_size_keeps_portrait_canvas(self):
        self.assertEqual(output_size(2160, 3840, None), (2160, 3840))
        self.assertEqual(output_size(2160, 3840, "1080"), (1080, 1920))
        self.assertEqual(output_size(1920, 1080, "1080"), (1920, 1080))

    def test_collect_clips_reads_volume_and_skips_text(self):
        content = {
            "canvas_config": {"width": 320, "height": 240},
            "duration": _us(2),
            "materials": {
                "videos": [{"id": "v1", "path": __file__}],
                "audios": [{"id": "a1", "path": __file__}],
            },
            "tracks": [
                {
                    "name": "VideoTrack",
                    "type": "video",
                    "segments": [
                        {
                            "material_id": "v1",
                            "target_timerange": {"start": 0, "duration": _us(2)},
                            "source_timerange": {"start": 0, "duration": _us(2)},
                            "volume": 1,
                            "speed": 1.0,
                            "visible": True,
                        }
                    ],
                },
                {
                    "name": "BGM",
                    "type": "audio",
                    "segments": [
                        {
                            "material_id": "a1",
                            "target_timerange": {"start": 0, "duration": _us(2)},
                            "source_timerange": {"start": 0, "duration": _us(2)},
                            "volume": 0.6,
                            "speed": 1.0,
                            "visible": True,
                        }
                    ],
                },
                {
                    "name": "Subtitles",
                    "type": "text",
                    "segments": [
                        {
                            "material_id": "t1",
                            "target_timerange": {"start": 0, "duration": _us(2)},
                        }
                    ],
                },
            ],
        }
        clips = collect_clips(content)
        self.assertEqual(len(clips["video_clips"]), 1)
        self.assertEqual(len(clips["audio_clips"]), 1)
        self.assertEqual(clips["audio_clips"][0]["volume"], 0.6)
        self.assertEqual(clips["text_tracks"], ["Subtitles"])
        self.assertEqual(clips["missing"], [])

        cmd = build_ffmpeg_command(clips, "out.mp4", "ffmpeg", 30, 320, 240)
        joined = " ".join(cmd)
        self.assertIn("volume=0.6000", joined)
        self.assertIn("color=c=black:s=320x240", joined)

    @unittest.skipUnless(find_tool("ffmpeg"), "ffmpeg not installed")
    def test_export_preview_mixes_real_files(self):
        ffmpeg = find_tool("ffmpeg")
        root = tempfile.mkdtemp(prefix="jy-preview-")
        try:
            video_a = os.path.join(root, "a.mp4")
            video_b = os.path.join(root, "b.mp4")
            audio = os.path.join(root, "voice.wav")
            for path, color in ((video_a, "red"), (video_b, "blue")):
                subprocess.run(
                    [
                        ffmpeg,
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        f"color=c={color}:s=320x240:d=0.4",
                        "-pix_fmt",
                        "yuv420p",
                        path,
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=0.8",
                    audio,
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            draft_dir = os.path.join(root, "DemoDraft")
            os.makedirs(draft_dir)
            content = {
                "canvas_config": {"width": 320, "height": 240, "ratio": "original"},
                "duration": _us(0.8),
                "materials": {
                    "videos": [
                        {"id": "v1", "path": video_a, "width": 320, "height": 240},
                        {"id": "v2", "path": video_b, "width": 320, "height": 240},
                    ],
                    "audios": [{"id": "a1", "path": audio}],
                },
                "tracks": [
                    {
                        "name": "VideoTrack",
                        "type": "video",
                        "segments": [
                            {
                                "material_id": "v1",
                                "target_timerange": {"start": 0, "duration": _us(0.4)},
                                "source_timerange": {"start": 0, "duration": _us(0.4)},
                                "volume": 1,
                                "speed": 1.0,
                                "visible": True,
                            },
                            {
                                "material_id": "v2",
                                "target_timerange": {
                                    "start": _us(0.4),
                                    "duration": _us(0.4),
                                },
                                "source_timerange": {"start": 0, "duration": _us(0.4)},
                                "volume": 1,
                                "speed": 1.0,
                                "visible": True,
                            },
                        ],
                    },
                    {
                        "name": "VoiceOver",
                        "type": "audio",
                        "segments": [
                            {
                                "material_id": "a1",
                                "target_timerange": {"start": 0, "duration": _us(0.8)},
                                "source_timerange": {"start": 0, "duration": _us(0.8)},
                                "volume": 1,
                                "speed": 1.0,
                                "visible": True,
                            }
                        ],
                    },
                    {
                        "name": "Subtitles",
                        "type": "text",
                        "segments": [
                            {
                                "material_id": "t1",
                                "target_timerange": {"start": 0, "duration": _us(0.8)},
                            }
                        ],
                    },
                ],
            }
            with open(os.path.join(draft_dir, "draft_info.json"), "w", encoding="utf-8") as handle:
                json.dump(content, handle)

            out_path = os.path.join(root, "out.mp4")
            result = export_draft_preview("DemoDraft", out_path, drafts_root=root)
            self.assertTrue(os.path.isfile(out_path))
            self.assertGreater(result["size_bytes"], 1000)
            self.assertEqual(result["mode"], "ffmpeg_preview")
            self.assertEqual(result["video_clips"], 2)
            self.assertEqual(result["audio_clips"], 1)
            self.assertFalse(result["burned_text"])
            self.assertIn("Subtitles", result["text_tracks_skipped"])
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
