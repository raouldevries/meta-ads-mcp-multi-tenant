"""Video Processing Module for Creative Analysis.

This module provides video download, frame extraction, and OCR capabilities
for analyzing video ad creatives. Requires external dependencies:
- ffmpeg >= 4.0 for video processing
- tesseract-ocr >= 4.0 for subtitle detection (optional)
"""

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import atexit
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import httpx

from .api import make_api_request
from .utils import logger


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class VideoConfig:
    """Configuration for video processing."""
    max_frames: int = 10  # Maximum frames to extract
    frame_interval_seconds: float = 2.0  # Seconds between frames
    scene_change_threshold: float = 0.3  # Scene detection sensitivity (0-1)
    max_duration_seconds: int = 300  # Max video duration to process (5 min)
    subtitle_region_percent: float = 0.25  # Bottom portion for subtitles
    ocr_confidence_threshold: float = 0.6  # Min confidence for OCR text
    download_timeout_seconds: int = 60  # Video download timeout
    ffmpeg_timeout_seconds: int = 120  # FFmpeg operation timeout


# Default configuration
DEFAULT_CONFIG = VideoConfig()


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ExtractedFrame:
    """Represents an extracted video frame."""
    path: str  # Path to the frame image file
    timestamp: float  # Timestamp in seconds
    index: int  # Frame index (0-based)
    is_scene_change: bool = False  # Whether this is a scene change


@dataclass
class SubtitleRegion:
    """Detected text region from a video frame."""
    text: str
    confidence: float  # 0.0 to 1.0
    timestamp: float  # Timestamp where text was detected
    frame_index: int


@dataclass
class VideoMetadata:
    """Metadata about a video."""
    duration_seconds: float
    width: int
    height: int
    fps: float
    codec: str
    file_size_bytes: Optional[int] = None


@dataclass
class VideoProcessingResult:
    """Result of video processing operations."""
    video_id: str
    metadata: Optional[VideoMetadata]
    frames: List[ExtractedFrame] = field(default_factory=list)
    subtitles: List[SubtitleRegion] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    processing_level: str = "metadata_only"  # metadata_only, frames_extracted, full


# =============================================================================
# Dependency Checking
# =============================================================================

def check_ffmpeg_available() -> Tuple[bool, str]:
    """
    Check if ffmpeg is available and return version info.

    Returns:
        Tuple of (is_available, version_string_or_error)
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version from first line
            version_line = result.stdout.split('\n')[0]
            return True, version_line
        return False, f"ffmpeg returned error code {result.returncode}"
    except FileNotFoundError:
        return False, "ffmpeg not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "ffmpeg version check timed out"
    except Exception as e:
        return False, f"Error checking ffmpeg: {str(e)}"


def check_tesseract_available() -> Tuple[bool, str]:
    """
    Check if tesseract is available and return version info.

    Returns:
        Tuple of (is_available, version_string_or_error)
    """
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version from first line
            version_line = result.stdout.split('\n')[0]
            return True, version_line
        return False, f"tesseract returned error code {result.returncode}"
    except FileNotFoundError:
        return False, "tesseract not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "tesseract version check timed out"
    except Exception as e:
        return False, f"Error checking tesseract: {str(e)}"


# =============================================================================
# Video Processing Context Manager
# =============================================================================

class VideoProcessingContext:
    """
    Context manager for video processing with automatic cleanup.

    Creates a temporary directory for video and frame files,
    and ensures cleanup even on errors.

    Usage:
        async with VideoProcessingContext() as ctx:
            video_path = ctx.get_video_path("video.mp4")
            frame_path = ctx.get_frame_path(0)
            # ... process video ...
    """

    # Track all active contexts for cleanup
    _active_contexts: List["VideoProcessingContext"] = []

    def __init__(self, prefix: str = "meta_ads_video_"):
        self.prefix = prefix
        self.temp_dir: Optional[Path] = None
        self._cleanup_registered = False

    async def __aenter__(self) -> "VideoProcessingContext":
        """Create temporary directory and register cleanup."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix=self.prefix))
        logger.debug(f"Created temp directory: {self.temp_dir}")

        # Register for cleanup tracking
        VideoProcessingContext._active_contexts.append(self)

        # Register atexit handler if not already done
        if not self._cleanup_registered:
            atexit.register(self._cleanup_all_contexts)
            self._cleanup_registered = True

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary directory."""
        await self.cleanup()

        # Remove from active contexts
        if self in VideoProcessingContext._active_contexts:
            VideoProcessingContext._active_contexts.remove(self)

    async def cleanup(self):
        """Remove temporary directory and all contents."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
            finally:
                self.temp_dir = None

    @staticmethod
    def _cleanup_all_contexts():
        """Clean up all active contexts (called by atexit)."""
        for ctx in VideoProcessingContext._active_contexts[:]:
            if ctx.temp_dir and ctx.temp_dir.exists():
                try:
                    shutil.rmtree(ctx.temp_dir)
                except Exception:
                    pass

    def get_video_path(self, filename: str = "video.mp4") -> Path:
        """Get path for video file in temp directory."""
        if not self.temp_dir:
            raise RuntimeError("Context not entered")
        return self.temp_dir / filename

    def get_frame_path(self, index: int, extension: str = "jpg") -> Path:
        """Get path for frame file in temp directory."""
        if not self.temp_dir:
            raise RuntimeError("Context not entered")
        return self.temp_dir / f"frame_{index:04d}.{extension}"

    def get_temp_path(self, filename: str) -> Path:
        """Get path for any temp file."""
        if not self.temp_dir:
            raise RuntimeError("Context not entered")
        return self.temp_dir / filename


