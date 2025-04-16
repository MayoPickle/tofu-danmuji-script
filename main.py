from src.core.room_manager import RoomManager
from src.core.fleet_manager import FleetManager
from src.services.http_request_handler import HttpRequestHandler
from src.services.config_manager import ConfigManager
from src.core.app import BiliLiveApp
from src.config.settings import CONFIG

def main():
    # Initialize all components with dependency injection
    room_manager = RoomManager()
    fleet_manager = FleetManager(CONFIG)
    http_handler = HttpRequestHandler(CONFIG)
    config_manager = ConfigManager(CONFIG)
    
    # Create and run the application
    app = BiliLiveApp(room_manager, fleet_manager, http_handler, config_manager)
    app.run()

if __name__ == "__main__":
    main()
