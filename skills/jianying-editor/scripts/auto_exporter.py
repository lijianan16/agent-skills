import argparse
import os
import sys

from utils.cli_protocol import emit_result, make_result
from utils.env_setup import setup_env
from utils.errors import InfraError, UserInputError
from utils.ffmpeg_bin import ensure_ffmpeg_on_path
from utils.logging_utils import setup_logger

setup_env()
ensure_ffmpeg_on_path()

from ffmpeg_preview_export import default_output_path, export_draft_preview  # noqa: E402
import pyJianYingDraft as draft  # noqa: E402

logger = setup_logger("auto_exporter")


def _preview_export(
    draft_name: str,
    output_path: str,
    resolution: str = None,
    framerate: str = None,
    drafts_root: str = None,
) -> tuple[int, dict]:
    try:
        data = export_draft_preview(
            draft_name,
            output_path,
            drafts_root=drafts_root,
            resolution=resolution,
            framerate=framerate,
        )
    except FileNotFoundError as exc:
        return 2, make_result(
            False,
            "ffmpeg_missing",
            str(exc),
            {"draft": draft_name, "output": output_path, "platform": sys.platform},
        )
    except UserInputError as exc:
        raise exc
    except InfraError as exc:
        logger.error("Preview export failed: %s", exc)
        return 1, make_result(
            False,
            "export_failed",
            str(exc),
            {"draft": draft_name, "output": output_path, "mode": "ffmpeg_preview"},
        )
    logger.info("Preview export succeeded: %s", data["output"])
    if data.get("text_tracks_skipped"):
        logger.warning(
            "JianYing text tracks were not burned in: %s",
            ", ".join(data["text_tracks_skipped"]),
        )
    return 0, make_result(True, "ok", "", data)


def _jianying_export(
    draft_name: str, output_path: str, resolution: str = None, framerate: str = None
) -> tuple[int, dict]:
    if sys.platform != "win32":
        return 2, make_result(
            False,
            "unsupported_platform",
            "JianYing UI export is Windows-only. Use default/preview mode to mix an MP4 with ffmpeg.",
            {
                "draft": draft_name,
                "output": output_path,
                "platform": sys.platform,
                "manual_export_required": True,
            },
        )

    missing = [
        name
        for name in ("JianyingController", "ExportResolution", "ExportFramerate")
        if not hasattr(draft, name)
    ]
    if missing:
        return 2, make_result(
            False,
            "automation_unavailable",
            f"pyJianYingDraft automation API unavailable: {', '.join(missing)}",
            {"draft": draft_name, "output": output_path, "manual_export_required": True},
        )

    res_map = {
        "480": draft.ExportResolution.RES_480P,
        "720": draft.ExportResolution.RES_720P,
        "1080": draft.ExportResolution.RES_1080P,
        "2K": draft.ExportResolution.RES_2K,
        "4K": draft.ExportResolution.RES_4K,
        "8K": draft.ExportResolution.RES_8K,
    }
    fr_map = {
        "24": draft.ExportFramerate.FR_24,
        "25": draft.ExportFramerate.FR_25,
        "30": draft.ExportFramerate.FR_30,
        "50": draft.ExportFramerate.FR_50,
        "60": draft.ExportFramerate.FR_60,
    }

    target_res = res_map.get(str(resolution).upper() if resolution else "")
    target_fr = fr_map.get(str(framerate) if framerate else "")

    if resolution and target_res is None:
        raise UserInputError(
            f"Unsupported resolution: {resolution} (allowed: {', '.join(res_map.keys())})"
        )
    if framerate and target_fr is None:
        raise UserInputError(
            f"Unsupported framerate: {framerate} (allowed: {', '.join(fr_map.keys())})"
        )

    try:
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        logger.info("Preparing JianYing export: draft=%s", draft_name)
        ctrl = draft.JianyingController()
        ctrl.export_draft(draft_name, output_path, resolution=target_res, framerate=target_fr)
        logger.info("Export succeeded: %s", output_path)
        return 0, make_result(
            True,
            "ok",
            "",
            {
                "draft": draft_name,
                "output": output_path,
                "resolution": resolution,
                "fps": framerate,
                "mode": "jianying",
            },
        )
    except Exception as e:
        logger.error("Export failed: %s", e)
        logger.error("Hint: restart JianYing and keep it on Home/Edit page before retry.")
        return 1, make_result(
            False,
            "export_failed",
            str(e),
            {"draft": draft_name, "output": output_path, "mode": "jianying"},
        )


def auto_export(
    draft_name: str,
    output_path: str = None,
    resolution: str = None,
    framerate: str = None,
    mode: str = "auto",
    drafts_root: str = None,
) -> tuple[int, dict]:
    mode = (mode or "auto").strip().lower()
    if mode not in {"auto", "preview", "jianying"}:
        raise UserInputError("Unsupported mode: use auto, preview, or jianying")
    output_path = os.path.abspath(os.path.expanduser(output_path or default_output_path(draft_name)))

    use_preview = mode == "preview" or (mode == "auto" and sys.platform != "win32")
    if use_preview:
        return _preview_export(
            draft_name, output_path, resolution, framerate, drafts_root=drafts_root
        )
    return _jianying_export(draft_name, output_path, resolution, framerate)


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless draft exporter")
    parser.add_argument("name", help="Draft name")
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output mp4 path. Default: ~/Movies on macOS, ~/Videos on Windows/Linux",
    )
    parser.add_argument("--res", help="Resolution: 480/720/1080/2K/4K/8K")
    parser.add_argument("--fps", help="Framerate: 24/25/30/50/60")
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "preview", "jianying"],
        help="auto: ffmpeg preview on macOS/Linux, JianYing UI on Windows; "
        "preview: always ffmpeg; jianying: Windows UI only",
    )
    parser.add_argument("--root", help="Override JianYing drafts root")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    args = parser.parse_args()
    try:
        code, summary = auto_export(
            args.name,
            args.output,
            args.res,
            args.fps,
            mode=args.mode,
            drafts_root=args.root,
        )
    except UserInputError as e:
        logger.error(str(e))
        summary = make_result(
            False,
            "invalid_input",
            str(e),
            {"draft": args.name, "output": args.output or default_output_path(args.name)},
        )
        code = 2
    emit_result(summary, args.json)
    if not args.json:
        if summary.get("ok"):
            data = summary.get("data") or {}
            print(f"Exported {args.name} -> {data.get('output', args.output)}")
            skipped = data.get("text_tracks_skipped") or []
            if skipped:
                print("Preview mix skipped JianYing text tracks: " + ", ".join(skipped))
        else:
            print(f"Error [{summary.get('code')}]: {summary.get('reason')}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
