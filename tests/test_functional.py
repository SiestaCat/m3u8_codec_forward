import pytest
import pytest_asyncio
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import asyncio
import time

from m3u8_codec_forward.server import app
from m3u8_codec_forward.parser import M3U8Parser
from m3u8_codec_forward.transcoder import TranscodingEngine
from m3u8_codec_forward.models import TranscodingConfig, StreamVariant, CodecType, AudioCodec, Resolution, ContainerFormat


# Apple's test stream URL
APPLE_TEST_STREAM = "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8"


class TestFunctionalAppleStream:
    
    @pytest.mark.asyncio
    async def test_parse_apple_test_stream(self):
        """Test parsing the real Apple test stream"""
        parser = M3U8Parser()
        try:
            # Test master playlist parsing
            master_info = await parser.get_master_playlist_info(APPLE_TEST_STREAM)
            
            assert "url" in master_info
            assert "variants" in master_info
            assert "total_variants" in master_info
            assert master_info["total_variants"] > 0
            
            # Verify variant structure
            variants = master_info["variants"]
            assert len(variants) > 0
            
            for variant in variants:
                assert "uri" in variant
                assert "bandwidth" in variant
                assert variant["bandwidth"] > 0
                
            print(f"Found {len(variants)} variants in Apple test stream")
            
        finally:
            await parser.close()
    
    @pytest.mark.asyncio
    async def test_parse_individual_variant_from_apple_stream(self):
        """Test parsing individual variant playlists from Apple stream"""
        parser = M3U8Parser()
        try:
            master_info = await parser.get_master_playlist_info(APPLE_TEST_STREAM)
            
            if master_info["variants"]:
                # Test first variant
                first_variant = master_info["variants"][0]
                variant_url = first_variant["uri"]
                
                # Resolve relative URL if needed
                if not variant_url.startswith("http"):
                    base_url = APPLE_TEST_STREAM.rsplit('/', 1)[0]
                    variant_url = f"{base_url}/{variant_url}"
                
                # Parse the variant playlist
                variant_info = await parser.parse_playlist(variant_url)
                
                assert variant_info.segments is not None
                assert len(variant_info.segments) > 0
                
                print(f"Variant has {len(variant_info.segments)} segments")
                
        finally:
            await parser.close()


