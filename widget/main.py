import re

from PyQt5.Qt import *
from time import mktime
from datetime import datetime
from widget.base import BaseWindow

user_id = '0'
username = ''

friend_list = dict()
message_list = list()
user_to_message_dict = dict()

message_card_style = ''
chatting_widget_style = ''
single_message_style = ''
single_friend_style = ''
user_info_style = ''
single_friend_application_style = ''

replace_char = {
    ',': '[dh]',
    '\n': '[hh]'
}

message_queue = list()


# (KChat/main.py).main_window_init() -> (KChat/main.py).goto()
# (KChar/main.oy).main_window_init() -> (KChat/main.py).add()
f_search = f_goto = f_add = f_change_info = f_accept = f_refuse = None


def init_button(text=None, obj_name=None, fixed_width=None, fixed_height=None, func=None):
    button = QPushButton()
    if text is not None:
        button.setText(text)
    if obj_name is not None:
        button.setObjectName(obj_name)
    if fixed_width is not None:
        button.setFixedWidth(fixed_width)
    if fixed_height is not None:
        button.setFixedHeight(fixed_height)
    if func is not None:
        button.clicked.connect(func)
    return button


def encode_message(m):
    for ch, ch2 in replace_char.items():
        m = m.replace(ch, ch2)
    return m


def decode_message(m):
    for ch, ch2 in replace_char.items():
        m = m.replace(ch2, ch)
    return m


def get_string_length(string):
    length = 0
    for ch in string:
        length += 2 if '\u4e00' <= ch <= '\u9fa5' else 1
    return length


def get_message_tuple(msg):
    return (
        '-10001' if msg['message_type'][0] == '0' and msg['receiver_id'] != user_id else msg['receiver_id'],
        '-10001' if msg['message_type'][0] == '0' and msg['sender_id'] != user_id else msg['sender_id'],
        msg['message'],
        msg['time'],
        msg['message_type'],
        msg['message_id'],
    )


def get_message_fr_id(msg):
    if msg['message_type'][0] == '0':
        return '-10001'
    return msg['sender_id'] if msg['sender_id'] != user_id else msg['receiver_id']


def add_message_to_user_to_message_dict(msg):
    fr_id = get_message_fr_id(msg)
    if user_to_message_dict.get(fr_id):
        user_to_message_dict[fr_id].insert(0, get_message_tuple(msg))
    else:
        user_to_message_dict.setdefault(fr_id, []).append(get_message_tuple(msg))


# MainWindow.new_message_signals
class NewMessageSignals(QObject):
    new_message = pyqtSignal(dict)


# MainWindow.new_friend_signals
class NewFriendSignals(QObject):
    new_friend = pyqtSignal(dict)


class MainWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.__init_data()
        self.__init_view()

        self.button_image_name = {
            self.self_info_button: 'info',
            self.message_button: 'message',
            self.friend_button: 'friend',
            self.shrink_button: 'shrink',
            self.end_button: 'end',
            self.out_button: 'out'
        }
        self.selected_button = self.message_button
        self.show_message()

    def __init_data(self):
        self.window_opacity = 1
        self.button_style = {
            'unselected': """
                QPushButton {
                    border-image: url('./image/%s.png');
                }
                QPushButton:hover {
                    border-image: url('./image/%s.png');
                    border-radius: 10px;
                    background-color: rgba(255, 225, 125, 0.5);
                }
            """,
            'selected': """
                QPushButton {
                    border-image: url('./image/%s.png');
                    border-radius: 10px;
                    background-color: rgba(255, 225, 125);
                }
            """
        }

        self.new_message_signals = NewMessageSignals()
        self.new_message_signals.new_message.connect(self.new_message)

        self.new_friend_signals = NewFriendSignals()
        self.new_friend_signals.new_friend.connect(self.new_friend)

    def __init_view(self):
        self.setWindowTitle('KChat')
        self.resize(1200, 675)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.user_info_widget = UserInfoWidget('-1', 'None')

        """
            main-widget
        """
        self.main_widget = QWidget()
        self.main_layout = QGridLayout()
        self.main_widget.setLayout(self.main_layout)
        self.main_widget.setObjectName('main-main-widget')

        self.tool_widget = QWidget()
        self.tool_layout = QVBoxLayout()
        self.tool_widget.setLayout(self.tool_layout)
        self.tool_widget.setObjectName('main-tool-widget')
        self.tool_widget.setFixedWidth(60)

        self.message_list_widget = MessageListWidget()
        self.message_list_widget.setFixedWidth(250)
        self.message_list_widget.message_list_widget.itemClicked.connect(self.message_item_clicked)

        self.chatting_widget = ChattingWidget('')

        self.friend_list_widget = FriendListWidget()
        self.friend_list_widget.setFixedWidth(250)
        self.friend_list_widget.friend_list_widget.itemClicked.connect(self.friend_item_clicked)

        self.clear_widget = QWidget()
        self.clear_widget.setMinimumWidth(400)
        self.clear_widget.setStyleSheet(
            """
            QWidget {
                background-color: #FFFFFF;
                border-radius: 30px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
            }
            """
        )

        self.main_layout.addWidget(self.tool_widget, 0, 0)
        self.main_layout.addWidget(self.message_list_widget, 0, 1)
        self.main_layout.addWidget(self.friend_list_widget, 0, 1)
        self.main_layout.addWidget(self.chatting_widget, 0, 2)
        self.main_layout.addWidget(self.clear_widget, 0, 2)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setCentralWidget(self.main_widget)

        """
            tool-widget
        """
        self.self_info_button = self.new_button('info', self.show_self_info)
        self.message_button = self.new_button('message', self.show_message)
        self.friend_button = self.new_button('friend', self.show_friend)
        self.end_button = self.new_button('end', self.close)
        self.shrink_button = self.new_button('shrink', self.showMinimized)
        self.out_button = self.new_button('out', self.login_out)

        self.tool_layout.addWidget(self.self_info_button, alignment=Qt.AlignCenter)
        self.tool_layout.addWidget(self.message_button, alignment=Qt.AlignCenter)
        self.tool_layout.addWidget(self.friend_button, alignment=Qt.AlignCenter)
        self.tool_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.tool_layout.addWidget(self.shrink_button, alignment=Qt.AlignCenter)
        self.tool_layout.addWidget(self.out_button, alignment=Qt.AlignCenter)
        self.tool_layout.addWidget(self.end_button, alignment=Qt.AlignCenter)
        self.tool_layout.setSpacing(15)

    def new_button(self, name, func):
        button = init_button(fixed_width=30, fixed_height=30, func=func)
        button.setStyleSheet(self.button_style['unselected'] % (name, name))
        return button

    def change_button_style(self, button):
        t = self.button_image_name[self.selected_button]
        self.selected_button.setStyleSheet(self.button_style['unselected'] % (t, t))
        button.setStyleSheet(self.button_style['selected'] % self.button_image_name[button])
        self.selected_button = button

    def show_self_info(self):
        self.show_user_info(user_id, username)

    def show_message(self):
        self.change_button_style(self.message_button)
        self.message_list_widget.show()
        self.friend_list_widget.hide()
        self.chatting_widget.show()
        self.clear_widget.hide()

    def show_friend(self):
        self.change_button_style(self.friend_button)
        self.friend_list_widget.show()
        self.message_list_widget.hide()
        self.chatting_widget.hide()
        self.clear_widget.show()

    def login_out(self):
        pass

    def new_message(self, msg):
        message_list.append(msg)
        msg['message'] = decode_message(msg['message'])
        add_message_to_user_to_message_dict(msg)
        self.message_list_widget.new_message((
            msg['receiver_id'],
            msg['sender_id'],
            msg['message'],
            msg['time'],
            msg['message_id'],
            msg['message_type']
        ))
        if self.chatting_widget.fr_id in [msg['receiver_id'], msg['sender_id']]:
            item = QListWidgetItem()
            widget = SingleMessageWidget().get_widget(msg['sender_id'], msg['message'], msg['message_type'])
            item.setSizeHint(widget.sizeHint())
            self.chatting_widget.message_list_widget.addItem(item)
            self.chatting_widget.message_list_widget.setItemWidget(item, widget)
            self.chatting_widget.message_list_widget.scrollToBottom()

    def new_friend(self, fr):
        friend_list[fr['fr_id']] = fr['fr_name']
        self.friend_list_widget.new_friend()
        self.message_list_widget.new_friend(fr)

    def show_user_info(self, _id, _name):
        self.user_info_widget.set_user(_id, _name)
        self.user_info_widget.show()

    def message_item_clicked(self, item):
        key_list = list(self.message_list_widget.item_widget_list.keys())
        value_list = list(self.message_list_widget.item_widget_list.values())
        fr_id = key_list[value_list.index(item)]
        self.chatting_widget.set_fr(fr_id)

    def friend_item_clicked(self, item):
        key_list = list(self.friend_list_widget.item_widget_dict.keys())
        value_list = list(self.friend_list_widget.item_widget_dict.values())
        fr_id = key_list[value_list.index(item)]
        self.show_user_info(fr_id, friend_list[fr_id])

    def close_event(self):
        self.user_info_widget.close()


class MessageListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.__init_data()
        self.__init_view()

    def __init_data(self):
        self.item_widget_list = dict()

    def __init_view(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.search_edit = QLineEdit()
        self.search_edit_action = QAction(self)
        self.search_edit_action.setIcon(QIcon('./image/search.png'))
        self.search_edit_action.triggered.connect(self.search)
        self.search_edit.addAction(self.search_edit_action, QLineEdit.LeadingPosition)
        self.search_edit.setPlaceholderText('搜索')
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setObjectName('main-search-edit')

        self.add_button = init_button(obj_name='main-add-button', func=self.add)
        self.add_button.setIcon(QIcon('./image/add.png'))

        self.message_list_widget = QListWidget()
        self.message_list_widget.setObjectName('main-info-list-widget')
        self.message_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.message_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout = QHBoxLayout()
        layout.addWidget(self.search_edit)
        layout.addWidget(self.add_button)
        self.layout.addLayout(layout)
        self.layout.addWidget(self.message_list_widget)

    def add(self):
        pass

    @staticmethod
    def search():
        f_search()

    def add_item(self, receiver_id, sender_id, message, message_time, message_type):
        item = QListWidgetItem()
        widget = MessageCardWidget(receiver_id, sender_id, message, message_time, message_type)
        item.setSizeHint(widget.sizeHint())
        self.item_widget_list[receiver_id if receiver_id != user_id else sender_id] = item
        self.message_list_widget.addItem(item)
        self.message_list_widget.setItemWidget(item, widget)

    def init_message_list_widget(self, friend, message):
        global friend_list, message_list
        friend_list = {fr['fr_id']: fr['fr_name'] for fr in friend}
        message_list = message
        for i in range(len(message_list)):
            message_list[i]['message'] = decode_message(message_list[i]['message'])
        tmp_msg_li = []

        for msg in message:
            add_message_to_user_to_message_dict(msg)
        for fr in user_to_message_dict.keys():
            user_to_message_dict[fr].sort(key=lambda k: int(k[3]), reverse=True)
            tmp_msg_li.append(user_to_message_dict[fr][0])

        tmp_msg_li = [msg for *msg, msg_id in tmp_msg_li]
        tmp_msg_li = sorted(tmp_msg_li, key=lambda k: int(k[3]), reverse=True)
        user_li = [msg[0] if msg[0] != user_id else msg[1] for msg in tmp_msg_li]
        for fr in friend:
            if fr['fr_id'] in user_li:
                continue
            tmp_msg_li.append((user_id, fr['fr_id'], '', '9999999999', '-1'))

        for msg in tmp_msg_li:
            self.add_item(*msg[:5])

    def new_message(self, msg):
        msg = list(msg)
        msg[2] = decode_message(msg[2])
        msg = tuple(msg)
        item = self.item_widget_list[msg[0] if msg[0] != user_id else msg[1]]
        widget = self.message_list_widget.itemWidget(item)
        widget.reset_message(*msg[2:4])

    def new_friend(self, fr):
        self.add_item(user_id, fr['fr_id'], '', '9999999999', '-1')

    def reset_time(self):
        for item in self.item_widget_list.values():
            widget = self.message_list_widget.itemWidget(item)
            widget.reset_time()


class MessageCardWidget(QWidget):
    def __init__(self, receiver_id, sender_id, message, message_time, message_type):
        super().__init__()

        self.setStyleSheet(message_card_style)

        fr_id = get_message_fr_id({'message_type': message_type, 'sender_id': sender_id, 'receiver_id': receiver_id})
        self.fr_name = friend_list[fr_id]
        self.self_send = sender_id == user_id
        self.message = ('我：' if self.self_send else '') + decode_message(message).replace('\n', '')
        self.message_time = int(message_time)

        tmp = self.fr_name
        while get_string_length(self.fr_name) > 10:
            self.fr_name = self.fr_name[:-1]
        self.fr_name = self.fr_name if tmp == self.fr_name else f'{self.fr_name}...'

        tmp = self.message
        while get_string_length(self.message) >= 25:
            self.message = self.message[:-1]
        self.message = self.message if tmp == self.message else f'{self.message}...'

        now = datetime.now()
        tm = datetime.fromtimestamp(self.message_time)
        date = int(mktime(now.date().timetuple()))
        tm_date = int(mktime(tm.date().timetuple()))
        if tm > now:
            self.message_time_string = '来自未来'
        elif date == tm_date:
            self.message_time_string = datetime.fromtimestamp(self.message_time).strftime('%H:%M')
        elif tm_date - date == 1:
            self.message_time_string = '昨天'
        elif tm_date - date == 6:
            self.message_time_string = datetime.fromtimestamp(self.message_time).weekday()
        else:
            self.message_time_string = datetime.fromtimestamp(self.message_time).strftime('%Y/%m/%d')

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.background_widget = QWidget()
        self.background_widget.setObjectName('background-widget')

        self.name_label = QLabel()
        self.name_label.setText(f' {self.fr_name}')
        self.name_label.setObjectName('name-label')

        self.last_message_label = QLabel()
        self.last_message_label.setText(f' {self.message}')
        self.last_message_label.setObjectName('last-message-label')

        self.last_time_label = QLabel()
        self.last_time_label.setText(f'{self.message_time_string} ')
        self.last_time_label.setObjectName('last-time-label')

        self.layout.addWidget(self.background_widget, 0, 0, 2, 3)
        self.layout.addWidget(self.name_label, 0, 0, 1, 2, Qt.AlignLeft)
        self.layout.addWidget(self.last_time_label, 0, 2, 1, 1, Qt.AlignRight)
        self.layout.addWidget(self.last_message_label, 1, 0, 1, 3, Qt.AlignLeft)

    def reset_time(self):
        now = datetime.now()
        tm = datetime.fromtimestamp(self.message_time)
        date = int(mktime(now.date().timetuple()))
        tm_date = int(mktime(tm.date().timetuple()))
        if tm > now:
            self.message_time_string = '来自未来'
        elif date == tm_date:
            self.message_time_string = datetime.fromtimestamp(self.message_time).strftime('%H:%M')
        elif tm_date - date == 1:
            self.message_time_string = '昨天'
        elif tm_date - date == 6:
            self.message_time_string = datetime.fromtimestamp(self.message_time).weekday()
        else:
            self.message_time_string = datetime.fromtimestamp(self.message_time).strftime('%Y/%m/%d')

        self.last_time_label.setText(f'{self.message_time_string} ')

    def reset_message(self, message, message_time):
        self.message = ('我：' if self.self_send else '') + decode_message(message).replace('\n', '')
        self.message_time = int(message_time)

        tmp = self.message
        while get_string_length(self.message) >= 25:
            self.message = self.message[:-1]
        self.message = self.message if tmp == self.message else f'{self.message}...'

        self.last_message_label.setText(f' {self.message}')


class FriendListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.__init_data()
        self.__init_view()

    def __init_data(self):
        self.mode = 0
        self.mode_to_text_dict = {
            0: '搜索',
            1: '搜索用户'
        }
        self.item_widget_dict = dict()

    def __init_view(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.search_edit = QLineEdit()
        self.search_edit_action = QAction(self)
        self.search_edit_action.setIcon(QIcon('./image/search.png'))
        self.search_edit_action.triggered.connect(self.search)
        self.search_edit.addAction(self.search_edit_action, QLineEdit.LeadingPosition)
        self.search_edit.setPlaceholderText(self.mode_to_text_dict[self.mode])
        self.search_edit.setObjectName('main-search-edit')
        self.search_edit.setClearButtonEnabled(True)

        self.add_button = init_button(obj_name='main-add-button', func=self.change_mode)
        self.add_button.setIcon(QIcon('./image/add_friend.png'))

        self.friend_list_widget = QListWidget()
        self.friend_list_widget.setObjectName('main-info-list-widget')
        self.friend_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.friend_list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout = QHBoxLayout()
        layout.addWidget(self.search_edit)
        layout.addWidget(self.add_button)
        self.layout.addLayout(layout)
        self.layout.addWidget(self.friend_list_widget)

    def change_mode(self):
        self.mode = 1 - self.mode
        if self.mode == 0:
            self.add_button.setIcon(QIcon('./image/add_friend.png'))
        else:
            self.add_button.setIcon(QIcon('./image/cancel.png'))
        self.search_edit.clear()
        self.search_edit.setPlaceholderText(self.mode_to_text_dict[self.mode])

    def init_friend_list_widget(self):
        def get_first_letter(nm):
            return nm[0]
        fr_list = dict()
        tmp = ''
        for fr_id, fr_nm in friend_list.items():
            fr_list.setdefault(tmp if 'a' <= (tmp := get_first_letter(fr_nm)) <= 'z' or 'A' <= tmp <= 'Z' else '#',
                               []).append((fr_id, fr_nm))
        for key in fr_list.keys():
            fr_list[key] = sorted(fr_list[key])
        for key, value in fr_list.items():
            label = QLabel(key)
            label.setStyleSheet(
                """
                QLabel {
                    font-family: "Microsoft YaHei";
                    font-size: 20px;
                    border: none;
                    color: #CCCCCC;
                }
                """
            )
            self.add_widget(label, (0, 0))

            for friend in value:
                self.add_widget(SingleFriendWidget(friend[1]), friend)
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Plain)
            line.setStyleSheet(
                """
                QFrame {
                    color: #CCCCCC;
                }
                """
            )
            self.add_widget(line, (0, 0))

    def add_widget(self, widget, friend):
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        if friend != (0, 0):
            self.item_widget_dict[friend[0]] = item
        self.friend_list_widget.addItem(item)
        self.friend_list_widget.setItemWidget(item, widget)

    def new_friend(self):
        self.item_widget_dict = dict()
        self.friend_list_widget.clear()
        self.init_friend_list_widget()

    @staticmethod
    def search():
        f_search()


class SingleFriendWidget(QWidget):
    def __init__(self, friend):
        super().__init__()
        self.setStyleSheet(single_friend_style)

        self.layout = QGridLayout()
        self.layout.setSpacing(15)
        self.setLayout(self.layout)

        self.name_label = QLabel(friend[0])
        self.name_label.setObjectName('name-label')
        self.name_label.setFixedSize(40, 40)
        self.name_label.setAlignment(Qt.AlignCenter)

        self.name_label_2 = QLabel(friend)
        self.name_label_2.setObjectName('name-label-2')
        self.name_label_2.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.name_label, 0, 0, 1, 1)
        self.layout.addWidget(self.name_label_2, 0, 1, 1, 1, Qt.AlignVCenter)
        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 2, 1, 1)


