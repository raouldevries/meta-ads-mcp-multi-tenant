"""Tests for video processing module.

Unit tests for video processing functions and dataclasses.
"""

import pytest
import tempfile
from pathlib import Path

from meta_ads_mcp.core.video_processing import (
    # Configuration
    VideoConfig,
    DEFAULT_CONFIG,
    # Dataclasses
    ExtractedFrame,
    SubtitleRegion,
    VideoMetadata,
    VideoProcessingResult,
    # Context manager
    VideoProcessingContext,
    # Dependency checks
    check_ffmpeg_available,
    check_tesseract_available,
    # Helper functions
    _parse_ffmpeg_showinfo,
)


# =============================================================================
# Configuration Tests
# =============================================================================

class TestVideoConfig:
    """Tests for VideoConfig dataclass."""

    def test_default_config_values(self):
        """Test default configuration values."""
        config = VideoConfig()
        assert config.max_frames == 10
        assert config.frame_interval_seconds == 2.0
        assert config.scene_change_threshold == 0.3
        assert config.max_duration_seconds == 300
        assert config.subtitle_region_percent == 0.25
        assert config.ocr_confidence_threshold == 0.6
        assert config.download_timeout_seconds == 60
        assert config.ffmpeg_timeout_seconds == 120

    def test_custom_config_values(self):
        """Test custom configuration values."""
        config = VideoConfig(
            max_frames=5,
            frame_interval_seconds=3.0,
            scene_change_threshold=0.5
        )
        assert config.max_frames == 5
        assert config.frame_interval_seconds == 3.0
        assert config.scene_change_threshold == 0.5

    def test_default_config_constant(self):
        """Test DEFAULT_CONFIG is a VideoConfig instance."""
        assert isinstance(DEFAULT_CONFIG, VideoConfig)
        assert DEFAULT_CONFIG.max_frames == 10


# =============================================================================
# Dataclass Tests
# =============================================================================

class TestExtractedFrame:
    """Tests for ExtractedFrame dataclass."""

    def test_create_frame(self):
        """Test creating an ExtractedFrame."""
        frame = ExtractedFrame(
            path="/tmp/frame_001.jpg",
            timestamp=2.5,
            index=0
        )
        assert frame.path == "/tmp/frame_001.jpg"
        assert frame.timestamp == 2.5
        assert frame.index == 0
        assert frame.is_scene_change is False

    def test_frame_with_scene_change(self):
        """Test frame with scene change flag."""
        frame = ExtractedFrame(
            path="/tmp/frame.jpg",
            timestamp=5.0,
            index=1,
            is_scene_change=True
        )
        assert frame.is_scene_change is True


class TestSubtitleRegion:
    """Tests for SubtitleRegion dataclass."""

    def test_create_subtitle(self):
        """Test creating a SubtitleRegion."""
        subtitle = SubtitleRegion(
            text="Hello World",
            confidence=0.95,
            timestamp=3.0,
            frame_index=1
        )
        assert subtitle.text == "Hello World"
        assert subtitle.confidence == 0.95
        assert subtitle.timestamp == 3.0
        assert subtitle.frame_index == 1


class TestVideoMetadata:
    """Tests for VideoMetadata dataclass."""

    def test_create_metadata(self):
        """Test creating VideoMetadata."""
        meta = VideoMetadata(
            duration_seconds=30.5,
            width=1920,
            height=1080,
            fps=30.0,
            codec="h264"
        )
        assert meta.duration_seconds == 30.5
        assert meta.width == 1920
        assert meta.height == 1080
        assert meta.fps == 30.0
        assert meta.codec == "h264"
        assert meta.file_size_bytes is None

    def test_metadata_with_file_size(self):
        """Test metadata with file size."""
        meta = VideoMetadata(
            duration_seconds=60.0,
            width=1080,
            height=1920,
            fps=60.0,
            codec="hevc",
            file_size_bytes=10_000_000
        )
        assert meta.file_size_bytes == 10_000_000


class TestVideoProcessingResult:
    """Tests for VideoProcessingResult dataclass."""

    def test_create_empty_result(self):
        """Test creating an empty result."""
        result = VideoProcessingResult(
            video_id="123456",
            metadata=None
        )
        assert result.video_id == "123456"
        assert result.metadata is None
        assert result.frames == []
        assert result.subtitles == []
        assert result.errors == []
        assert result.processing_level == "metadata_only"

    def test_result_with_frames(self):
        """Test result with frames."""
        frames = [
            ExtractedFrame(path="/tmp/f1.jpg", timestamp=0.0, index=0),
            ExtractedFrame(path="/tmp/f2.jpg", timestamp=2.0, index=1)
        ]
        result = VideoProcessingResult(
            video_id="123",
            metadata=None,
            frames=frames,
            processing_level="frames_extracted"
        )
        assert len(result.frames) == 2
        assert result.processing_level == "frames_extracted"


# =============================================================================
# Dependency Check Tests
# =============================================================================

class TestDependencyChecks:
    """Tests for dependency check functions."""

    def test_check_ffmpeg_returns_tuple(self):
        """Test check_ffmpeg_available returns a tuple."""
        result = check_ffmpeg_available()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_check_tesseract_returns_tuple(self):
        """Test check_tesseract_available returns a tuple."""
        result = check_tesseract_available()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_ffmpeg_available_on_system(self):
        """Test that ffmpeg is available on this system."""
        available, info = check_ffmpeg_available()
        # This test assumes ffmpeg is installed (as per previous verification)
        if not available:
            pytest.skip(f"FFmpeg not available: {info}")
        assert "ffmpeg" in info.lower()

    def test_tesseract_available_on_system(self):
        """Test that tesseract is available on this system."""
        available, info = check_tesseract_available()
        # This test assumes tesseract is installed (as per previous verification)
        if not available:
            pytest.skip(f"Tesseract not available: {info}")
        assert "tesseract" in info.lower()


