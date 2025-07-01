import pytest
import json
import tempfile
from pathlib import Path

from m3u8_codec_forward.config import ConfigManager, AppConfig, PresetConfig
from m3u8_codec_forward.models import StreamVariant, CodecType, AudioCodec, Resolution


class TestAppConfig:
    def test_app_config_defaults(self):
        config = AppConfig()
        assert config.server_host == "0.0.0.0"
        assert config.server_port == 80
        assert config.working_dir is None
        assert config.log_level == "INFO"
        assert config.max_concurrent_streams == 5
    
    def test_app_config_custom_values(self):
        config = AppConfig(
            server_host="192.168.1.100",
            server_port=9000,
            log_level="DEBUG",
            max_concurrent_streams=10
        )
        assert config.server_host == "192.168.1.100"
        assert config.server_port == 9000
        assert config.log_level == "DEBUG"
        assert config.max_concurrent_streams == 10


class TestConfigManager:
    def test_config_manager_initialization(self):
        manager = ConfigManager()
        assert isinstance(manager.app_config, AppConfig)
        assert len(manager.presets) > 0
        assert "standard" in manager.presets
        assert "high_efficiency" in manager.presets
        assert "multi_codec" in manager.presets
    
    def test_default_presets(self):
        manager = ConfigManager()
        
        # Test standard preset
        standard = manager.get_preset("standard")
        assert standard is not None
        assert len(standard.variants) == 3
        assert all(v.codec == CodecType.H264 for v in standard.variants)
        
        # Test high efficiency preset
        high_eff = manager.get_preset("high_efficiency")
        assert high_eff is not None
        assert any(v.codec == CodecType.H265 for v in high_eff.variants)
        assert any(v.codec == CodecType.VP9 for v in high_eff.variants)
        
        # Test multi codec preset
        multi = manager.get_preset("multi_codec")
        assert multi is not None
        codecs = {v.codec for v in multi.variants}
        assert CodecType.H264 in codecs
        assert CodecType.H265 in codecs
        assert CodecType.VP9 in codecs
        assert CodecType.AV1 in codecs
    
    def test_load_json_config(self):
        config_data = {
            "app": {
                "server_host": "127.0.0.1",
                "server_port": 9999,
                "log_level": "DEBUG"
            },
            "presets": [
                {
                    "name": "test_preset",
                    "variants": [
                        {
                            "codec": "h264",
                            "audio_codec": "aac_lc",
                            "resolution": {"width": 1920, "height": 1080},
                            "bitrate": 5000,
                            "framerate": 30.0,
                            "container": "ts"
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            manager = ConfigManager()
            manager.load_config(config_path)
            
            assert manager.app_config.server_host == "127.0.0.1"
            assert manager.app_config.server_port == 9999
            assert manager.app_config.log_level == "DEBUG"
            
            test_preset = manager.get_preset("test_preset")
            assert test_preset is not None
            assert len(test_preset.variants) == 1
            assert test_preset.variants[0].codec == CodecType.H264
            
        finally:
            Path(config_path).unlink()
    
    def test_load_config_file_not_found(self):
        manager = ConfigManager()
        with pytest.raises(FileNotFoundError):
            manager.load_config("/nonexistent/config.json")
    
    def test_load_config_invalid_format(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_path = f.name
        
        try:
            manager = ConfigManager()
            with pytest.raises(ValueError, match="Invalid config file format"):
                manager.load_config(config_path)
        finally:
            Path(config_path).unlink()
    
    def test_save_config(self):
        manager = ConfigManager()
        manager.app_config.server_port = 9999
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            manager.save_config(config_path)
            
            # Load and verify
            with open(config_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["app"]["server_port"] == 9999
            assert "presets" in saved_data
            assert len(saved_data["presets"]) > 0
            
        finally:
            Path(config_path).unlink()
    
    def test_list_presets(self):
        manager = ConfigManager()
        presets = manager.list_presets()
        
        assert isinstance(presets, list)
        assert "standard" in presets
        assert "high_efficiency" in presets
        assert "multi_codec" in presets
    
    def test_get_nonexistent_preset(self):
        manager = ConfigManager()
        preset = manager.get_preset("nonexistent")
        assert preset is None