class ChattingWidget(QWidget):
    def __init__(self, fr_id):
        super().__init__()
        self.__init_data(fr_id)
        self.__init_view()

    def __init_data(self, fr_id):
        self.fr_id = fr_id

    def __init_view(self):
        self.setMinimumWidth(400)
        self.setStyleSheet(chatting_widget_style)

        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        """
            layout
        """

        self.background_widget = QWidget()
        self.background_widget.setObjectName('background-widget')
        self.layout.addWidget(self.background_widget, 0, 0)

        self.layout_two = QGridLayout()
        self.layout_two.setContentsMargins(15, 10, 10, 10)

        """
            layout-two
        """

        self.fr_name_label = QLabel()
        self.fr_name_label.setObjectName('friend-name-label')

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setObjectName('frame-line')

        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.HLine)
        self.line2.setFrameShadow(QFrame.Plain)
        self.line2.setObjectName('frame-line')

        self.message_list_widget = QListWidget()
        self.message_list_widget.setObjectName('message-list-widget')

        self.layout_three = QGridLayout()

        self.layout_two.addWidget(self.fr_name_label, 0, 0, 1, 1, Qt.AlignLeft)
        self.layout_two.addWidget(line, 1, 0, 1, 1)
        self.layout_two.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding), 2, 0, 1, 1)
        self.layout_two.addWidget(self.message_list_widget, 2, 0, 1, 1)
        self.layout_two.addWidget(self.line2, 3, 0, 1, 1)
        self.layout_two.addLayout(self.layout_three, 4, 0, 1, 1)

        """
            layout-three
        """

        self.message_edit = QPlainTextEdit()
        self.message_edit.setFixedHeight(150)
        self.message_edit.setObjectName('message-edit')

        self.send_button = init_button('发送', 'send-button', 73, 30, self.send)

        self.layout_three.addWidget(self.message_edit, 0, 0, 3, 1)
        self.layout_three.addWidget(self.send_button, 2, 0, 1, 1, Qt.AlignRight)

    def send(self):
        global message_queue
        msg = encode_message(self.message_edit.toPlainText().strip())
        self.message_edit.clear()
        message_queue = message_queue + [(msg, self.fr_id, '1')]

    def set_fr(self, fr_id):
        if not self.fr_id:
            self.layout.addLayout(self.layout_two, 0, 0)
        self.fr_id = fr_id
        self.message_edit.clear()
        self.message_list_widget.clear()
        self.fr_name_label.setText(friend_list[self.fr_id])

        if user_to_message_dict.get(self.fr_id):
            msg_li = user_to_message_dict[self.fr_id]
            for msg in msg_li[::-1]:
                item = QListWidgetItem()
                widget = SingleMessageWidget().get_widget(*msg[1:3], msg[4])
                item.setSizeHint(widget.sizeHint())
                self.message_list_widget.addItem(item)
                self.message_list_widget.setItemWidget(item, widget)
        self.message_list_widget.scrollToBottom()

        if fr_id == '-10001':
            self.line2.hide()
            self.message_edit.hide()
            self.send_button.hide()
        else:
            self.line2.show()
            self.message_edit.show()
            self.send_button.show()


