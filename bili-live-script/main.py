import os
import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import inquirer

# 全局配置变量
CONFIG = {
    'ip_address': '127.0.0.1',
    'start_port': 23330,
    'end_port': 23353,
    'filename': 'cookies.txt',
    'fleet_size': 8
}

def save_room_data(room_data):
    with open("room_ids.json", "w") as file:
        json.dump(room_data, file, indent=4)

def load_room_data():
    if not os.path.exists("room_ids.json"):
        return []
    with open("room_ids.json", "r") as file:
        return json.load(file)

def get_user_choice(room_data):
    choices = [f"{item['room_id']} ({item['remark']})" for item in room_data] + ["Enter a new room ID with remark"]
    questions = [inquirer.List('choice', message="Choose a room ID or add new one with remark", choices=choices)]
    answer = inquirer.prompt(questions)
    selected = answer['choice']
    if selected == "Enter a new room ID with remark":
        room_id = input("Enter new room ID: ")
        remark = input("Enter remark for this room ID: ")
        room_data.append({"room_id": room_id, "remark": remark})
        save_room_data(room_data)
        return room_id
    else:
        return selected.split(" ")[0]

def get_fleet_nums():
    """获取用户想要调度的 fleet 数量列表。如果输入为0或为空，则返回所有 fleets。"""
    fleet_nums_input = input("Enter the fleet numbers to dispatch (e.g., '1,2,3'), or '0' for all fleets: ")
    if not fleet_nums_input or fleet_nums_input == '0':  # 检查是否为空或为'0'
        total_fleets = (CONFIG['end_port'] - CONFIG['start_port'] + 1) // CONFIG['fleet_size']
        return list(range(1, total_fleets + 1))  # 返回所有可能的 fleet 编号
    fleet_nums = [int(num.strip()) for num in fleet_nums_input.split(',')]
    return fleet_nums