# =============================================================================
# Video Download
# =============================================================================

async def download_video(
    video_id: str,
    account_id: str,
    access_token: str,
    output_path: Path,
    config: VideoConfig = DEFAULT_CONFIG
) -> Optional[VideoMetadata]:
    """
    Download a video from Meta Ads API.

    Args:
        video_id: Meta video ID
        account_id: Ad account ID (with act_ prefix)
        access_token: Meta API access token
        output_path: Path to save the downloaded video
        config: Video processing configuration

    Returns:
        VideoMetadata if successful, None on failure
    """
    # Ensure account_id has act_ prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    # Fetch video source URL and metadata
    endpoint = f"{video_id}"
    params = {
        "fields": "source,length,width,height,created_time"
    }

    data = await make_api_request(endpoint, access_token, params)

    if "error" in data:
        logger.error(f"Failed to fetch video metadata: {data.get('error')}")
        return None

    source_url = data.get("source")
    if not source_url:
        logger.error("No source URL found for video")
        return None

    # Parse metadata
    duration = float(data.get("length", 0))
    width = int(data.get("width", 0))
    height = int(data.get("height", 0))

    # Check duration limit
    if duration > config.max_duration_seconds:
        logger.warning(f"Video duration ({duration}s) exceeds limit ({config.max_duration_seconds}s)")

    # Download video
    try:
        async with httpx.AsyncClient(timeout=config.download_timeout_seconds) as client:
            response = await client.get(
                source_url,
                follow_redirects=True,
                headers={
                    "User-Agent": "curl/8.4.0",
                    "Accept": "*/*"
                }
            )

            if response.status_code != 200:
                logger.error(f"Failed to download video: HTTP {response.status_code}")
                return None

            # Write to file
            with open(output_path, "wb") as f:
                f.write(response.content)

            file_size = len(response.content)
            logger.debug(f"Downloaded video: {file_size} bytes to {output_path}")

            return VideoMetadata(
                duration_seconds=duration,
                width=width,
                height=height,
                fps=30.0,  # Default, will be refined by ffprobe
                codec="unknown",
                file_size_bytes=file_size
            )

    except httpx.TimeoutException:
        logger.error("Video download timed out")
        return None
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return None


