import os
import json
import sys
import time
import threading
import inquirer
from concurrent.futures import ThreadPoolExecutor, as_completed

class ConfigManager:
    def __init__(self, config):
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
                # 处理配置文件
                config_file = None
                
                # 检查是否传入了配置文件路径
                if args.config and args.config.endswith('.json'):
                    # 如果提供了完整路径，直接使用
                    if os.path.exists(args.config):
                        config_file = args.config
                    # 如果只提供了文件名，尝试在 config 目录下查找
                    elif os.path.exists(os.path.join('./config', args.config)):
                        config_file = os.path.join('./config', args.config)
                    else:
                        with self.lock:
                            print(f"Error: Config file '{args.config}' not found.")
                        return False
                else:
                    # 没有提供文件路径，使用交互式选择
                    config_file = self.choose_config_file()
                
                # 如果找到配置文件，则应用它
                if config_file:
                    with self.lock:
                        print(f"Loading configuration from: {config_file}")
                    
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
                    return False
                
                # 处理等待时间 - 现在使用单独的 -t/--time 参数
                if args.time and args.time > 0:
                    wait_time = args.time
                    with self.lock:
                        print(f"Waiting for {wait_time} seconds before loading default configuration...")
                    
                    time.sleep(wait_time)
                    default_config_file = "./config/set-default-idle.json"
                    
                    with self.lock:
                        print(f"Loading default configuration from: {default_config_file}")
                        
                    config_data = self.update_config_from_file(default_config_file)
                    
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