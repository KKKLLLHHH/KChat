from PyQt5.Qt import *
from widget.base import BaseWindow


class LoginWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.__init_data()
        self.__init_view()

    def __init_data(self):
        pass

    def __init_view(self):
        self.setWindowTitle('Login & Register')
        self.setFixedSize(800, 450)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        """
            main-widget
        """

        self.main_widget = QWidget(self)
        self.main_layout = QGridLayout(self)
        self.main_widget.setLayout(self.main_layout)
        self.main_widget.setObjectName('login-background-widget')

        self.splitter = QWidget()
        self.splitter.setFixedSize(400, 450)

        self.board_widget = QWidget()
        self.board_widget.setFixedSize(300, 350)
        self.board_widget.setObjectName('login-board-widget')

        self.login_widget = LoginWidget(self.login, self.change_to_register)
        self.register_widget = RegisterWidget(self.register, self.change_to_login)

        self.main_layout.addWidget(self.splitter, 0, 0)
        self.main_layout.addWidget(self.board_widget, 0, 1)
        self.main_layout.addWidget(self.login_widget, 0, 1)
        self.main_layout.addWidget(self.register_widget, 0, 1)
        self.change_to_login()
        self.setCentralWidget(self.main_widget)

        """
            menu-widget
        """

        self.close_button = QPushButton(self)
        self.close_button.setText('×')
        self.close_button.setStyleSheet('color:white;')
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.close)
        self.close_button.setObjectName('login-close-button')

    def login(self):
        pass

    def change_to_register(self):
        self.login_widget.hide()
        for item in self.login_widget.children():
            if isinstance(item, QLineEdit):
                item.clear()
        self.register_widget.show()

    def change_to_login(self):
        self.login_widget.show()
        self.register_widget.hide()
        for item in self.register_widget.children():
            if isinstance(item, QLineEdit):
                item.clear()

    def register(self):
        pass

    @staticmethod
    def show_tip(tip):
        print(tip)


class LoginWidget(QWidget):
    def __init__(self, f_login, f_register):
        super().__init__()
        self.__init_data(f_login, f_register)
        self.__init_view()

    def __init_data(self, f_login, f_register):
        self.f_login = f_login
        self.f_register = f_register

    def __init_view(self):
        self.layout = QGridLayout(self)
        self.setFixedSize(300, 350)
        self.setLayout(self.layout)

        self.login_text_label = QLabel()
        self.login_text_label.setText('登录')
        self.login_text_label.setObjectName('login-login-text-label')

        self.user_name_edit = QLineEdit()
        self.user_name_edit.setObjectName('login-login-user-name-edit')
        self.user_name_edit.setPlaceholderText('用户名/用户ID号')

        self.password_edit = QLineEdit()
        self.password_edit.setObjectName('login-login-password-edit')
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('密码')

        self.login_button = QPushButton()
        self.login_button.setText('登录')
        self.login_button.setObjectName('login-login-button')
        self.login_button.clicked.connect(self.f_login)

        self.register_button = QPushButton()
        self.register_button.setText('注册')
        self.register_button.setObjectName('login-register-button')
        self.register_button.clicked.connect(self.f_register)

        self.layout.addWidget(self.login_text_label, 0, 0, 2, 8, Qt.AlignCenter)
        self.layout.addWidget(self.user_name_edit, 2, 1, 2, 6)
        self.layout.addWidget(self.password_edit, 4, 1, 2, 6)
        self.layout.addWidget(self.login_button, 6, 1, 2, 3)
        self.layout.addWidget(self.register_button, 6, 4, 2, 3)

    def set_f_login(self, f_login):
        self.f_login = f_login
        self.login_button.clicked.connect(self.f_login)

    def set_f_register(self, f_register):
        self.f_register = f_register
        self.register_button.clicked.connect(self.f_register)

    def get_user_name(self):
        return self.user_name_edit.text()

    def get_password(self):
        return self.password_edit.text()


class RegisterWidget(QWidget):
    def __init__(self, f_submit, f_back):
        super().__init__()
        self.__init_data(f_submit, f_back)
        self.__init_view()

    def __init_data(self, f_submit, f_back):
        self.f_submit = f_submit
        self.f_back = f_back

    def __init_view(self):
        self.layout = QGridLayout(self)
        self.setFixedSize(300, 350)
        self.setLayout(self.layout)

        self.register_text_label = QLabel()
        self.register_text_label.setText('注册')
        self.register_text_label.setObjectName('login-register-text-label')

        self.user_name_edit = QLineEdit()
        self.user_name_edit.setObjectName('login-register-user-name-edit')
        self.user_name_edit.setPlaceholderText('用户名')

        self.password_edit = QLineEdit()
        self.password_edit.setObjectName('login-register-password-edit')
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('密码')

        self.password_again_edit = QLineEdit()
        self.password_again_edit.setObjectName('login-register-password-again-edit')
        self.password_again_edit.setEchoMode(QLineEdit.Password)
        self.password_again_edit.setPlaceholderText('再次输入密码')

        self.submit_button = QPushButton()
        self.submit_button.setText('注册')
        self.submit_button.setObjectName('login-submit-button')
        self.submit_button.clicked.connect(self.f_submit)

        self.back_button = QPushButton()
        self.back_button.setText('返回')
        self.back_button.setObjectName('login-back-button')
        self.back_button.clicked.connect(self.f_back)

        self.layout.addWidget(self.register_text_label, 0, 0, 2, 8, Qt.AlignCenter)
        self.layout.addWidget(self.user_name_edit, 2, 1, 2, 6)
        self.layout.addWidget(self.password_edit, 4, 1, 2, 6)
        self.layout.addWidget(self.password_again_edit, 6, 1, 2, 6)
        self.layout.addWidget(self.submit_button, 8, 1, 2, 3)
        self.layout.addWidget(self.back_button, 8, 4, 2, 3)

    def set_f_submit(self, f_submit):
        self.f_submit = f_submit
        self.submit_button.clicked.connect(self.f_submit)

    def set_f_back(self, f_back):
        self.f_back = f_back
        self.back_button.clicked.connect(self.f_back)

    def get_user_name(self):
        return self.user_name_edit.text()

    def get_password(self):
        return self.password_edit.text()

    def get_password_again(self):
        return self.password_again_edit.text()