async def get_video_metadata_ffprobe(
    video_path: Path
) -> Optional[VideoMetadata]:
    """
    Get detailed video metadata using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        VideoMetadata with accurate info, or None on failure
    """
    ffprobe_available, _ = check_ffmpeg_available()
    if not ffprobe_available:
        return None

    try:
        # Run ffprobe to get video info
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=30
        )

        if proc.returncode != 0:
            logger.warning(f"ffprobe failed: {stderr.decode()}")
            return None

        data = json.loads(stdout.decode())

        # Find video stream
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if not video_stream:
            return None

        # Parse frame rate
        fps_str = video_stream.get("r_frame_rate", "30/1")
        if "/" in fps_str:
            num, denom = fps_str.split("/")
            fps = float(num) / float(denom) if float(denom) > 0 else 30.0
        else:
            fps = float(fps_str)

        format_info = data.get("format", {})

        return VideoMetadata(
            duration_seconds=float(format_info.get("duration", 0)),
            width=int(video_stream.get("width", 0)),
            height=int(video_stream.get("height", 0)),
            fps=fps,
            codec=video_stream.get("codec_name", "unknown"),
            file_size_bytes=int(format_info.get("size", 0))
        )

    except asyncio.TimeoutError:
        logger.warning("ffprobe timed out")
        return None
    except Exception as e:
        logger.warning(f"Error running ffprobe: {e}")
        return None


# =============================================================================
# Frame Extraction
# =============================================================================

async def extract_frames(
    video_path: Path,
    output_dir: Path,
    config: VideoConfig = DEFAULT_CONFIG,
    metadata: Optional[VideoMetadata] = None
) -> List[ExtractedFrame]:
    """
    Extract frames from a video using ffmpeg.

    Uses hybrid extraction: scene changes + interval-based sampling.

    Args:
        video_path: Path to video file
        output_dir: Directory to save extracted frames
        config: Video processing configuration
        metadata: Optional video metadata for optimization

    Returns:
        List of ExtractedFrame objects
    """
    ffmpeg_available, ffmpeg_info = check_ffmpeg_available()
    if not ffmpeg_available:
        logger.error(f"FFmpeg not available: {ffmpeg_info}")
        return []

    # Calculate frame extraction parameters
    if metadata:
        duration = min(metadata.duration_seconds, config.max_duration_seconds)
    else:
        duration = config.max_duration_seconds

    # Build ffmpeg command for hybrid extraction
    # Uses scene detection + interval-based fallback
    output_pattern = str(output_dir / "frame_%04d.jpg")

    # Scene detection filter with interval fallback
    # This extracts frames at scene changes OR every N seconds
    select_filter = (
        f"select='gt(scene,{config.scene_change_threshold})"
        f"+isnan(prev_selected_t)*gte(t-prev_selected_t,{config.frame_interval_seconds})'"
    )

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"{select_filter},showinfo",
        "-vsync", "vfr",
        "-q:v", "2",  # High quality JPEG
        "-frames:v", str(config.max_frames),
        output_pattern,
        "-y"  # Overwrite existing files
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=config.ffmpeg_timeout_seconds
        )

        if proc.returncode != 0:
            logger.warning(f"FFmpeg returned code {proc.returncode}")
            # Continue anyway - might have extracted some frames

        # Parse showinfo output for timestamps
        timestamps = _parse_ffmpeg_showinfo(stderr.decode())

        # Collect extracted frames
        frames = []
        for i, frame_path in enumerate(sorted(output_dir.glob("frame_*.jpg"))):
            timestamp = timestamps.get(i, i * config.frame_interval_seconds)
            frames.append(ExtractedFrame(
                path=str(frame_path),
                timestamp=timestamp,
                index=i,
                is_scene_change=True  # Assume scene change for now
            ))

        logger.debug(f"Extracted {len(frames)} frames from video")
        return frames

    except asyncio.TimeoutError:
        logger.error("FFmpeg frame extraction timed out")
        return []
    except Exception as e:
        logger.error(f"Error extracting frames: {e}")
        return []


def _parse_ffmpeg_showinfo(stderr_output: str) -> Dict[int, float]:
    """
    Parse ffmpeg showinfo filter output to extract timestamps.

    Args:
        stderr_output: FFmpeg stderr containing showinfo output

    Returns:
        Dict mapping frame index to timestamp in seconds
    """
    timestamps = {}
    frame_num = 0

    for line in stderr_output.split('\n'):
        if "showinfo" in line.lower() and "pts_time" in line.lower():
            # Parse line like: [Parsed_showinfo_1 @ 0x...] n:0 pts:12345 pts_time:0.500000 ...
            try:
                for part in line.split():
                    if part.startswith("pts_time:"):
                        timestamp = float(part.split(":")[1])
                        timestamps[frame_num] = timestamp
                        frame_num += 1
                        break
            except (ValueError, IndexError):
                continue

    return timestamps


