import m3u8
import httpx
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse
import asyncio

from .models import StreamInfo


class M3U8Parser:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def parse_playlist(self, url: str) -> StreamInfo:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            content = response.text
            
            playlist = m3u8.loads(content, uri=url)
            
            stream_info = StreamInfo(url=url)
            
            if playlist.is_variant:
                stream_info.variants = self._extract_variants(playlist)
            else:
                stream_info.segments = self._extract_segments(playlist, url)
                stream_info.duration = self._calculate_duration(playlist)
            
            return stream_info
            
        except httpx.RequestError as e:
            raise Exception(f"Error fetching M3U8: {e}")
        except Exception as e:
            raise Exception(f"Error parsing M3U8: {e}")
    
    def _extract_variants(self, playlist) -> List[Dict[str, Any]]:
        variants = []
        for variant in playlist.playlists:
            variant_info = {
                "uri": variant.uri,
                "bandwidth": variant.stream_info.bandwidth,
                "resolution": getattr(variant.stream_info, 'resolution', None),
                "codecs": getattr(variant.stream_info, 'codecs', None),
                "frame_rate": getattr(variant.stream_info, 'frame_rate', None),
            }
            variants.append(variant_info)
        return variants
    
    def _extract_segments(self, playlist, base_url: str) -> List[str]:
        segments = []
        base_uri = self._get_base_uri(base_url)
        
        for segment in playlist.segments:
            segment_url = urljoin(base_uri, segment.uri)
            segments.append(segment_url)
        return segments
    
    def _calculate_duration(self, playlist) -> Optional[float]:
        if hasattr(playlist, 'target_duration') and playlist.target_duration is not None:
            return float(playlist.target_duration) * len(playlist.segments)
        return None
    
    def _get_base_uri(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{'/'.join(parsed.path.split('/')[:-1])}/"
    
    async def get_master_playlist_info(self, url: str) -> Dict[str, Any]:
        stream_info = await self.parse_playlist(url)
        
        if not stream_info.variants:
            raise Exception("Not a master playlist - no variants found")
        
        return {
            "url": str(stream_info.url),
            "variants": stream_info.variants,
            "total_variants": len(stream_info.variants)
        }
    
    async def close(self):
        await self.client.aclose()