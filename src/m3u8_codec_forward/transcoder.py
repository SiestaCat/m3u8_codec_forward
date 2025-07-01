import ffmpeg
import asyncio
import os
import tempfile
import shutil
from typing import List, Dict, Optional
from pathlib import Path
import logging

from .models import StreamVariant, TranscodingConfig, CodecType, AudioCodec, ContainerFormat
from .parser import M3U8Parser

logger = logging.getLogger(__name__)


class TranscodingEngine:
    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = Path(working_dir) if working_dir else Path(tempfile.mkdtemp())
        self.working_dir.mkdir(exist_ok=True)
        self.parser = M3U8Parser()
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}
    
    async def start_transcoding(self, config: TranscodingConfig) -> Dict[str, str]:
        master_info = await self.parser.get_master_playlist_info(str(config.input_url))
        
        if not master_info["variants"]:
            raise Exception("No variants found in master playlist")
        
        source_variant = self._select_best_source_variant(master_info["variants"])
        
        variant_urls = {}
        
        for variant in config.output_variants:
            output_path = self.working_dir / f"{variant.variant_name}.m3u8"
            
            ffmpeg_cmd = self._build_ffmpeg_command(
                str(config.input_url), 
                str(output_path), 
                variant, 
                source_variant
            )
            
            process = await self._start_ffmpeg_process(ffmpeg_cmd, variant.variant_name)
            self.active_processes[variant.variant_name] = process
            
            variant_urls[variant.variant_name] = f"http://{config.output_host}:{config.output_port}/{variant.variant_name}.m3u8"
        
        return variant_urls
    
    def _select_best_source_variant(self, variants: List[Dict]) -> Dict:
        best_variant = max(variants, key=lambda x: x.get("bandwidth", 0))
        return best_variant
    
    def _build_ffmpeg_command(self, input_url: str, output_path: str, 
                            variant: StreamVariant, source_variant: Dict) -> List[str]:
        cmd = [
            "ffmpeg",
            "-re",
            "-i", input_url,
            "-c:v", self._get_video_codec_params(variant.codec),
            "-c:a", self._get_audio_codec_params(variant.audio_codec),
            "-s", str(variant.resolution),
            "-b:v", f"{variant.bitrate}k",
            "-maxrate", f"{int(variant.bitrate * 1.2)}k",
            "-bufsize", f"{int(variant.bitrate * 2)}k",
        ]
        
        # Add codec-specific parameters
        cmd.extend(self._get_codec_specific_params(variant.codec))
        
        # Add container format and output parameters
        container_params = self._get_container_format_params(variant.container, variant.variant_name)
        cmd.extend(container_params)
        
        if variant.framerate:
            cmd.extend(["-r", str(variant.framerate)])
        
        cmd.append(str(output_path))
        return cmd
    
    def _get_codec_specific_params(self, codec: CodecType) -> List[str]:
        """Get codec-specific parameters for better quality/performance"""
        if codec in [CodecType.H264, CodecType.H265]:
            return ["-preset", "fast", "-g", "30", "-sc_threshold", "0"]
        elif codec == CodecType.VP9:
            return ["-deadline", "realtime", "-cpu-used", "4"]
        elif codec == CodecType.VP8:
            return ["-deadline", "realtime", "-cpu-used", "4"]
        elif codec == CodecType.AV1:
            return ["-preset", "8", "-g", "30"]
        else:
            return ["-g", "30"]
    
    def _get_container_format_params(self, container: ContainerFormat, variant_name: str) -> List[str]:
        """Get container format specific parameters"""
        if container == ContainerFormat.TS:
            return [
                "-f", "hls",
                "-hls_time", "6",
                "-hls_list_size", "10", 
                "-hls_flags", "delete_segments+append_list",
                "-hls_segment_filename", str(self.working_dir / f"{variant_name}_%03d.ts")
            ]
        elif container == ContainerFormat.FMP4:
            return [
                "-f", "hls",
                "-hls_time", "6",
                "-hls_list_size", "10",
                "-hls_flags", "delete_segments+append_list",
                "-hls_segment_type", "fmp4",
                "-hls_segment_filename", str(self.working_dir / f"{variant_name}_%03d.m4s")
            ]
        elif container == ContainerFormat.MP4:
            return ["-f", "mp4", "-movflags", "faststart"]
        elif container == ContainerFormat.WEBM:
            return ["-f", "webm"]
        elif container == ContainerFormat.MKV:
            return ["-f", "matroska"]
        elif container == ContainerFormat.FLV:
            return ["-f", "flv"]
        elif container == ContainerFormat.AVI:
            return ["-f", "avi"]
        else:
            # Default to HLS with TS segments
            return [
                "-f", "hls",
                "-hls_time", "6", 
                "-hls_list_size", "10",
                "-hls_flags", "delete_segments+append_list",
                "-hls_segment_filename", str(self.working_dir / f"{variant_name}_%03d.ts")
            ]
    
    def _get_video_codec_params(self, codec: CodecType) -> str:
        codec_map = {
            # Modern video codecs
            CodecType.H264: "libx264",
            CodecType.H265: "libx265", 
            CodecType.AV1: "libaom-av1",
            CodecType.VP9: "libvpx-vp9",
            CodecType.VP8: "libvpx",
            
            # Legacy video codecs
            CodecType.MPEG4: "mpeg4",
            CodecType.MPEG2: "mpeg2video",
            CodecType.MPEG1: "mpeg1video",
            CodecType.H263: "h263",
            CodecType.SORENSON_SPARK: "flv1",
            CodecType.VP6: "vp6",
            CodecType.VC1: "vc1",
            CodecType.THEORA: "libtheora",
            CodecType.REALVIDEO: "rv40",
            CodecType.CINEPAK: "cinepak",
            CodecType.INDEO: "indeo3",
            CodecType.MSVIDEO1: "msvideo1"
        }
        return codec_map.get(codec, "libx264")
    
    def _get_audio_codec_params(self, codec: AudioCodec) -> str:
        codec_map = {
            # Modern audio codecs
            AudioCodec.AAC_LC: "aac",
            AudioCodec.AAC: "aac",  # Alias
            AudioCodec.HE_AAC: "libfdk_aac",
            AudioCodec.XHE_AAC: "libfdk_aac",
            AudioCodec.AC3: "ac3",
            AudioCodec.EAC3: "eac3",
            AudioCodec.MP3: "libmp3lame",
            AudioCodec.OPUS: "libopus",
            AudioCodec.VORBIS: "libvorbis",
            
            # Legacy audio codecs
            AudioCodec.MP2: "mp2",
            AudioCodec.MP1: "mp1",
            AudioCodec.WMA1: "wmav1",
            AudioCodec.WMA2: "wmav2",
            AudioCodec.REALAUDIO: "ra_144"
        }
        return codec_map.get(codec, "aac")
    
    async def _start_ffmpeg_process(self, cmd: List[str], variant_name: str) -> asyncio.subprocess.Process:
        logger.info(f"Starting transcoding for {variant_name}: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            asyncio.create_task(self._monitor_process(process, variant_name))
            return process
            
        except Exception as e:
            logger.error(f"Failed to start FFmpeg process for {variant_name}: {e}")
            raise
    
    async def _monitor_process(self, process: asyncio.subprocess.Process, variant_name: str):
        try:
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"FFmpeg process for {variant_name} failed with code {process.returncode}")
                logger.error(f"stderr: {stderr.decode()}")
            else:
                logger.info(f"FFmpeg process for {variant_name} completed successfully")
                
        except Exception as e:
            logger.error(f"Error monitoring process for {variant_name}: {e}")
    
    async def stop_transcoding(self, variant_name: Optional[str] = None):
        if variant_name:
            if variant_name in self.active_processes:
                process = self.active_processes[variant_name]
                process.terminate()
                await process.wait()
                del self.active_processes[variant_name]
        else:
            for name, process in list(self.active_processes.items()):
                process.terminate()
                await process.wait()
            self.active_processes.clear()
    
    def cleanup(self):
        if self.working_dir.exists():
            shutil.rmtree(self.working_dir)
    
    async def close(self):
        await self.stop_transcoding()
        await self.parser.close()
        self.cleanup()