class SingleMessageWidget:
    def __init__(self):
        pass

    @staticmethod
    def get_widget(sender_id, info, message_type):
        if message_type[0] == '0':
            return SingleFriendApplicationWidget(info, message_type[1] == '1')
        else:
            return SingleNormalMessageWidget(sender_id, info)


class SingleNormalMessageWidget(QWidget):
    def __init__(self, sender_id, message):
        super().__init__()
        self.setStyleSheet(single_message_style)

        self_send = sender_id == user_id
        message = '\n'.join([self.split_message(msg) for msg in message.split('\n')])

        self.layout = QGridLayout()
        self.layout.setSpacing(15)
        self.setLayout(self.layout)

        self.name_label = QLabel(friend_list[sender_id][0] if not self_send else username[0])
        self.name_label.setObjectName('name-label')
        self.name_label.setFixedSize(40, 40)
        self.name_label.setAlignment(Qt.AlignCenter)

        self.message_label = QLabel(message)
        self.message_label.setMaximumWidth(400)
        self.message_label.setContentsMargins(10, 5, 10, 5)
        self.message_label.setObjectName('self-message-label' if self_send else 'other-message-label')

        if self_send:
            self.layout.addWidget(self.name_label, 0, 2, 1, 1)
            self.layout.addWidget(self.message_label, 0, 1, 2, 1)
            self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 0, 1, 1)
        else:
            self.layout.addWidget(self.name_label, 0, 0, 1, 1)
            self.layout.addWidget(self.message_label, 0, 1, 2, 1)
            self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 2, 1, 1)

    @staticmethod
    def split_message(message):
        msg = message
        message = ''
        tmp = ''
        ind = 0
        while ind < len(msg):
            if ind:
                message += '\n'
            while get_string_length(tmp) <= 35 and ind < len(msg):
                tmp += msg[ind]
                ind += 1
            if get_string_length(tmp) > 35:
                tmp = tmp[:len(tmp) - 1]
                ind -= 1
            message += tmp
            tmp = ''
        return message


