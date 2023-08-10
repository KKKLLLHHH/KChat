import os
import time
import socket
import threading
import configparser
from datetime import datetime
from csv import DictReader, DictWriter

config_parser = configparser.RawConfigParser()
config_parser.read('./config/network.ini', encoding='utf-8')

back_log = config_parser.getint('base', 'back_log')
buffer_size = config_parser.getint('base', 'buffer_size')
user_port = config_parser.getint('base', 'user_port')
# local_host = socket.gethostbyname(socket.gethostname())
local_host = '127.0.0.1'
server_host, server_port = config_parser.get('base', 'server_host'), config_parser.getint('base', 'server_port')

config_parser = configparser.RawConfigParser()
config_parser.read('./config/message.ini', encoding='utf-8')

end_string = config_parser.get('base', 'end_string')

user_id, user_name = None, None
client_addr, server_addr = None, None
tcp_client, tcp_server = None, None

alive = True

friend_table = []
message_table = []
new_friend_list = []
new_message_list = []
friend_csv_field_name = []
message_csv_field_name = []


def add_message(msg):
    new_message_list.append(msg)


def add_friend(fr):
    new_friend_list.append(fr)


def update_friend_file(fr):
    with open(f'./data/{user_id}_fr.csv', 'a', encoding='utf-8') as ff:
        writer = DictWriter(ff, fieldnames=friend_csv_field_name)
        writer.writerow(fr)


def update_message_file(msg):
    with open(f'./data/{user_id}.csv', 'a', encoding='utf-8') as ff:
        writer = DictWriter(ff, fieldnames=message_csv_field_name)
        writer.writerow(msg)


def rewrite_message_file():
    with open(f'./data/{user_id}.csv', 'w', encoding='utf-8') as ff:
        writer = DictWriter(ff, fieldnames=message_csv_field_name)
        writer.writeheader()
        writer.writerows(message_table)


