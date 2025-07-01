import uvicorn
import logging
import argparse
from pathlib import Path

from .config import ConfigManager
from .server import app

def setup_logging(log_level: str):
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description="M3U8 Codec Forward Server")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=80, help="Server port")
    parser.add_argument("--log-level", type=str, default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Load configuration
    config_manager = ConfigManager()
    if args.config:
        config_manager.load_config(args.config)
    
    # Override with command line arguments
    host = args.host or config_manager.app_config.server_host
    port = args.port or config_manager.app_config.server_port
    log_level = args.log_level or config_manager.app_config.log_level
    
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting M3U8 Codec Forward server on {host}:{port}")
    
    # Store config in app state
    app.state.config_manager = config_manager
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level.lower()
    )

if __name__ == "__main__":
    main()