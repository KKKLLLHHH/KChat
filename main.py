from PyQt5.Qt import *
import widget.login
import widget.main
import threading
import time
import func
import sys


def read_qss(file_name):
    with open(file_name, 'r') as f:
        return f.read()


def login():
    result = func.f_login(login_window.login_widget.get_user_name(),
                          login_window.login_widget.get_password()).split()
    if result[0] == '<error>':
        login_window.show_tip(result[1])
    elif result[0] == '<success>':
        login_window.show_tip(f'登录成功！ID:{func.user_id}')
        login_window.show_tip(f'端口号：{func.client_addr} & {func.server_addr}')
        login_window.close()

        get_friend()
        get_message()
        time.sleep(1)

        widget.main.user_id = func.user_id
        widget.main.username = func.user_name
        main_window.message_list_widget.init_message_list_widget(func.friend_table, func.message_table)
        main_window.friend_list_widget.init_friend_list_widget()
        main_window.show()

        friend_info_listen_thread.start()
        message_listen_thread.start()
        reset_thread.start()
        send_thread.start()


def register():
    result = func.f_register(login_window.register_widget.get_user_name(),
                             login_window.register_widget.get_password(),
                             login_window.register_widget.get_password_again()).split()
    if result[0] == '<error>':
        login_window.show_tip(result[1])
    elif result[0] == '<success>':
        login_window.show_tip(f'注册成功！用户ID：{result[1]}')

        login_window.change_to_login()


def get_friend():
    func.f_get_friend()


def get_message():
    func.f_get_message()


def send_message(message, receiver_id, message_type):
    func.f_send_message(message, receiver_id, message_type)


def f_search():
    if main_window.friend_list_widget.mode == 0:
        pass
    elif main_window.friend_list_widget.mode == 1:
        result = func.f_search_friend(main_window.friend_list_widget.search_edit.text())
        print(result)
        if result[0] != 'None':
            main_window.show_user_info(*result)
            # widget.main.UserInfoWidget(*result).show()
        else:
            msg_box = QMessageBox(QMessageBox.Information, '提示', '没有找到对应的用户！')
            msg_box.exec_()


def f_goto(user_id):
    main_window.show_message()
    main_window.chatting_widget.set_fr(user_id)


def f_add(user_id):
    send_message(f'{func.user_name} (uid:{func.user_id}) 想要添加你为好友！', user_id, '00')


def f_change_info():
    pass


def f_accept(fr_id):
    func.f_accept_friend_application(fr_id)


def f_refuse(fr_id):
    func.f_refuse_friend_application(fr_id)


def login_window_init():
    login_window.login_widget.set_f_login(login)
    login_window.register_widget.set_f_submit(register)


def main_window_init():
    widget.main.f_search = f_search
    widget.main.f_goto = f_goto
    widget.main.f_add = f_add
    widget.main.f_change_info = f_change_info
    widget.main.f_accept = f_accept
    widget.main.f_refuse = f_refuse


def new_friend_listener():
    while func.alive:
        if len(func.new_friend_list):
            fr = func.new_friend_list[0]
            print(fr)
            del func.new_friend_list[0]
            func.friend_table.append(fr)
            func.update_friend_file(fr)
            main_window.new_friend_signals.new_friend.emit(fr)
        time.sleep(0.01)


def new_message_listener():
    while func.alive:
        if len(func.new_message_list):
            msg = func.new_message_list[0]
            print(msg)
            del func.new_message_list[0]
            func.message_table.append(msg)
            func.update_message_file(msg)
            main_window.new_message_signals.new_message.emit(msg)
        time.sleep(0.01)


def message_time_reseter():
    while func.alive:
        main_window.message_list_widget.reset_time()
        time.sleep(1)


def message_sender():
    while func.alive:
        if len(widget.main.message_queue):
            msg = widget.main.message_queue[0]
            del widget.main.message_queue[0]
            func.f_send_message(*msg)
        time.sleep(0.01)


friend_info_listen_thread = threading.Thread(target=new_friend_listener)
message_listen_thread = threading.Thread(target=new_message_listener)
reset_thread = threading.Thread(target=message_time_reseter)
send_thread = threading.Thread(target=message_sender)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    login_style = read_qss('./widget/style/login-style.qss')
    main_style = read_qss('./widget/style/main-style.qss')
    widget.main.message_card_style = read_qss('./widget/style/message-card-style.qss')
    widget.main.chatting_widget_style = read_qss('./widget/style/chatting-widget-style.qss')
    widget.main.single_message_style = read_qss('./widget/style/single-message-widget-style.qss')
    widget.main.single_friend_style = read_qss('./widget/style/single-friend-widget-style.qss')
    widget.main.user_info_style = read_qss('./widget/style/user-info-style.qss')
    widget.main.single_friend_application_style = read_qss('./widget/style/single-friend-application-widget-style.qss')

    login_window = widget.login.LoginWindow()
    login_window.setStyleSheet(login_style)
    login_window_init()
    login_window.show()

    main_window = widget.main.MainWindow()
    main_window.setStyleSheet(main_style)
    main_window_init()

    # test
    # login_window.login_widget.user_name_edit.setText('s')
    # login_window.login_widget.password_edit.setText('s')
    # login()
    # main_window.friend_list_widget.mode = 1
    # main_window.friend_list_widget.search_edit.setText('521')
    # search()
    # test

    exit_id = app.exec_()
    func.close()
    sys.exit(exit_id)
