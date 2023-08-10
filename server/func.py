import time
import random
import socket
import threading
import configparser
from csv import DictReader, DictWriter

config_parser = configparser.RawConfigParser()
config_parser.read('./config/network.ini', encoding='utf-8')

back_log = config_parser.getint('base', 'back_log')
buffer_size = config_parser.getint('base', 'buffer_size')
user_port = config_parser.getint('base', 'user_port')
server_host, server_port = config_parser.get('base', 'server_host'), config_parser.getint('base', 'server_port')

config_parser = configparser.RawConfigParser()
config_parser.read('./config/message.ini', encoding='utf-8')

end_string = config_parser.get('base', 'end_string')

port_list = [server_port]
server_list = []
id_to_server_list = dict()

with open('./data/message_id.txt', 'r', encoding='utf-8') as f:
    last_message_id = int(f.readlines()[0].strip().split()[0])
with open('./data/user_id.txt', 'r', encoding='utf-8') as f:
    last_user_id = int(f.readlines()[0].strip().split()[0])
with open('./data/user.csv', 'r', encoding='utf-8') as f:
    reader = DictReader(f)
    user_table = []
    username_to_id_table = dict()
    id_to_user_table = dict()
    user_csv_field_name = reader.fieldnames
    for t in reader:
        user_table.append(t)
        username_to_id_table[t['username']] = t['id']
        id_to_user_table[t['id']] = dict()
        for fn in user_csv_field_name:
            if fn == 'id':
                continue
            id_to_user_table[t['id']][fn] = t[fn]

with open('./data/relation.csv', 'r', encoding='utf-8') as f:
    reader = DictReader(f)
    relation_table = []
    relation_csv_field_name = reader.fieldnames
    for t in reader:
        relation_table.append(t)
with open('./data/message.csv', 'r', encoding='utf-8') as f:
    reader = DictReader(f)
    message_table = []
    message_csv_field_name = reader.fieldnames
    for t in reader:
        message_table.append(t)
with open('./data/friend_info.csv', 'r', encoding='utf-8') as f:
    reader = DictReader(f)
    friend_info_table = []
    friend_info_csv_field_name = reader.fieldnames
    for t in reader:
        friend_info_table.append(t)


def update_files():
    while True:
        with open('./data/message_id.txt', 'w', encoding='utf-8') as ff:
            ff.write(str(last_message_id))
        with open('./data/relation.csv', 'w', encoding='utf-8') as ff:
            writer = DictWriter(ff, fieldnames=relation_csv_field_name)
            writer.writeheader()
            writer.writerows(relation_table)
        with open('./data/message.csv', 'w', encoding='utf-8') as ff:
            writer = DictWriter(ff, fieldnames=message_csv_field_name)
            writer.writeheader()
            writer.writerows(message_table)
        with open('./data/friend_info.csv', 'w', encoding='utf-8') as ff:
            writer = DictWriter(ff, fieldnames=friend_info_csv_field_name)
            writer.writeheader()
            writer.writerows(friend_info_table)
        time.sleep(1.5)


update_files_thread = threading.Thread(target=update_files)
update_files_thread.start()


# def get_friend(user_id):
#     result = []
#     for rel in relation_table:
#         if rel['id1'] == user_id:
#             result.append((rel['id2'], id_to_user_table[rel['id2']]['username']))
#     return result


def get_new_friend(user_id):
    result = []
    for fr in friend_info_table:
        if fr['receiver_id'] == user_id:
            result.append((fr['fr_id'], fr['fr_name']))
    ind = -1
    while (ind := ind + 1) < len(friend_info_table):
        if friend_info_table[ind]['receiver_id'] == user_id:
            del friend_info_table[ind]
            ind -= 1
    return result


def get_new_message(user_id):
    result = []
    for msg in message_table:
        if msg['receiver_id'] == user_id:
            result.append((msg['message'], msg['message_id'], msg['sender_id'], msg['time'], msg['message_type']))
    ind = -1
    while (ind := ind + 1) < len(message_table):
        if message_table[ind]['receiver_id'] == user_id:
            del message_table[ind]
            ind -= 1
    return result


def send_new_friend_info(receiver_id, fr_id, fr_name):
    if id_to_server_list.get(receiver_id):
        id_to_server_list[receiver_id].send(f'<friend> {fr_id} {fr_name}{end_string}'.encode('utf-8'))
    else:
        friend_info_table.append({
            'receiver_id': receiver_id,
            'fr_id': fr_id,
            'fr_name': fr_name,
        })


def send_message(msg, sender_id, receiver_id, msg_time, msg_type):
    global last_message_id
    last_message_id += 1

    if id_to_server_list.get(receiver_id):
        id_to_server_list[receiver_id].send(
            f'<message> {"-10001" if msg_type[0] == "0" else sender_id} {last_message_id} '
            f'{msg_time} {msg_type} {msg}{end_string}'
            .encode('utf-8'))
    else:
        message_table.append({
            'message': msg,
            'sender_id': '-10001' if msg_type[0] == '0' else sender_id,
            'receiver_id': receiver_id,
            'time': msg_time,
            'message_id': last_message_id,
            'message_type': msg_type
        })


