import requests

def send_post_request(port, cookie_data):
    url = f"http://localhost:{port}/customCookie"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'cookie': cookie_data}
    response = requests.post(url, headers=headers, data=data)
    print(f"Response from server on port {port}: {response.status_code} - {response.text}")

def read_and_send_cookies(filename, start_port, end_port):
    with open(filename, 'r') as file:
        lines = file.readlines()

    port = 23330  # 开始端口
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):  # 确保cookie数据行存在
            user_remark = lines[i].strip()  # 用户备注行（不用于POST请求，只用于标记）
            cookie_data = lines[i+1].strip()
            send_post_request(start_port, cookie_data)
            print(f"Sent data for {user_remark} to port {port}")
            start_port += 1  # 移动到下一个端口
            if start_port > end_port:  # 如果端口超出范围则重置
                break
