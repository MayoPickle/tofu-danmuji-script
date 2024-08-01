import os
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import inquirer

from arg_handler import read_and_send_cookies

ip_address = '127.0.0.1'
start_port = 23330
end_port = 23352
num_ports = end_port - start_port + 1
filename = 'cookies.txt'

def save_room_data(room_data, filename="room_ids.json"):
    with open(filename, "w") as file:
        json.dump(room_data, file, indent=4)

def load_room_data(filename="room_ids.json"):
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as file:
        return json.load(file)

def get_user_choice(room_data):
    choices = [f"{item['room_id']} ({item['remark']})" for item in room_data] + ["Enter a new room ID with remark"]
    questions = [
        inquirer.List('choice',
                      message="Choose a room ID or add new one with remark",
                      choices=choices,
                      ),
    ]
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

def send_request(url):
    try:
        response = requests.get(url)
        return f"URL: {url}, Status Code: {response.status_code}"
    except requests.RequestException as e:
        return f"Error connecting to {url}: {e}"

def process_requests(room_id, only_disconnect, single_threaded):

    disconnect_urls = [f"http://{ip_address}:{port}/disconnectRoom" for port in range(start_port, end_port + 1)]
    
    if single_threaded:
        for url in disconnect_urls:
            print(send_request(url))
        if not only_disconnect:
            connect_urls = [f"http://{ip_address}:{port}/connectRoom?roomid={room_id}" for port in range(start_port, end_port + 1)]
            for url in connect_urls:
                print(send_request(url))
    else:
        with ThreadPoolExecutor(max_workers=num_ports) as executor:
            future_to_url = {executor.submit(send_request, url): url for url in disconnect_urls}
            for future in as_completed(future_to_url):
                print(future.result())

            if not only_disconnect:
                connect_urls = [f"http://{ip_address}:{port}/connectRoom?roomid={room_id}" for port in range(start_port, end_port + 1)]
                future_to_url = {executor.submit(send_request, url): url for url in connect_urls}
                for future in as_completed(future_to_url):
                    print(future.result())

def send_quit_request(port):
    url = f"http://{ip_address}:{port}/quit"
    response = requests.get(url)
    print(f"Sent /quit to port {port}: {response.status_code}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control connection operations.")
    parser.add_argument('-d', '--disconnect', action='store_true', help='Only send disconnect requests')
    parser.add_argument('-s', '--single', action='store_true', help='Use single-threaded mode for requests')
    parser.add_argument('-q', '--quiet', action='store_true', help='Send /quit GET request to all ports after operations')
    parser.add_argument('-l', '--login', action='store_true', help='Send /login cookie data to server')
    args = parser.parse_args()

    # 如果需要选择房间ID
    if not args.quiet:  # 现在将判断条件修改为当不是执行-quiet操作时才进行房间选择和请求发送
        if not args.disconnect:
            room_data = load_room_data()
            chosen_room_id = get_user_choice(room_data)
            process_requests(chosen_room_id, args.disconnect, args.single)
        else:
            process_requests(None, args.disconnect, args.single)

    # 单独处理-quiet参数，不依赖room_id的选择
    if args.quiet:
        for port in range(start_port, end_port):  # Assuming ports from 23333 to 23340
            send_quit_request(port)

    if args.login:
        read_and_send_cookies(filename, start_port, end_port)
