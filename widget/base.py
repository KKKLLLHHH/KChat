from PyQt5.Qt import *


class BaseWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.window_opacity = 1

        self.show_ignore = self.close_ignore = False

        self.move_flag = False
        self.mouse_pos = QPoint(-1, -1)

        self.show_anim = None
        self.close_anim = None

        self.__init_data()
        self.__init_view()

    def __init_data(self):
        pass

    def __init_view(self):
        pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.move_flag = True
            self.mouse_pos = event.globalPos() - self.pos()
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseMoveEvent(self, event):
        if Qt.LeftButton and self.move_flag:
            self.move(event.globalPos() - self.mouse_pos)

    def mouseReleaseEvent(self, event):
        self.move_flag = False
        self.setCursor(QCursor(Qt.ArrowCursor))

    def close_event(self):
        pass

    def closeEvent(self, event):
        self.close_event()
        if self.close_ignore:
            return
        if self.close_anim is None:
            self.close_anim = QPropertyAnimation(self, b'windowOpacity')
            self.close_anim.setEndValue(0)
            self.close_anim.finished.connect(self.close)
            self.close_anim.setDuration(500)
            self.close_anim.start()

            event.ignore()

    def showEvent(self, event):
        if self.show_ignore:
            return
        if self.show_anim is None:
            self.show_anim = QPropertyAnimation(self, b'windowOpacity')
            self.show_anim.setStartValue(0)
            self.show_anim.setEndValue(self.window_opacity)
            self.show_anim.finished.connect(self.show)
            self.show_anim.setDuration(500)
            self.show_anim.start()

            event.ignore()