def calculate_ports(fleet_nums):
    """计算多个 fleet 对应的端口范围。"""
    if not fleet_nums or fleet_nums == '0':
        fleet_nums = list(range(1, (CONFIG['end_port'] - CONFIG['start_port'] + 1) // CONFIG['fleet_size'] + 1))
    ports = []
    for num in fleet_nums:
        start_port = CONFIG['start_port'] + (num - 1) * CONFIG['fleet_size']
        end_port = start_port + CONFIG['fleet_size'] - 1
        ports.extend(range(start_port, end_port + 1))
    return ports

def send_post_request(port, cookie_data):
    url = f"http://{CONFIG['ip_address']}:{port}/customCookie"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'cookie': cookie_data}
    response = requests.post(url, headers=headers, data=data)
    print(f"Response from server on port {port}: {response.status_code} - {response.text}")

def read_and_send_cookies(filename, start_port, end_port):
    with open(filename, 'r') as file:
        lines = file.readlines()

    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            user_remark = lines[i].strip()
            cookie_data = lines[i+1].strip()
            if start_port <= end_port:
                send_post_request(start_port, cookie_data)
                print(f"Sent data for {user_remark} to port {start_port} with {cookie_data}")
                start_port += 1

def send_request(url, method='get', data=None, headers=None, delay=0):
    """
    Send an HTTP request of specified type to the given URL.

    :param url: URL to which the request is to be sent.
    :param method: Type of the HTTP request (e.g., 'get', 'post').
    :param data: Data to be sent in the case of a 'post' request.
    :param headers: Headers to be used for the request.
    :return: A string describing the result of the request.
    """
    if delay:
        time.sleep(delay)
    try:
        # Use the requests library's method corresponding to the specified type
        if method.lower() == 'get':
            response = requests.get(url, headers=headers)
        elif method.lower() == 'post':
            response = requests.post(url, data=data, headers=headers)
        elif method.lower() == 'put':
            response = requests.put(url, data=data, headers=headers)
        elif method.lower() == 'delete':
            response = requests.delete(url, headers=headers)
        else:
            print("Unsupported HTTP method.")

        print(f"URL: {url}, Status Code: {response.status_code}, Response: {response.text}")
    except requests.RequestException as e:
        print(f"Error connecting to {url}: {e}")

def process_requests(single_threaded=True, ports=[], endpoint=None, param=""):
    requests_urls = [f"http://{CONFIG['ip_address']}:{port}/{endpoint}" for port in ports]
    if param:
        requests_urls = [url + f"?{param}" for url in requests_urls]
    if single_threaded:
        handle_requests(requests_urls)
    else:
        handle_requests_concurrent(requests_urls)
    
def handle_requests_concurrent(request_urls):
    with ThreadPoolExecutor(max_workers=len(request_urls)) as executor:
        future_to_url = {executor.submit(send_request, url): url for url in request_urls}
        for future in as_completed(future_to_url):
            print(future.result())

def handle_requests(request_urls):
    for url in request_urls:
        print(send_request(url))

def send_quit_request(port):
    url = f"http://{CONFIG['ip_address']}:{port}/quit"
    response = requests.get(url)
    print(f"Sent /quit to port {port}: {response.status_code}")

def list_config_files(directory):
    """列出指定目录中的所有 JSON 文件."""
    return [f for f in os.listdir(directory) if f.endswith('.json')]

def update_config_from_file(config_path):
    """从指定的 JSON 文件更新全局配置."""
    with open(config_path, 'r') as file:
        file_config = json.load(file)

    # 将字典转换为 JSON 字符串
    json_string = json.dumps(file_config)
    return json_string

def choose_config_file(directory='./config'):
    """让用户从列表中选择一个配置文件."""
    files = list_config_files(directory)
    if not files:
        print("No configuration files found.")
        return None
    question = [inquirer.List('config', message="Choose a configuration file", choices=files)]
    answer = inquirer.prompt(question)
    return os.path.join(directory, answer['config'])

def update_advert_in_config(config_path, new_advert_text, is_enabled):
    """Update the 'advert' parameter in the JSON configuration file, including text and enable status."""
    with open(config_path, 'r') as file:
        config_data = json.load(file)

    # Check if 'advert' exists and update the 'adverts' and 'is_open' fields
    if 'advert' in config_data:
        if 'adverts' in config_data['advert']:
            config_data['advert']['adverts'] = new_advert_text
        # Update the 'is_open' field based on is_enabled argument
        config_data['advert']['is_open'] = is_enabled

    # Serialize the modified configuration back to a JSON string with indentation for readability
    updated_json_string = json.dumps(config_data, indent=4)
    return updated_json_string

def send_requests_in_parallel(ports, config_file_data_true_list, config_file_data_false, single_threaded):
    if single_threaded:
        # 使用单线程发送请求
        for port in ports:
            request_url = f"http://{CONFIG['ip_address']}:{port}/sendSet"
            if len(config_file_data_true_list) == 1:
                config_data_true = config_file_data_true_list[0]
                send_request(request_url, "post", {'set': config_data_true})
                time.sleep(5)
                send_request(request_url, "post", {'set': config_file_data_false})
            else:
                for config_data_true in config_file_data_true_list:
                    send_request(request_url, "post", {'set': config_data_true})
                    time.sleep(5)
                    send_request(request_url, "post", {'set': config_file_data_false})
    else:
        # 使用多线程发送请求
        with ThreadPoolExecutor(max_workers=len(ports)) as executor:
            future_to_url = {}
            for port in ports:
                request_url = f"http://{CONFIG['ip_address']}:{port}/sendSet"
                if len(config_file_data_true_list) == 1:
                    config_data_true = config_file_data_true_list[0]
                    future = executor.submit(send_request, request_url, "post", {'set': config_data_true})
                    future_to_url[future] = request_url
                    future = executor.submit(send_request, request_url, "post", {'set': config_file_data_false}, delay=5)
                    future_to_url[future] = request_url
                else:
                    for config_data_true in config_file_data_true_list:
                        future = executor.submit(send_request, request_url, "post", {'set': config_data_true})
                        future_to_url[future] = request_url
                        future = executor.submit(send_request, request_url, "post", {'set': config_file_data_false}, delay=5)
                        future_to_url[future] = request_url

            # Collect and display results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    print(result)
                except Exception as exc:
                    print(f"{url} generated an exception: {exc}")

# def send_requests_in_parallel(ports, config_file_data_true_list, config_file_data_false, single_threaded):
#     with ThreadPoolExecutor(max_workers=len(ports)) as executor:
#         future_to_url = {}

#         # Check the length of config_file_data_true_list
#         if len(config_file_data_true_list) == 1:
#             # If there is only one element, send this element to all ports
#             config_data_true = config_file_data_true_list[0]
#             for port in ports:
#                 request_url = f"http://{CONFIG['ip_address']}:{port}/sendSet"

#                 # Submit the first request with no delay
#                 future = executor.submit(send_request, request_url, "post", {'set': config_data_true})
#                 future_to_url[future] = request_url

#                 # Submit the second request with a 5-second delay
#                 future = executor.submit(send_request, request_url, "post", {'set': config_file_data_false}, delay=5)
#                 future_to_url[future] = request_url
#         else:
#             # If there are multiple elements, send them as originally planned
#             for port, config_data_true in zip(ports, config_file_data_true_list):
#                 request_url = f"http://{CONFIG['ip_address']}:{port}/sendSet"

#                 # Submit the first request with no delay
#                 future = executor.submit(send_request, request_url, "post", {'set': config_data_true})
#                 future_to_url[future] = request_url

#                 # Submit the second request with a 5-second delay
#                 future = executor.submit(send_request, request_url, "post", {'set': config_file_data_false}, delay=5)
#                 future_to_url[future] = request_url

#         # Collect and display results as they complete
#         for future in as_completed(future_to_url):
#             url = future_to_url[future]
#             try:
#                 result = future.result()
#                 print(result)
#             except Exception as exc:
#                 print(f"{url} generated an exception: {exc}")

def main():
    parser = argparse.ArgumentParser(description="Control connection operations.")
    parser.add_argument('-d', '--disconnect', action='store_true', help='Only send disconnect requests')
    parser.add_argument('-s', '--single', action='store_true', help='Use single-threaded mode for requests')
    parser.add_argument('-q', '--quiet', action='store_true', help='Send /quit GET request to all ports')
    parser.add_argument('-l', '--login', action='store_true', help='Send login requests with cookies data to ports')
    parser.add_argument('-c', '--config', action='store_true', help='Load a configuration file from ./config directory')
    parser.add_argument('-m', '--message', type=str, help='Store a custom message')
    args = parser.parse_args()

    fleet_nums = get_fleet_nums()
    ports = calculate_ports(fleet_nums)

    if args.config:
        config_file = choose_config_file()
        if config_file:
            config_file_data = update_config_from_file(config_file)
            requests_urls = [f"http://{CONFIG['ip_address']}:{port}/sendSet" for port in ports]
            for request_url in requests_urls:
                data = {'set': config_file_data}
                send_request(request_url, method='post', data=data, headers=None)
        else:
            print("No config file selected or available.")
        return
    
    if args.message:
        config_file_path = "./config/set-custom-ad-template.json"
        config_file_data_true_list = []
        config_file_data_false = update_advert_in_config(config_file_path, "", False)
        if '+' in args.message:
            processed_message = args.message.split('+')
        else:
            processed_message = [args.message]

        for message in processed_message:
            config_file_data_true_list.append(update_advert_in_config(config_file_path, message, True))
            print(len(config_file_data_true_list))
            
        send_requests_in_parallel(ports, config_file_data_true_list, config_file_data_false, args.single)
        return

    # if args.message:
    #     config_file_path = "./config/set-custom-ad-template.json"
    #     if '+' in args.message:
    #         processed_message = args.message.split('+')
    #     else:
    #         processed_message = args.message
    #     config_file_data_true = update_advert_in_config(config_file_path, processed_message, True)
    #     config_file_data_false = update_advert_in_config(config_file_path, processed_message, False)

    #     requests_urls = [f"http://{CONFIG['ip_address']}:{port}/sendSet" for port in ports]
    #     for request_url in requests_urls:
    #         data = {'set': config_file_data_true}
    #         send_request(request_url, method='post', data=data, headers=None)
    #         time.sleep(5)
    #         data = {'set': config_file_data_false}
    #         send_request(request_url, method='post', data=data, headers=None)
    #     else:
    #         print("No config file selected or available.")
    #     return

    if args.quiet:
        process_requests(args.single, ports, endpoint="quiet", param=None)
        return  # 结束程序执行

    if args.disconnect:
        # 为连接或断开连接操作计算端口
        process_requests(args.single, ports, endpoint="disconnectRoom", param=None)
        return

    if args.login:
        read_and_send_cookies(CONFIG['filename'], ports[0], ports[-1])
        return

    # chose a room number to connect
    room_data = load_room_data()

    # connect with the roomid
    chosen_room_id = get_user_choice(room_data)
    
    # dissconnect room
    process_requests(args.single, ports, endpoint="disconnectRoom", param=None)

    param = f"roomid={chosen_room_id}"
    process_requests(args.single, ports, endpoint="connectRoom", param=param)


if __name__ == "__main__":
    main()
