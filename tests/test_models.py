import pytest
from pydantic import ValidationError

from m3u8_codec_forward.models import (
    StreamVariant, Resolution, CodecType, AudioCodec, ContainerFormat,
    StreamInfo, TranscodingConfig
)


class TestResolution:
    def test_resolution_creation(self):
        resolution = Resolution(width=1920, height=1080)
        assert resolution.width == 1920
        assert resolution.height == 1080
        assert str(resolution) == "1920x1080"
    
    def test_resolution_validation(self):
        with pytest.raises(ValidationError):
            Resolution(width=-1, height=1080)


class TestStreamVariant:
    def test_stream_variant_creation(self):
        resolution = Resolution(width=1920, height=1080)
        variant = StreamVariant(
            codec=CodecType.H264,
            audio_codec=AudioCodec.AAC_LC,
            resolution=resolution,
            bitrate=5000,
            framerate=30.0,
            container=ContainerFormat.TS
        )
        
        assert variant.codec == CodecType.H264
        assert variant.audio_codec == AudioCodec.AAC_LC
        assert variant.resolution == resolution
        assert variant.bitrate == 5000
        assert variant.framerate == 30.0
    
    def test_variant_name_generation(self):
        resolution = Resolution(width=1280, height=720)
        variant = StreamVariant(
            codec=CodecType.H265,
            audio_codec=AudioCodec.OPUS,
            resolution=resolution,
            bitrate=3000,
            container=ContainerFormat.FMP4
        )
        
        assert variant.variant_name == "h265_1280x720_3000k_fmp4"
    
    def test_optional_framerate(self):
        resolution = Resolution(width=854, height=480)
        variant = StreamVariant(
            codec=CodecType.VP9,
            audio_codec=AudioCodec.MP3,
            resolution=resolution,
            bitrate=1500,
            container=ContainerFormat.WEBM
        )
        
        assert variant.framerate is None


class TestStreamInfo:
    def test_stream_info_creation(self):
        stream_info = StreamInfo(url="http://example.com/playlist.m3u8")
        
        assert str(stream_info.url) == "http://example.com/playlist.m3u8"
        assert stream_info.duration is None
        assert stream_info.segments == []
        assert stream_info.variants == []
    
    def test_stream_info_with_data(self):
        segments = ["segment1.ts", "segment2.ts"]
        variants = [{"bandwidth": 5000, "resolution": "1920x1080"}]
        
        stream_info = StreamInfo(
            url="http://example.com/playlist.m3u8",
            duration=120.0,
            segments=segments,
            variants=variants
        )
        
        assert stream_info.duration == 120.0
        assert stream_info.segments == segments
        assert stream_info.variants == variants


class TestTranscodingConfig:
    def test_transcoding_config_creation(self):
        resolution = Resolution(width=1920, height=1080)
        variant = StreamVariant(
            codec=CodecType.H264,
            audio_codec=AudioCodec.AAC_LC,
            resolution=resolution,
            bitrate=5000,
            container=ContainerFormat.TS
        )
        
        config = TranscodingConfig(
            input_url="http://example.com/input.m3u8",
            output_variants=[variant]
        )
        
        assert str(config.input_url) == "http://example.com/input.m3u8"
        assert len(config.output_variants) == 1
        assert config.output_port == 8080
        assert config.output_host == "localhost"
    
    def test_transcoding_config_custom_settings(self):
        resolution = Resolution(width=1280, height=720)
        variant = StreamVariant(
            codec=CodecType.H265,
            audio_codec=AudioCodec.OPUS,
            resolution=resolution,
            bitrate=3000,
            container=ContainerFormat.FMP4
        )
        
        config = TranscodingConfig(
            input_url="http://example.com/input.m3u8",
            output_variants=[variant],
            output_port=9000,
            output_host="192.168.1.100"
        )
        
        assert config.output_port == 9000
        assert config.output_host == "192.168.1.100"