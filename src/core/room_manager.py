import os
import json
import threading
import inquirer

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