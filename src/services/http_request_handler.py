import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class HttpRequestHandler:
    def __init__(self, config):
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