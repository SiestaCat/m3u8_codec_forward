import json
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, ValidationError

from .models import StreamVariant, CodecType, AudioCodec, Resolution, ContainerFormat


class AppConfig(BaseModel):
    server_host: str = "0.0.0.0"
    server_port: int = 80
    working_dir: Optional[str] = None
    log_level: str = "INFO"
    max_concurrent_streams: int = 5
    segment_duration: int = 6
    playlist_size: int = 10


class PresetConfig(BaseModel):
    name: str
    variants: List[StreamVariant]


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self.app_config = AppConfig()
        self.presets: Dict[str, PresetConfig] = {}
        self._load_default_presets()
    
    def load_config(self, config_path: str):
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            if config_file.suffix.lower() == '.json':
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
            elif config_file.suffix.lower() in ['.yaml', '.yml']:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
            else:
                raise ValueError("Config file must be JSON or YAML")
            
            # Load app config
            if 'app' in config_data:
                self.app_config = AppConfig(**config_data['app'])
            
            # Load presets
            if 'presets' in config_data:
                for preset_data in config_data['presets']:
                    preset = PresetConfig(**preset_data)
                    self.presets[preset.name] = preset
                    
        except (json.JSONDecodeError, yaml.YAMLError, ValidationError) as e:
            raise ValueError(f"Invalid config file format: {e}")
    
    def _load_default_presets(self):
        # Default quality presets
        self.presets["standard"] = PresetConfig(
            name="standard",
            variants=[
                StreamVariant(
                    codec=CodecType.H264,
                    audio_codec=AudioCodec.AAC_LC,
                    resolution=Resolution(width=1920, height=1080),
                    bitrate=5000,
                    framerate=30.0,
                    container=ContainerFormat.TS
                ),
                StreamVariant(
                    codec=CodecType.H264,
                    audio_codec=AudioCodec.AAC_LC,
                    resolution=Resolution(width=1280, height=720),
                    bitrate=3000,
                    framerate=30.0,
                    container=ContainerFormat.TS
                ),
                StreamVariant(
                    codec=CodecType.H264,
                    audio_codec=AudioCodec.AAC_LC,
                    resolution=Resolution(width=854, height=480),
                    bitrate=1500,
                    framerate=30.0,
                    container=ContainerFormat.TS
                )
            ]
        )
        
        self.presets["high_efficiency"] = PresetConfig(
            name="high_efficiency",
            variants=[
                StreamVariant(
                    codec=CodecType.H265,
                    audio_codec=AudioCodec.AAC_LC,
                    resolution=Resolution(width=1920, height=1080),
                    bitrate=3000,
                    framerate=30.0,
                    container=ContainerFormat.FMP4
                ),
                StreamVariant(
                    codec=CodecType.H265,
                    audio_codec=AudioCodec.AAC_LC,
                    resolution=Resolution(width=1280, height=720),
                    bitrate=2000,
                    framerate=30.0,
                    container=ContainerFormat.FMP4
                ),
                StreamVariant(
                    codec=CodecType.VP9,
                    audio_codec=AudioCodec.OPUS,
                    resolution=Resolution(width=1280, height=720),
                    bitrate=2500,
                    framerate=30.0,
                    container=ContainerFormat.WEBM
                )
            ]
        )
        
        self.presets["multi_codec"] = PresetConfig(
            name="multi_codec",
            variants=[
                StreamVariant(
                    codec=CodecType.H264,
                    audio_codec=AudioCodec.AAC_LC,
                    resolution=Resolution(width=1920, height=1080),
                    bitrate=5000,
                    framerate=30.0,
                    container=ContainerFormat.TS
                ),
                StreamVariant(
                    codec=CodecType.H265,
                    audio_codec=AudioCodec.AAC_LC,
                    resolution=Resolution(width=1920, height=1080),
                    bitrate=3000,
                    framerate=30.0,
                    container=ContainerFormat.FMP4
                ),
                StreamVariant(
                    codec=CodecType.VP9,
                    audio_codec=AudioCodec.OPUS,
                    resolution=Resolution(width=1280, height=720),
                    bitrate=2500,
                    framerate=30.0,
                    container=ContainerFormat.WEBM
                ),
                StreamVariant(
                    codec=CodecType.AV1,
                    audio_codec=AudioCodec.OPUS,
                    resolution=Resolution(width=1280, height=720),
                    bitrate=2000,
                    framerate=30.0,
                    container=ContainerFormat.FMP4
                )
            ]
        )
        
        self.presets["legacy_support"] = PresetConfig(
            name="legacy_support",
            variants=[
                StreamVariant(
                    codec=CodecType.MPEG4,
                    audio_codec=AudioCodec.MP3,
                    resolution=Resolution(width=720, height=576),
                    bitrate=1200,
                    framerate=25.0,
                    container=ContainerFormat.AVI
                ),
                StreamVariant(
                    codec=CodecType.H263,
                    audio_codec=AudioCodec.MP3,
                    resolution=Resolution(width=352, height=288),
                    bitrate=400,
                    framerate=15.0,
                    container=ContainerFormat.FLV
                ),
                StreamVariant(
                    codec=CodecType.VP8,
                    audio_codec=AudioCodec.VORBIS,
                    resolution=Resolution(width=854, height=480),
                    bitrate=1000,
                    framerate=30.0,
                    container=ContainerFormat.WEBM
                )
            ]
        )
        
        self.presets["modern_web"] = PresetConfig(
            name="modern_web",
            variants=[
                StreamVariant(
                    codec=CodecType.VP9,
                    audio_codec=AudioCodec.OPUS,
                    resolution=Resolution(width=1920, height=1080),
                    bitrate=3500,
                    framerate=30.0,
                    container=ContainerFormat.WEBM
                ),
                StreamVariant(
                    codec=CodecType.VP8,
                    audio_codec=AudioCodec.VORBIS,
                    resolution=Resolution(width=1280, height=720),
                    bitrate=2000,
                    framerate=30.0,
                    container=ContainerFormat.WEBM
                ),
                StreamVariant(
                    codec=CodecType.AV1,
                    audio_codec=AudioCodec.OPUS,
                    resolution=Resolution(width=1920, height=1080),
                    bitrate=2500,
                    framerate=30.0,
                    container=ContainerFormat.FMP4
                )
            ]
        )
        
        self.presets["audio_focus"] = PresetConfig(
            name="audio_focus",
            variants=[
                StreamVariant(
                    codec=CodecType.H264,
                    audio_codec=AudioCodec.AC3,
                    resolution=Resolution(width=1280, height=720),
                    bitrate=2000,
                    framerate=30.0,
                    container=ContainerFormat.TS
                ),
                StreamVariant(
                    codec=CodecType.H264,
                    audio_codec=AudioCodec.EAC3,
                    resolution=Resolution(width=1920, height=1080),
                    bitrate=4000,
                    framerate=30.0,
                    container=ContainerFormat.TS
                ),
                StreamVariant(
                    codec=CodecType.H265,
                    audio_codec=AudioCodec.HE_AAC,
                    resolution=Resolution(width=1280, height=720),
                    bitrate=2500,
                    framerate=30.0,
                    container=ContainerFormat.FMP4
                )
            ]
        )
    
    def get_preset(self, preset_name: str) -> Optional[PresetConfig]:
        return self.presets.get(preset_name)
    
    def list_presets(self) -> List[str]:
        return list(self.presets.keys())
    
    def save_config(self, output_path: str):
        config_data = {
            "app": self.app_config.model_dump(),
            "presets": [preset.model_dump() for preset in self.presets.values()]
        }
        
        output_file = Path(output_path)
        
        if output_file.suffix.lower() == '.json':
            with open(output_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        elif output_file.suffix.lower() in ['.yaml', '.yml']:
            with open(output_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
        else:
            raise ValueError("Output file must have .json, .yaml, or .yml extension")