class Server:
    def __init__(self, user_host, serv_port, user_id):
        self.client_host = user_host
        self.client_port = user_port
        self.client_addr = self.client_host, self.client_port

        self.server_host = server_host
        self.server_port = serv_port
        self.server_addr = self.server_host, self.server_port

        self.user_id = user_id
        self.username = id_to_user_table[self.user_id]['username']

        self.client, self.server = new_tcp(self.client_addr, self.server_addr)

        self.thread = threading.Thread(target=self.listen)
        self.alive = True

        server_list.append(self)
        id_to_server_list[self.user_id] = self

    def send(self, data):
        self.server.send(data)

    def listen(self):
        while self.alive:
            try:
                data = self.client.recv(buffer_size).decode('utf-8')
            except ConnectionResetError:
                self.close()
            else:
                for d in data.split(end_string)[:-1]:
                    info = d.split()
                    global last_message_id

                    if info[0] == '<close>':
                        self.close()
                    elif info[0] == '<get-friend>':
                        self.send(f'<all-new-friend> {get_new_friend(self.user_id)}{end_string}'.encode('utf-8'))
                    elif info[0] == '<get-message>':
                        self.send(f'<all-new-message> {get_new_message(self.user_id)}{end_string}'.encode('utf-8'))
                    elif info[0] == '<send-message>':
                        receiver_id, msg_time, msg_type = info[1], info[2], info[3]
                        msg = d[len(f'{info[0]} {info[1]} {info[2]} {info[3]}') + 1:]
                        send_message(msg, self.user_id, receiver_id, msg_time, msg_type)

                        if msg_type[0] == '0':
                            last_message_id += 1
                            msg = f'已经向 {id_to_user_table[receiver_id]["username"]} (uid: {receiver_id}) 发送好友申请.'
                            send_message(msg, '-10001', self.user_id, msg_time, '1')
                        else:
                            self.send(
                                f'<return-message-id> {receiver_id} {msg_time} {last_message_id} {msg_type} {msg}'
                                f'{end_string}'
                                .encode('utf-8'))
                    elif info[0] == '<search_friend>':
                        user = info[1]
                        if only_number(user) and id_to_user_table.get(user):
                            user_id, user_name = user, id_to_user_table[user]['username']
                            self.send(f'<return-searched-user> {user_id} {user_name}{end_string}'.encode('utf-8'))
                        elif username_to_id_table.get(user):
                            user_id, user_name = username_to_id_table[user], user
                            self.send(f'<return-searched-user> {user_id} {user_name}{end_string}'.encode('utf-8'))
                        else:
                            self.send(f'<return-searched-user> {None} {None}{end_string}'.encode('utf-8'))
                    elif info[0] == '<refuse-application>':
                        fr_id = info[1]
                        msg_time = info[2]

                        msg = f'{self.username} (uid: {self.user_id}) 拒绝了你的好友申请.'
                        send_message(msg, '-10001', fr_id, msg_time, '1')

                        msg = f'已拒绝 {id_to_user_table[fr_id]["username"]} (uid: {fr_id}) 的好友申请.'
                        send_message(msg, '-10001', self.user_id, msg_time, '1')
                    elif info[0] == '<accept-application>':
                        fr_id = info[1]
                        msg_time = info[2]

                        msg = f'{self.username} (uid: {self.user_id}) 通过了你的好友申请.'
                        send_message(msg, '-10001', fr_id, msg_time, '1')

                        msg = f'已通过 {id_to_user_table[fr_id]["username"]} (uid: {fr_id}) 的好友申请.'
                        send_message(msg, '-10001', self.user_id, msg_time, '1')

                        relation_table.append({'id1': self.user_id, 'id2': fr_id})
                        relation_table.append({'id1': fr_id, 'id2': self.user_id})
                        send_new_friend_info(fr_id, self.user_id, self.username)
                        send_new_friend_info(self.user_id, fr_id, id_to_user_table[fr_id]['username'])

                        msg = '系统：我们已成为好友，快来打个招呼吧！'
                        send_message(msg, self.user_id, fr_id, msg_time, '1')
                        self.send(
                            f'<return-message-id> {fr_id} {msg_time} {last_message_id} {"1"} {msg}'
                            f'{end_string}'
                            .encode('utf-8'))

            time.sleep(0.01)

    def start(self):
        self.thread.start()

    def close(self):
        self.alive = False
        server_list.remove(self)
        port_list.remove(self.server_port)
        del id_to_server_list[self.user_id]
        self.server.close()
        self.client.close()
        print(f'user {self.username} (from {self.server_host}:{self.server_port}) leaves.')


def new_user(username, password):
    global last_user_id
    last_user_id += 1
    username_to_id_table[username] = str(last_user_id)
    id_to_user_table[str(last_user_id)] = {'username': username, 'password': password}
    user_table.append({'id': str(last_user_id), 'username': username, 'password': password})
    relation_table.append({'id1': '-10001', 'id2': str(last_user_id)})
    relation_table.append({'id1': str(last_user_id), 'id2': '-10001'})
    send_new_friend_info(last_user_id, '-10001', '好友申请')
    with open('./data/user_id.txt', 'w', encoding='utf-8') as ff:
        ff.write(str(last_user_id))
    with open('./data/user.csv', 'a', encoding='utf-8') as ff:
        writer = DictWriter(ff, fieldnames=user_csv_field_name)
        writer.writerow({'id': str(last_user_id), 'username': username, 'password': password})


def new_port():
    while (pt := random.randint(10000, 19999)) in port_list:
        pass
    port_list.append(pt)
    return pt


def new_upd_server(addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(addr)
    return s


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


def new_tcp(client_addr, server_addr):
    return new_tcp_client(client_addr), new_tcp_server(server_addr)


def only_number(string):
    for ch in string[1:]:
        if ch < '0' or ch > '9':
            return False
    return '0' <= string[0] <= '9' or string[0] == '-'


def new_socket(user_host, serv_port, user_id):
    s = Server(user_host, serv_port, user_id)
    s.start()