class SingleFriendApplicationWidget(QWidget):
    def __init__(self, msg, flag):
        super().__init__()
        self.setStyleSheet(single_friend_application_style)

        self.sender_id = re.search(r'[0-9]+', msg).group()

        self.layout = QGridLayout()
        self.layout.setSpacing(15)
        self.setLayout(self.layout)

        self.message_label = QLabel(msg)
        self.message_label.setContentsMargins(10, 5, 10, 5)
        self.message_label.setObjectName('message-label')

        self.accept_button = init_button(text='通过', obj_name='accept-button', fixed_width=75, func=self.accept)
        self.refuse_button = init_button(text='拒绝', obj_name='refuse-button', fixed_width=75, func=self.refuse)
        self.accept_button.setDisabled(flag)
        self.refuse_button.setDisabled(flag)

        self.layout.addWidget(self.message_label, 0, 0, 1, 3)
        self.layout.addWidget(self.accept_button, 1, 0, 1, 1)
        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 1, 1, 1, 1)
        self.layout.addWidget(self.refuse_button, 1, 2, 1, 1)

    def accept(self):
        self.set_disabled()
        f_accept(self.sender_id)

    def refuse(self):
        self.set_disabled()
        f_refuse(self.sender_id)

    def set_disabled(self):
        self.accept_button.setDisabled(True)
        self.refuse_button.setDisabled(True)


