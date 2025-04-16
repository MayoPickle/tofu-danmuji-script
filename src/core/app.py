import argparse

class BiliLiveApp:
    def __init__(self, room_manager, fleet_manager, http_handler, config_manager):
        self.room_manager = room_manager
        self.fleet_manager = fleet_manager
        self.http_handler = http_handler
        self.config_manager = config_manager
    
    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Control connection operations.")
        parser.add_argument('-d', '--disconnect', action='store_true', help='Only send disconnect requests')
        parser.add_argument('-q', '--quiet', action='store_true', help='Send /quit GET request to all ports')
        parser.add_argument('-l', '--login', action='store_true', help='Send login requests with cookies data to ports')
        parser.add_argument('-c', '--config', type=str, nargs='?', const=None, default=-1, 
                           help='Configuration file path. Options: filepath.json or empty (interactive)')
        parser.add_argument('-t', '--time', type=int, help='Sleep time before loading default configuration (seconds)')
        parser.add_argument('-m', '--message', type=str, help='Store a custom message')
        parser.add_argument('-r', '--room', type=int, help='Directly connect to a specific room ID')
        parser.add_argument('-f', '--fleet', type=str, default='0', help='Specify fleet numbers to use (e.g., "1,2,3"). Default: all fleets')
        return parser.parse_args()
    
    def get_fleet_nums(self, args):
        """根据命令行参数获取 fleet numbers，不再提示用户输入"""
        fleet_nums_input = args.fleet
        total_fleets = (self.config_manager.config['end_port'] - self.config_manager.config['start_port'] + 1) // self.config_manager.config['fleet_size']
        
        # 如果指定了 '0' 或空字符串，使用所有 fleets
        if not fleet_nums_input or fleet_nums_input == '0':
            return list(range(1, total_fleets + 1))
        
        # 否则解析指定的 fleets
        try:
            return [int(num.strip()) for num in fleet_nums_input.split(',')]
        except ValueError:
            print(f"警告：无效的舰队编号 '{fleet_nums_input}'，使用所有舰队代替。")
            return list(range(1, total_fleets + 1))
    
    def run(self):
        args = self.parse_arguments()
        
        # 获取 fleet_nums，避免用户输入
        fleet_nums = self.get_fleet_nums(args)
        ports = self.fleet_manager.calculate_ports(fleet_nums)
        
        # 处理配置和等待时间
        config_processed = False
        if args.config != -1:
            config_processed = self.config_manager.process_config_command(self.http_handler, ports, args)
        
        # 如果只处理配置，没有其他操作，则退出
        if config_processed and not args.room and not args.quiet and not args.disconnect and not args.login and not args.message:
            return
        
        # Handle message command
        if args.message:
            self.config_manager.process_message_command(self.http_handler, ports, args.message)
            return
        
        # Handle quiet command
        if args.quiet:
            self.http_handler.process_requests(ports, "quiet")
            return
        
        # Handle disconnect command
        if args.disconnect:
            self.http_handler.process_requests(ports, "disconnectRoom")
            return
        
        # Handle login command
        if args.login:
            self.http_handler.send_cookie_requests(self.config_manager.config['filename'], ports)
            return
        
        # Default flow: connect to a room
        if args.room:
            # 直接使用命令行传入的房间号
            room_id = args.room
        else:
            # 如果没有直接指定房间号，则使用交互式界面让用户选择
            room_id = self.room_manager.get_user_choice()
            
        # 无论通过哪种方式获取房间号，都执行相同的连接逻辑
        self.http_handler.process_requests(ports, "disconnectRoom")
        self.http_handler.process_requests(ports, "connectRoom", f"roomid={room_id}") 