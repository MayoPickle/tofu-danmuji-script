import os
import time
import sys
import requests
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import inquirer

# Global configuration
CONFIG = {
    'ip_address': '127.0.0.1',
    'start_port': 23330,
    'end_port': 23353,
    'filename': 'cookies.txt',
    'fleet_size': 8
}

class RoomManager:
    def __init__(self, filename="room_ids.json"):
        self.filename = filename
        self.lock = threading.Lock()
    
    def save_room_data(self, room_data):
        with self.lock:
            with open(self.filename, "w") as file:
                json.dump(room_data, file, indent=4)
    
    def load_room_data(self):
        with self.lock:
            if not os.path.exists(self.filename):
                return []
            with open(self.filename, "r") as file:
                return json.load(file)

    def get_user_choice(self):
        room_data = self.load_room_data()
        choices = [f"{item['room_id']} ({item['remark']})" for item in room_data] + ["Enter a new room ID with remark"]
        questions = [inquirer.List('choice', message="Choose a room ID or add new one with remark", choices=choices)]
        answer = inquirer.prompt(questions)
        selected = answer['choice']
        
        if selected == "Enter a new room ID with remark":
            while True:
                room_id = input("Enter new room ID: ")
                if room_id.isdigit(): 
                    remark = input("Enter remark for this room ID: ")
                    room_data.append({"room_id": int(room_id), "remark": remark})
                    self.save_room_data(room_data)
                    return int(room_id)
                else:
                    print("Error: Room ID must be a number.")
        else:
            return int(selected.split(" ")[0])