class UserInfoWidget(BaseWindow):
    def __init__(self, _id, _name):
        super().__init__()
        self.__init_data(_id, _name)
        self.__init_view()

    def __init_data(self, _id, _name):
        self.window_opacity = 1
        self.show_ignore = self.close_ignore = True

        self.id_, self.name_ = _id, _name
        self.is_friend = friend_list.get(_id)

    def __init_view(self):
        self.setStyleSheet(user_info_style)
        self.setFixedSize(400, 300)
        self.setWindowTitle(f'({self.id_}, {self.name_})')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.widget = QWidget()
        self.layout = QGridLayout()
        self.layout.setSpacing(15)
        self.widget.setLayout(self.layout)
        self.widget.setObjectName('user-info-main-widget')

        self.name_label = QLabel(self.name_[0])
        self.name_label.setObjectName('name-label')
        self.name_label.setFixedSize(75, 75)
        self.name_label.setAlignment(Qt.AlignCenter)
        # self.name_label.resize(self.name_label.width(), self.name_label.width())
        # self.name_label.resize(self.name_label.minimumHeight(), self.name_label.minimumHeight())

        self.name_label_2 = QLabel(self.name_)
        self.name_label_2.setObjectName('name-label-2')
        self.name_label_2.setAlignment(Qt.AlignCenter)

        self.id_label = QLabel(f'用户ID: {self.id_}')
        self.id_label.setObjectName('id-label')
        self.id_label.setAlignment(Qt.AlignCenter)

        self.close_button = init_button(text='关闭', obj_name='close-button', fixed_width=85, func=self.hide)
        self.action_button = init_button(text='发消息' if self.is_friend else '加好友', obj_name='action-button',
                                         fixed_width=85, func=self.action)

        self.layout.addWidget(self.name_label, 0, 0, 1, 2)
        self.layout.addWidget(self.name_label_2, 0, 2, 1, 3, Qt.AlignLeft)
        # self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 3, 1, 1)

        self.layout.addWidget(self.id_label, 1, 1, 1, 4, Qt.AlignLeft)
        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 2, 0, 2, 5)

        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 4, 0, 1, 1)
        self.layout.addWidget(self.action_button, 4, 1, 1, 1, Qt.AlignVCenter)
        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 4, 2, 1, 1)
        self.layout.addWidget(self.close_button, 4, 3, 1, 1, Qt.AlignVCenter)
        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 4, 4, 1, 1)

        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 5, 0, 2, 5)

        self.setCentralWidget(self.widget)

    def set_user(self, _id, _name):
        self.id_, self.name_ = _id, _name
        self.is_friend = friend_list.get(_id)

        self.setWindowTitle(f'({self.id_}, {self.name_})')

        self.name_label.setText(self.name_[0])
        self.name_label_2.setText(self.name_)
        self.id_label.setText(f'用户ID: {self.id_}')
        self.action_button.setText('发消息' if self.is_friend else ('修改' if _id == user_id else '加好友'))

    def action(self):
        self.hide()
        if self.is_friend:
            if not f_goto:
                return
            f_goto(self.id_)
            return
        elif self.id_ != user_id:
            if not f_add:
                return
            f_add(self.id_)
            return
        if not f_change_info:
            return
        f_change_info()
