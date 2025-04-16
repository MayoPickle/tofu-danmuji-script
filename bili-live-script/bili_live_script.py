import os
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import inquirer
import threading

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
            self.save_room_data(room_data)
            return room_id
        else:
            return selected.split(" ")[0]

class RequestHandler:
    def __init__(self, ip_address='127.0.0.1', start_port=23333, end_port=23340):
        self.ip_address = ip_address
        self.start_port = start_port
        self.end_port = end_port
        self.num_ports = end_port - start_port + 1
        self.lock = threading.Lock()
    
    def send_request(self, url):
        try:
            response = requests.get(url)
            result = f"URL: {url}, Status Code: {response.status_code}"
            with self.lock:
                print(result)
            return result
        except requests.RequestException as e:
            error_msg = f"Error connecting to {url}: {e}"
            with self.lock:
                print(error_msg)
            return error_msg
    
    def process_disconnect_requests(self):
        disconnect_urls = [f"http://{self.ip_address}:{port}/disconnectRoom" 
                         for port in range(self.start_port, self.end_port + 1)]
        
        with ThreadPoolExecutor(max_workers=self.num_ports) as executor:
            futures = [executor.submit(self.send_request, url) for url in disconnect_urls]
            for future in as_completed(futures):
                future.result()  # Results are already printed in send_request
        
        print("All disconnect requests have been processed.")
    
    def process_connect_requests(self, room_id):
        connect_urls = [f"http://{self.ip_address}:{port}/connectRoom?roomid={room_id}" 
                      for port in range(self.start_port, self.end_port + 1)]
        
        with ThreadPoolExecutor(max_workers=self.num_ports) as executor:
            futures = [executor.submit(self.send_request, url) for url in connect_urls]
            for future in as_completed(futures):
                future.result()  # Results are already printed in send_request
        
        print("All connect requests have been processed.")
    
    def process_all_requests(self, room_id, only_disconnect=False):
        # First process all disconnect requests
        self.process_disconnect_requests()
        
        # Then process connect requests if not in disconnect-only mode
        if not only_disconnect:
            self.process_connect_requests(room_id)

def main():
    parser = argparse.ArgumentParser(description="Control connection operations.")
    parser.add_argument('-d', '--disconnect', action='store_true', help='Only send disconnect requests')
    args = parser.parse_args()

    room_manager = RoomManager()
    request_handler = RequestHandler()

    if args.disconnect:
        request_handler.process_all_requests(None, only_disconnect=True)
    else:
        chosen_room_id = room_manager.get_user_choice()
        request_handler.process_all_requests(chosen_room_id, only_disconnect=False)

if __name__ == "__main__":
    main()