def new_upd_client():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def new_tcp_client(addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    return s


def new_tcp_server(addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(back_log)
    con, _ = s.accept()
    return con


def new_tcp(serv_addr, clt_addr):
    return new_tcp_server(serv_addr), new_tcp_client(clt_addr)


upd_client = new_upd_client()


def close():
    global alive
    alive = False
    upd_client.close()
    if isinstance(tcp_server, socket.socket):
        tcp_server.send(f'<close>{end_string}'.encode('utf-8'))
        tcp_server.close()
        if isinstance(tcp_client, socket.socket):
            tcp_client.close()


def only_number(string):
    for ch in string[1:]:
        if ch < '0' or ch > '9':
            return False
    return '0' <= string[0] <= '9' or string[0] == '-'


def listen():
    while alive:
        try:
            data = tcp_client.recv(buffer_size).decode('utf-8')
        except ConnectionResetError and ConnectionAbortedError:
            pass
        else:
            for d in data.split(end_string)[:-1]:
                info = d.split()
                if info[0] == '<friend>':
                    r_get_new_friend(d)
                elif info[0] == '<message>':
                    r_get_new_message(d)
                elif info[0] == '<all-new-friend>':
                    r_get_all_new_friend(d)
                elif info[0] == '<all-new-message>':
                    r_get_all_new_message(d)
                elif info[0] == '<return-message-id>':
                    r_get_message_id(d)
                elif info[0] == '<return-searched-user>':
                    r_get_searched_user(d)


def tcp_client_start():
    thread = threading.Thread(target=listen)
    thread.start()


def r_get_new_friend(d):
    info = d.split()
    fr_id, fr_name = info[1], info[2]
    add_friend({
        'fr_id': fr_id,
        'fr_name': fr_name
    })
    print(f'<new-friend> {fr_name} (uid: {fr_id})')


def r_get_new_message(d):
    info = d.split()
    sender_id, message_id, msg_time, msg_type = info[1], info[2], info[3], info[4]
    msg = d[len(f'{info[0]} {info[1]} {info[2]} {info[3]} {info[4]}') + 1:]
    add_message({
        'message': msg,
        'sender_id': sender_id,
        'receiver_id': user_id,
        'time': msg_time,
        'message_id': message_id,
        'message_type': msg_type
    })
    print(f'<new-message> (id: {message_id}) (type: {msg_type}) from {sender_id} at {msg_time} : {msg}')


def r_get_all_new_friend(d):
    fr = eval(d[len('<all-new-friend>') + 1:])
    for f in fr:
        add_friend({
            'fr_id': f[0],
            'fr_name': f[1]
        })
        print(f'<new-friend> {f[1]} (uid: {f[0]})')


def r_get_all_new_message(d):
    msg = eval(d[len('<all-new-message>') + 1:])
    for m in msg:
        add_message({
            'message': m[0],
            'sender_id': m[2],
            'receiver_id': user_id,
            'time': m[3],
            'message_id': m[1],
            'message_type': m[4]
        })
        print(f'<new-message> (id: {m[1]}) (type: {m[4]}) from {m[2]} at {m[3]} : {m[0]}')


def r_get_message_id(d):
    info = d.split()
    receiver_id, msg_time, message_id, msg_type = info[1], info[2], info[3], info[4]
    message = d[len(f'{info[0]} {info[1]} {info[2]} {info[3]} {info[4]}') + 1:]
    add_message({
        'message': message,
        'sender_id': user_id,
        'receiver_id': receiver_id,
        'time': msg_time,
        'message_id': message_id,
        'message_type': msg_type
    })


searching_state = -1
searching_result = None


def r_get_searched_user(d):
    global searching_state, searching_result
    info = d.split()
    searching_state = 1
    searching_result = info[1], info[2]


def f_login(username, password):
    if not password:
        return '<error> 密码为空！'
    for ch in password:
        if not ('a' <= ch <= 'z' or 'A' <= ch <= 'Z' or '0' <= ch <= '9'):
            return '<error> 密码含有非法字符！'
    if len(username) >= 16:
        return '<error> 用户名过长！'
    if not username:
        return '<error> 用户名为空！'
    if not only_number(username):
        for ch in username:
            if not ('a' <= ch <= 'z' or 'A' <= ch <= 'Z' or '0' <= ch <= '9'):
                return '<error> 用户名含有非法字符！'

    upd_client.sendto(f'<login> {username} {password}{end_string}'.encode('utf-8'), (server_host, server_port))

    data, addr = upd_client.recvfrom(buffer_size)
    data = data.decode('utf-8').split()

    if data[0] == '<error>':
        if data[1] == 'no-user':
            return '<error> 没有此用户！'
        elif data[1] == 'wrong-password':
            return '<error> 密码错误！'
        else:
            return '<error> unknown error!'
    elif data[0] == '<success>':
        global user_id, user_name
        global client_addr, server_addr
        global tcp_client, tcp_server
        port, user_id, user_name = int(data[1]), data[2], data[3]
        client_addr, server_addr = (server_host, port), (local_host, user_port)
        tcp_server, tcp_client = new_tcp(server_addr, client_addr)
        tcp_client_start()
        if not os.path.exists(f'./data/{user_id}.csv'):
            with open(f'./data/{user_id}.csv', 'w', encoding='utf-8') as f:
                f.write('message,sender_id,receiver_id,time,message_id,message_type\n\n')
        if not os.path.exists(f'./data/{user_id}_fr.csv'):
            with open(f'./data/{user_id}_fr.csv', 'w', encoding='utf-8') as f:
                f.write('fr_id,fr_name\n\n-10001,好友申请\n\n')
        with open(f'./data/{user_id}.csv', 'r', encoding='utf-8') as f:
            reader = DictReader(f)
            global message_csv_field_name
            message_csv_field_name = reader.fieldnames
            for t in reader:
                message_table.append(t)
        with open(f'./data/{user_id}_fr.csv', 'r', encoding='utf-8') as f:
            reader = DictReader(f)
            global friend_csv_field_name
            friend_csv_field_name = reader.fieldnames
            for t in reader:
                friend_table.append(t)
        return '<success> 登录成功！'


def f_register(username, password, password_a):
    if not password:
        return '<error> 密码为空！'
    if password != password_a:
        return '<error> 密码不一致！'
    for ch in password:
        if not ('a' <= ch <= 'z' or 'A' <= ch <= 'Z' or '0' <= ch <= '9'):
            return '<error> 密码含有非法字符！'
    if len(username) >= 16:
        return '<error> 用户名过长！'
    if not username:
        return '<error> 用户名为空！'
    if only_number(username):
        return '<error> 用户名只包含数字！'
    for ch in username:
        if not ('a' <= ch <= 'z' or 'A' <= ch <= 'Z' or '0' <= ch <= '9' or '\u4e00' <= ch <= '\u9fa5'):
            return '<error> 用户名含有非法字符！'

    upd_client.sendto(f'<register> {username} {password}{end_string}'.encode('utf-8'), (server_host, server_port))

    data, addr = upd_client.recvfrom(buffer_size)
    data = data.decode('utf-8').split()

    if data[0] == '<error>':
        if data[1] == 'username-repeated':
            return '<error> 用户名重复！'
    elif data[0] == '<success>':
        return f'<success> {int(data[1])}'


def f_get_friend():
    tcp_server.send(f'<get-friend>{end_string}'.encode('utf-8'))


def f_get_message():
    tcp_server.send(f'<get-message>{end_string}'.encode('utf-8'))


def f_send_message(message, receiver_id, message_type):
    if receiver_id in [fr['fr_id'] for fr in friend_table] or message_type[0] == '0':
        now = datetime.now()
        tcp_server.send(
            f'<send-message> {receiver_id} {int(time.mktime(now.timetuple()))} {message_type} {message}'
            f'{end_string}'.encode('utf-8'))


def f_search_friend(friend):
    global searching_state, searching_result
    if searching_state == 0:
        return '<error> is searching'
    searching_state = 0
    tcp_server.send(f'<search_friend> {friend}{end_string}'.encode('utf-8'))

    def listen_thread():
        while alive and searching_state != 1:
            time.sleep(0.01)

    thread = threading.Thread(target=listen_thread)
    thread.start()

    thread.join()
    if searching_result:
        return searching_result
    return '<error> unknown error'


def f_refuse_friend_application(fr_id):
    for msg in message_table:
        if msg['sender_id'] == '-10001' and msg['message'].find(f'(uid:{fr_id})') != -1:
            msg['message_type'] = '01'
    rewrite_message_file()

    now = datetime.now()
    tcp_server.send(f'<refuse-application> {fr_id} {int(time.mktime(now.timetuple()))}{end_string}'.encode('utf-8'))


def f_accept_friend_application(fr_id):
    for msg in message_table:
        if msg['sender_id'] == '-10001' and msg['message'].find(f'(uid:{fr_id})') != -1:
            msg['message_type'] = '01'
    rewrite_message_file()

    now = datetime.now()
    tcp_server.send(f'<accept-application> {fr_id} {int(time.mktime(now.timetuple()))}{end_string}'.encode('utf-8'))
