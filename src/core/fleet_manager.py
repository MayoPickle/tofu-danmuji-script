import threading

class FleetManager:
    def __init__(self, config):
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