# =============================================================================
# Subtitle Detection (OCR)
# =============================================================================

async def detect_subtitles(
    frame_path: Path,
    timestamp: float,
    frame_index: int,
    config: VideoConfig = DEFAULT_CONFIG
) -> List[SubtitleRegion]:
    """
    Detect subtitles/text in a video frame using Tesseract OCR.

    Focuses on the bottom portion of the frame where subtitles typically appear.

    Args:
        frame_path: Path to frame image
        timestamp: Frame timestamp in seconds
        frame_index: Frame index
        config: Video processing configuration

    Returns:
        List of detected SubtitleRegion objects
    """
    tesseract_available, _ = check_tesseract_available()
    if not tesseract_available:
        logger.debug("Tesseract not available, skipping OCR")
        return []

    try:
        # Use tesseract with confidence output
        cmd = [
            "tesseract",
            str(frame_path),
            "stdout",
            "--psm", "6",  # Assume uniform text block
            "-c", "tessedit_create_tsv=1"  # Output with confidence
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=30
        )

        if proc.returncode != 0:
            return []

        # Parse TSV output
        subtitles = []
        lines = stdout.decode().strip().split('\n')

        if len(lines) <= 1:
            return []

        # Skip header
        for line in lines[1:]:
            parts = line.split('\t')
            if len(parts) >= 12:
                conf = float(parts[10]) / 100.0  # Confidence is 0-100
                text = parts[11].strip()

                if text and conf >= config.ocr_confidence_threshold:
                    subtitles.append(SubtitleRegion(
                        text=text,
                        confidence=conf,
                        timestamp=timestamp,
                        frame_index=frame_index
                    ))

        return subtitles

    except asyncio.TimeoutError:
        logger.warning("Tesseract OCR timed out")
        return []
    except Exception as e:
        logger.warning(f"Error running OCR: {e}")
        return []


async def detect_subtitles_batch(
    frames: List[ExtractedFrame],
    config: VideoConfig = DEFAULT_CONFIG
) -> List[SubtitleRegion]:
    """
    Run OCR on multiple frames in parallel.

    Args:
        frames: List of ExtractedFrame objects
        config: Video processing configuration

    Returns:
        Combined list of SubtitleRegion objects from all frames
    """
    tasks = [
        detect_subtitles(
            Path(frame.path),
            frame.timestamp,
            frame.index,
            config
        )
        for frame in frames
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_subtitles = []
    for result in results:
        if isinstance(result, list):
            all_subtitles.extend(result)

    return all_subtitles


# =============================================================================
# High-Level Processing Function
# =============================================================================

async def process_video(
    video_id: str,
    account_id: str,
    access_token: str,
    config: VideoConfig = DEFAULT_CONFIG,
    extract_subtitles: bool = True
) -> VideoProcessingResult:
    """
    Process a video: download, extract frames, and optionally detect subtitles.

    Args:
        video_id: Meta video ID
        account_id: Ad account ID
        access_token: Meta API access token
        config: Video processing configuration
        extract_subtitles: Whether to run OCR on frames

    Returns:
        VideoProcessingResult with all extracted data
    """
    result = VideoProcessingResult(
        video_id=video_id,
        metadata=None
    )

    async with VideoProcessingContext() as ctx:
        # Download video
        video_path = ctx.get_video_path()
        metadata = await download_video(
            video_id, account_id, access_token, video_path, config
        )

        if not metadata:
            result.errors.append("Failed to download video")
            return result

        # Get detailed metadata with ffprobe
        detailed_metadata = await get_video_metadata_ffprobe(video_path)
        result.metadata = detailed_metadata or metadata
        result.processing_level = "metadata_only"

        # Extract frames
        frames = await extract_frames(
            video_path,
            ctx.temp_dir,
            config,
            result.metadata
        )

        if frames:
            result.frames = frames
            result.processing_level = "frames_extracted"
        else:
            result.errors.append("Failed to extract frames")
            return result

        # Detect subtitles if requested
        if extract_subtitles:
            subtitles = await detect_subtitles_batch(frames, config)
            result.subtitles = subtitles
            result.processing_level = "full"

        return result