class FleetManager:
    def __init__(self, config=CONFIG):
        self.config = config
        self.lock = threading.Lock()
    
    def get_fleet_nums(self):
        """获取用户想要调度的 fleet 数量列表。如果输入为0或为空，则返回所有 fleets。"""
        fleet_nums_input = input("Enter the fleet numbers to dispatch (e.g., '1,2,3'), or '0' for all fleets: ")
        if not fleet_nums_input or fleet_nums_input == '0':  # 检查是否为空或为'0'
            total_fleets = (self.config['end_port'] - self.config['start_port'] + 1) // self.config['fleet_size']
            return list(range(1, total_fleets + 1))  # 返回所有可能的 fleet 编号
        fleet_nums = [int(num.strip()) for num in fleet_nums_input.split(',')]
        return fleet_nums

    def calculate_ports(self, fleet_nums):
        """计算多个 fleet 对应的端口范围。"""
        if not fleet_nums or fleet_nums == '0':
            fleet_nums = list(range(1, (self.config['end_port'] - self.config['start_port'] + 1) // self.config['fleet_size'] + 1))
        ports = []
        for num in fleet_nums:
            start_port = self.config['start_port'] + (num - 1) * self.config['fleet_size']
            end_port = start_port + self.config['fleet_size'] - 1
            ports.extend(range(start_port, end_port + 1))
        return ports

class HttpRequestHandler:
    def __init__(self, config=CONFIG):
        self.config = config
        self.lock = threading.Lock()
    
    def send_request(self, url, method='get', data=None, headers=None, delay=0):
        """Send an HTTP request with specified parameters"""
        if delay:
            time.sleep(delay)
        try:
            if method.lower() == 'get':
                response = requests.get(url, headers=headers)
            elif method.lower() == 'post':
                response = requests.post(url, data=data, headers=headers)
            elif method.lower() == 'put':
                response = requests.put(url, data=data, headers=headers)
            elif method.lower() == 'delete':
                response = requests.delete(url, headers=headers)
            else:
                with self.lock:
                    print("Unsupported HTTP method.")
                return
            
            result = f"URL: {url}, Status Code: {response.status_code}, Response: {response.text}"
            with self.lock:
                print(result)
            return result
        except requests.RequestException as e:
            error_msg = f"Error connecting to {url}: {e}"
            with self.lock:
                print(error_msg)
            return error_msg
    
    def process_requests(self, ports, endpoint, param=None):
        """Process requests to multiple ports with multithreading"""
        urls = [f"http://{self.config['ip_address']}:{port}/{endpoint}" for port in ports]
        if param:
            urls = [url + f"?{param}" for url in urls]
        
        with ThreadPoolExecutor(max_workers=len(urls)) as executor:
            futures = [executor.submit(self.send_request, url) for url in urls]
            for future in as_completed(futures):
                future.result()  # Results already printed in send_request
        
        with self.lock:
            print(f"All {endpoint} requests have been processed.")
    
    def send_cookie_requests(self, filename, ports):
        """Send cookie data to specified ports"""
        with open(filename, 'r') as file:
            lines = file.readlines()
        
        cookie_tasks = []
        
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                user_remark = lines[i].strip()
                cookie_data = lines[i+1].strip()
                if i // 2 < len(ports):
                    port = ports[i // 2]
                    cookie_tasks.append((port, user_remark, cookie_data))
        
        with ThreadPoolExecutor(max_workers=len(cookie_tasks)) as executor:
            futures = []
            for port, user_remark, cookie_data in cookie_tasks:
                url = f"http://{self.config['ip_address']}:{port}/customCookie"
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                data = {'cookie': cookie_data}
                futures.append(executor.submit(self.send_request, url, 'post', data, headers))
                with self.lock:
                    print(f"Sending data for {user_remark} to port {port}")
            
            for future in as_completed(futures):
                future.result()
    
    def process_parallel_config_requests(self, ports, config_data_true_list, config_data_false):
        """Process config requests in parallel with multithreading"""
        with ThreadPoolExecutor(max_workers=len(ports) * 2) as executor:
            futures = []
            
            if len(config_data_true_list) == 1:
                config_data_true = config_data_true_list[0]
                for port in ports:
                    url = f"http://{self.config['ip_address']}:{port}/sendSet"
                    data_true = {'set': config_data_true}
                    data_false = {'set': config_data_false}
                    
                    # Submit true config request
                    futures.append(executor.submit(self.send_request, url, 'post', data_true))
                    
                    # Submit false config request with delay
                    futures.append(executor.submit(self.send_request, url, 'post', data_false, delay=5))
            else:
                config_index = 0
                port_index = 0
                while config_index < len(config_data_true_list):
                    if port_index >= len(ports):
                        port_index = 0
                    
                    url = f"http://{self.config['ip_address']}:{ports[port_index]}/sendSet"
                    data_true = {'set': config_data_true_list[config_index]}
                    data_false = {'set': config_data_false}
                    
                    # Submit true config request
                    futures.append(executor.submit(self.send_request, url, 'post', data_true))
                    
                    # Submit false config request with delay
                    futures.append(executor.submit(self.send_request, url, 'post', data_false, delay=5))
                    
                    port_index += 1
                    config_index += 1
            
            # Wait for all futures to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    with self.lock:
                        print(f"Request generated an exception: {exc}")

class ConfigManager:
    def __init__(self, config=CONFIG):
        self.config = config
        self.lock = threading.Lock()
    
    def list_config_files(self, directory='./config'):
        """List all JSON files in the specified directory"""
        with self.lock:
            return [f for f in os.listdir(directory) if f.endswith('.json')]
    
    def choose_config_file(self, directory='./config'):
        """Let the user choose a configuration file from the list"""
        files = self.list_config_files(directory)
        if not files:
            with self.lock:
                print("No configuration files found.")
            return None
        
        question = [inquirer.List('config', message="Choose a configuration file", choices=files)]
        answer = inquirer.prompt(question)
        return os.path.join(directory, answer['config'])
    
    def update_config_from_file(self, config_path):
        """Load and parse configuration from the specified JSON file"""
        with self.lock:
            with open(config_path, 'r') as file:
                file_config = json.load(file)
            return json.dumps(file_config)
    
    def update_advert_in_config(self, config_path, new_advert_text, is_enabled):
        """Update advertisement configuration in the JSON file"""
        with self.lock:
            with open(config_path, 'r') as file:
                config_data = json.load(file)
            
            if 'advert' in config_data:
                if 'adverts' in config_data['advert']:
                    config_data['advert']['adverts'] = new_advert_text
                config_data['advert']['is_open'] = is_enabled
            
            return json.dumps(config_data, indent=4)
    
    def process_config_command(self, http_handler, ports, args):
        """Process configuration command with error handling"""
        try:
            if args.config != -1:
                config_file = self.choose_config_file()
                if config_file:
                    config_data = self.update_config_from_file(config_file)
                    with ThreadPoolExecutor(max_workers=len(ports)) as executor:
                        futures = []
                        for port in ports:
                            url = f"http://{self.config['ip_address']}:{port}/sendSet"
                            data = {'set': config_data}
                            futures.append(executor.submit(http_handler.send_request, url, 'post', data))
                        
                        for future in as_completed(futures):
                            future.result()
                else:
                    with self.lock:
                        print("No config file selected or available.")
                
                if args.config is not None and int(args.config) > 0:
                    time.sleep(int(args.config))
                    config_file = "./config/set-default-idle.json"
                    config_data = self.update_config_from_file(config_file)
                    
                    with ThreadPoolExecutor(max_workers=len(ports)) as executor:
                        futures = []
                        for port in ports:
                            url = f"http://{self.config['ip_address']}:{port}/sendSet"
                            data = {'set': config_data}
                            futures.append(executor.submit(http_handler.send_request, url, 'post', data))
                        
                        for future in as_completed(futures):
                            future.result()
                
                return True
            return False
        
        except KeyboardInterrupt:
            with self.lock:
                print("Interrupt received, updating default configuration...")
            
            config_file = "./config/set-default-idle.json"
            config_data = self.update_config_from_file(config_file)
            
            with ThreadPoolExecutor(max_workers=len(ports)) as executor:
                futures = []
                for port in ports:
                    url = f"http://{self.config['ip_address']}:{port}/sendSet"
                    data = {'set': config_data}
                    futures.append(executor.submit(http_handler.send_request, url, 'post', data))
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        pass
            
            with self.lock:
                print("Default configuration updated on interrupt.")
            sys.exit(0)
    
    def process_message_command(self, http_handler, ports, message):
        """Process message command with multithreading"""
        config_file_path = "./config/set-custom-ad-template.json"
        config_data_true_list = []
        config_data_false = self.update_advert_in_config(config_file_path, "", False)
        
        if '+' in message:
            processed_messages = message.split('+')
            for msg in processed_messages:
                config_data_true_list.append(self.update_advert_in_config(config_file_path, msg, True))
        else:
            for _ in ports:
                config_data_true_list.append(self.update_advert_in_config(config_file_path, message, True))
        
        http_handler.process_parallel_config_requests(ports, config_data_true_list, config_data_false)
        return True

class BiliLiveApp:
    def __init__(self):
        self.room_manager = RoomManager()
        self.fleet_manager = FleetManager()
        self.http_handler = HttpRequestHandler()
        self.config_manager = ConfigManager()
    
    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Control connection operations.")
        parser.add_argument('-d', '--disconnect', action='store_true', help='Only send disconnect requests')
        parser.add_argument('-q', '--quiet', action='store_true', help='Send /quit GET request to all ports')
        parser.add_argument('-l', '--login', action='store_true', help='Send login requests with cookies data to ports')
        parser.add_argument('-c', '--config', nargs='?', const=None, default=-1, help='Optional: Sleep for specified seconds and then load the default configuration file')
        parser.add_argument('-m', '--message', type=str, help='Store a custom message')
        return parser.parse_args()
    
    def run(self):
        args = self.parse_arguments()
        
        fleet_nums = self.fleet_manager.get_fleet_nums()
        ports = self.fleet_manager.calculate_ports(fleet_nums)
        
        # Handle config command
        if self.config_manager.process_config_command(self.http_handler, ports, args):
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
            self.http_handler.send_cookie_requests(CONFIG['filename'], ports)
            return
        
        # Default flow: connect to a room
        chosen_room_id = self.room_manager.get_user_choice()
        self.http_handler.process_requests(ports, "disconnectRoom")
        self.http_handler.process_requests(ports, "connectRoom", f"roomid={chosen_room_id}")

def main():
    app = BiliLiveApp()
    app.run()

if __name__ == "__main__":
    main()
