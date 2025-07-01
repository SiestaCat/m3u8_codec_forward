import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
import httpx

from m3u8_codec_forward.parser import M3U8Parser
from m3u8_codec_forward.models import StreamInfo


class TestM3U8Parser:
    
    @pytest_asyncio.fixture
    async def parser(self):
        parser = M3U8Parser()
        yield parser
        await parser.close()
    
    @pytest.mark.asyncio
    async def test_parse_master_playlist(self, parser):
        # Sample master playlist content
        master_playlist = """#EXTM3U
#EXT-X-VERSION:6
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2"
high/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1280x720,CODECS="avc1.42001e,mp4a.40.2"
medium/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=854x480,CODECS="avc1.42001e,mp4a.40.2"
low/playlist.m3u8
"""
        
        mock_response = AsyncMock()
        mock_response.text = master_playlist
        mock_response.raise_for_status = AsyncMock()
        
        with patch.object(parser.client, 'get', return_value=mock_response):
            stream_info = await parser.parse_playlist("http://example.com/master.m3u8")
            
            assert isinstance(stream_info, StreamInfo)
            assert str(stream_info.url) == "http://example.com/master.m3u8"
            assert len(stream_info.variants) == 3
            
            # Check first variant
            first_variant = stream_info.variants[0]
            assert first_variant["bandwidth"] == 5000000
            assert first_variant["resolution"] == (1920, 1080)
    
    @pytest.mark.asyncio
    async def test_parse_media_playlist(self, parser):
        # Sample media playlist content
        media_playlist = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXTINF:9.009,
segment0.ts
#EXTINF:9.009,
segment1.ts
#EXTINF:9.009,
segment2.ts
#EXT-X-ENDLIST
"""
        
        mock_response = AsyncMock()
        mock_response.text = media_playlist
        mock_response.raise_for_status = AsyncMock()
        
        with patch.object(parser.client, 'get', return_value=mock_response):
            stream_info = await parser.parse_playlist("http://example.com/high/playlist.m3u8")
            
            assert isinstance(stream_info, StreamInfo)
            assert len(stream_info.segments) == 3
            assert stream_info.duration == 30.0  # 10 * 3 segments
            
            # Check segment URLs are properly resolved
            expected_segments = [
                "http://example.com/high/segment0.ts",
                "http://example.com/high/segment1.ts", 
                "http://example.com/high/segment2.ts"
            ]
            assert stream_info.segments == expected_segments
    
    @pytest.mark.asyncio
    async def test_get_master_playlist_info(self, parser):
        master_playlist = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
high.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1280x720
medium.m3u8
"""
        
        mock_response = AsyncMock()
        mock_response.text = master_playlist
        mock_response.raise_for_status = AsyncMock()
        
        with patch.object(parser.client, 'get', return_value=mock_response):
            info = await parser.get_master_playlist_info("http://example.com/master.m3u8")
            
            assert info["url"] == "http://example.com/master.m3u8"
            assert info["total_variants"] == 2
            assert len(info["variants"]) == 2
    
    @pytest.mark.asyncio
    async def test_parse_playlist_http_error(self, parser):
        with patch.object(parser.client, 'get', side_effect=httpx.RequestError("Network error")):
            with pytest.raises(Exception, match="Error fetching M3U8"):
                await parser.parse_playlist("http://example.com/invalid.m3u8")
    
    @pytest.mark.asyncio
    async def test_get_master_playlist_info_not_master(self, parser):
        # Media playlist instead of master
        media_playlist = """#EXTM3U
#EXT-X-VERSION:3
#EXTINF:10.0,
segment.ts
"""
        
        mock_response = AsyncMock()
        mock_response.text = media_playlist
        mock_response.raise_for_status = AsyncMock()
        
        with patch.object(parser.client, 'get', return_value=mock_response):
            with pytest.raises(Exception, match="Not a master playlist"):
                await parser.get_master_playlist_info("http://example.com/media.m3u8")
    
    def test_get_base_uri(self, parser):
        url = "http://example.com/path/to/playlist.m3u8"
        base_uri = parser._get_base_uri(url)
        assert base_uri == "http://example.com/path/to/"
        
        url2 = "https://cdn.example.com/streams/master.m3u8"
        base_uri2 = parser._get_base_uri(url2)
        assert base_uri2 == "https://cdn.example.com/streams/"