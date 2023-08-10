import time
import func

s = func.new_upd_server((func.server_host, func.server_port))

while True:
    data, addr = s.recvfrom(func.buffer_size)
    data = data.decode('utf-8')

    for d in data.split(func.end_string)[:-1]:
        info = d.split()

        if info[0] == '<login>':
            flag = -1
            username, password = info[1], info[2]

            if func.only_number(username):
                if not func.id_to_user_table.get(username):
                    s.sendto(f'<error> no-user'.encode('utf-8'), addr)
                else:
                    flag = 1
            else:
                if not func.username_to_id_table.get(username):
                    s.sendto(f'<error> no-user'.encode('utf-8'), addr)
                else:
                    flag = 2

            if flag != -1:
                user_id = username if flag == 1 else func.username_to_id_table[username]
                username = func.id_to_user_table[user_id]['username']
                # if int(user_id) < 0:
                #     s.sendto('<error> no-login-permissions'.encode('utf-8'), addr)
                # elif func.id_to_user_table[user_id]['password'] == password:
                #     pt = func.new_port()
                #     s.sendto(f'<success> {pt} {user_id} {username}'.encode('utf-8'), addr)
                #     func.new_socket(addr[0], pt, user_id)
                # else:
                #     s.sendto('<error> wrong-password'.encode('utf-8'), addr)

                if func.id_to_user_table[user_id]['password'] == password:
                    pt = func.new_port()
                    s.sendto(f'<success> {pt} {user_id} {username}'.encode('utf-8'), addr)
                    func.new_socket(addr[0], pt, user_id)
                else:
                    s.sendto('<error> wrong-password'.encode('utf-8'), addr)

        elif info[0] == '<register>':
            username, password = info[1], info[2]
            if func.username_to_id_table.get(username):
                s.sendto(f'<error> username-repeated'.encode('utf-8'), addr)
            else:
                func.new_user(username, password)
                s.sendto(f'<success> {func.last_user_id}'.encode('utf-8'), addr)

    time.sleep(0.01)