# =============================================================================
# Context Manager Tests
# =============================================================================

class TestVideoProcessingContext:
    """Tests for VideoProcessingContext context manager."""

    @pytest.mark.asyncio
    async def test_context_creates_temp_dir(self):
        """Test that context creates a temp directory."""
        async with VideoProcessingContext() as ctx:
            assert ctx.temp_dir is not None
            assert ctx.temp_dir.exists()
            assert ctx.temp_dir.is_dir()

    @pytest.mark.asyncio
    async def test_context_cleans_up_on_exit(self):
        """Test that context cleans up temp directory on exit."""
        temp_dir_path = None
        async with VideoProcessingContext() as ctx:
            temp_dir_path = ctx.temp_dir
            assert temp_dir_path.exists()

        # After exit, directory should be cleaned up
        assert not temp_dir_path.exists()

    @pytest.mark.asyncio
    async def test_context_get_video_path(self):
        """Test get_video_path method."""
        async with VideoProcessingContext() as ctx:
            video_path = ctx.get_video_path("test.mp4")
            assert video_path.name == "test.mp4"
            assert video_path.parent == ctx.temp_dir

    @pytest.mark.asyncio
    async def test_context_get_frame_path(self):
        """Test get_frame_path method."""
        async with VideoProcessingContext() as ctx:
            frame_path = ctx.get_frame_path(5)
            assert frame_path.name == "frame_0005.jpg"
            assert frame_path.parent == ctx.temp_dir

    @pytest.mark.asyncio
    async def test_context_get_temp_path(self):
        """Test get_temp_path method."""
        async with VideoProcessingContext() as ctx:
            temp_path = ctx.get_temp_path("custom_file.txt")
            assert temp_path.name == "custom_file.txt"
            assert temp_path.parent == ctx.temp_dir

    @pytest.mark.asyncio
    async def test_context_custom_prefix(self):
        """Test context with custom prefix."""
        async with VideoProcessingContext(prefix="test_video_") as ctx:
            assert "test_video_" in str(ctx.temp_dir)

    @pytest.mark.asyncio
    async def test_context_cleans_up_on_error(self):
        """Test that context cleans up even when an error occurs."""
        temp_dir_path = None
        with pytest.raises(ValueError):
            async with VideoProcessingContext() as ctx:
                temp_dir_path = ctx.temp_dir
                # Create a file to ensure cleanup works
                test_file = ctx.get_temp_path("test.txt")
                test_file.write_text("test content")
                raise ValueError("Intentional error")

        # Directory should be cleaned up despite error
        assert not temp_dir_path.exists()

    def test_context_raises_error_when_not_entered(self):
        """Test that methods raise error when context not entered."""
        ctx = VideoProcessingContext()
        with pytest.raises(RuntimeError, match="Context not entered"):
            ctx.get_video_path()


# =============================================================================
# FFmpeg Output Parsing Tests
# =============================================================================

class TestParseFFmpegShowinfo:
    """Tests for _parse_ffmpeg_showinfo function."""

    def test_parse_single_frame(self):
        """Test parsing single frame info."""
        stderr = """
[Parsed_showinfo_1 @ 0x7f8b8c] n:0 pts:0 pts_time:0.000000 fmt:yuvj420p
"""
        timestamps = _parse_ffmpeg_showinfo(stderr)
        assert 0 in timestamps
        assert timestamps[0] == 0.0

    def test_parse_multiple_frames(self):
        """Test parsing multiple frames."""
        stderr = """
[Parsed_showinfo_1 @ 0x7f8b8c] n:0 pts:0 pts_time:0.000000 fmt:yuvj420p
[Parsed_showinfo_1 @ 0x7f8b8c] n:1 pts:60000 pts_time:2.000000 fmt:yuvj420p
[Parsed_showinfo_1 @ 0x7f8b8c] n:2 pts:120000 pts_time:4.000000 fmt:yuvj420p
"""
        timestamps = _parse_ffmpeg_showinfo(stderr)
        assert len(timestamps) == 3
        assert timestamps[0] == 0.0
        assert timestamps[1] == 2.0
        assert timestamps[2] == 4.0

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        timestamps = _parse_ffmpeg_showinfo("")
        assert timestamps == {}

    def test_parse_non_showinfo_output(self):
        """Test parsing output without showinfo lines."""
        stderr = """
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'video.mp4':
  Duration: 00:00:30.00, start: 0.000000, bitrate: 1000 kb/s
"""
        timestamps = _parse_ffmpeg_showinfo(stderr)
        assert timestamps == {}

    def test_parse_mixed_output(self):
        """Test parsing mixed output with showinfo lines."""
        stderr = """
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'video.mp4':
[Parsed_showinfo_1 @ 0x7f8b8c] n:0 pts:0 pts_time:1.500000 fmt:yuvj420p
Output #0, image2, to 'frame_%04d.jpg':
[Parsed_showinfo_1 @ 0x7f8b8c] n:1 pts:90000 pts_time:3.000000 fmt:yuvj420p
"""
        timestamps = _parse_ffmpeg_showinfo(stderr)
        assert len(timestamps) == 2
        assert timestamps[0] == 1.5
        assert timestamps[1] == 3.0