class TestFunctionalAPI:
    
    def test_health_endpoint(self):
        """Test basic health endpoint"""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root endpoint with service info"""
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "M3U8 Codec Forward"
            assert "endpoints" in data
    
    def test_list_streams_empty(self):
        """Test listing streams when none are active"""
        with TestClient(app) as client:
            response = client.get("/streams")
            assert response.status_code == 200
            data = response.json()
            assert data["total_streams"] == 0
            assert data["active_streams"] == {}
    
    @patch('m3u8_codec_forward.transcoder.TranscodingEngine.start_transcoding')
    @patch('m3u8_codec_forward.parser.M3U8Parser.get_master_playlist_info')
    def test_start_transcoding_endpoint(self, mock_get_info, mock_start_transcoding):
        """Test starting transcoding via API endpoint"""
        # Mock the master playlist info
        mock_get_info.return_value = {
            "url": APPLE_TEST_STREAM,
            "variants": [
                {"bandwidth": 5000000, "resolution": (1920, 1080), "uri": "high.m3u8"},
                {"bandwidth": 3000000, "resolution": (1280, 720), "uri": "medium.m3u8"}
            ],
            "total_variants": 2
        }
        
        # Mock the transcoding start
        mock_start_transcoding.return_value = {
            "h264_1920x1080_5000k_ts": "http://localhost:8080/h264_1920x1080_5000k_ts.m3u8",
            "h264_1280x720_3000k_ts": "http://localhost:8080/h264_1280x720_3000k_ts.m3u8"
        }
        
        with TestClient(app) as client:
            response = client.post(
                "/start-transcoding",
                params={"input_url": APPLE_TEST_STREAM}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "stream_id" in data
            assert "variants" in data
            assert len(data["variants"]) > 0


class TestFunctionalTranscoding:
    
    @pytest.mark.asyncio
    async def test_transcoding_engine_initialization(self):
        """Test transcoding engine can be initialized"""
        engine = TranscodingEngine()
        try:
            assert engine.working_dir.exists()
            assert engine.parser is not None
        finally:
            await engine.close()
    
    @pytest.mark.asyncio
    async def test_ffmpeg_command_building(self):
        """Test FFmpeg command generation"""
        engine = TranscodingEngine()
        try:
            variant = StreamVariant(
                codec=CodecType.H264,
                audio_codec=AudioCodec.AAC,
                resolution=Resolution(width=1280, height=720),
                bitrate=3000,
                framerate=30.0
            )
            
            source_variant = {"bandwidth": 5000000, "resolution": (1920, 1080)}
            
            cmd = engine._build_ffmpeg_command(
                APPLE_TEST_STREAM,
                "/tmp/output.m3u8",
                variant,
                source_variant
            )
            
            assert "ffmpeg" in cmd
            assert APPLE_TEST_STREAM in cmd
            assert "-c:v" in cmd
            assert "libx264" in cmd
            assert "-c:a" in cmd
            assert "aac" in cmd
            assert "-s" in cmd
            assert "1280x720" in cmd
            assert "-b:v" in cmd
            assert "3000k" in cmd
            
        finally:
            await engine.close()
    
    @pytest.mark.asyncio  
    async def test_codec_parameter_mapping(self):
        """Test codec parameter mapping"""
        engine = TranscodingEngine()
        try:
            # Test video codecs
            assert engine._get_video_codec_params(CodecType.H264) == "libx264"
            assert engine._get_video_codec_params(CodecType.H265) == "libx265"
            assert engine._get_video_codec_params(CodecType.VP9) == "libvpx-vp9"
            assert engine._get_video_codec_params(CodecType.AV1) == "libaom-av1"
            
            # Test audio codecs
            assert engine._get_audio_codec_params(AudioCodec.AAC) == "aac"
            assert engine._get_audio_codec_params(AudioCodec.MP3) == "libmp3lame"
            assert engine._get_audio_codec_params(AudioCodec.OPUS) == "libopus"
            
        finally:
            await engine.close()


class TestFunctionalIntegration:
    
    @pytest.mark.asyncio
    async def test_end_to_end_parsing_flow(self):
        """Test complete parsing flow with Apple test stream"""
        parser = M3U8Parser()
        try:
            # Step 1: Parse master playlist
            master_info = await parser.get_master_playlist_info(APPLE_TEST_STREAM)
            assert master_info["total_variants"] > 0
            
            # Step 2: Select best variant
            variants = master_info["variants"]
            best_variant = max(variants, key=lambda x: x.get("bandwidth", 0))
            assert best_variant["bandwidth"] > 0
            
            # Step 3: Parse variant playlist
            variant_url = best_variant["uri"]
            if not variant_url.startswith("http"):
                base_url = APPLE_TEST_STREAM.rsplit('/', 1)[0]
                variant_url = f"{base_url}/{variant_url}"
            
            variant_info = await parser.parse_playlist(variant_url)
            assert len(variant_info.segments) > 0
            
            # Step 4: Verify segment URLs are accessible
            first_segment = variant_info.segments[0]
            assert first_segment.startswith("http")
            
            # Optional: Test if first segment is actually reachable
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.head(first_segment, timeout=5.0)
                    # If successful, segment is accessible
                    if response.status_code == 200:
                        print(f"Successfully verified segment accessibility: {response.status_code}")
                except httpx.RequestError:
                    # Network issues are acceptable in tests
                    print("Segment check skipped due to network issues")
                    
        finally:
            await parser.close()
    
    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_transcoding_config_creation(self, mock_subprocess):
        """Test transcoding configuration with Apple stream"""
        # Mock FFmpeg process
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        engine = TranscodingEngine()
        try:
            variants = [
                StreamVariant(
                    codec=CodecType.H264,
                    audio_codec=AudioCodec.AAC_LC,
                    resolution=Resolution(width=1280, height=720),
                    bitrate=3000,
                    container=ContainerFormat.TS
                ),
                StreamVariant(
                    codec=CodecType.H265,
                    audio_codec=AudioCodec.AAC_LC,
                    resolution=Resolution(width=1920, height=1080),
                    bitrate=4000,
                    container=ContainerFormat.FMP4
                )
            ]
            
            config = TranscodingConfig(
                input_url=APPLE_TEST_STREAM,
                output_variants=variants
            )
            
            # Mock the parser to avoid actual network calls
            with patch.object(engine.parser, 'get_master_playlist_info') as mock_parser:
                mock_parser.return_value = {
                    "variants": [{"bandwidth": 5000000, "resolution": (1920, 1080)}]
                }
                
                variant_urls = await engine.start_transcoding(config)
                
                assert len(variant_urls) == 2
                assert "h264_1280x720_3000k_ts" in variant_urls
                assert "h265_1920x1080_4000k_fmp4" in variant_urls
                
                for url in variant_urls.values():
                    assert url.startswith("http://localhost:8080/")
                    assert url.endswith(".m3u8")
                    
        finally:
            await engine.close()