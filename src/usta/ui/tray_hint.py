"""A tray-anchored startup hint with an application-controlled lifetime."""

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QPainter, QPainterPath, QPalette, QPen, QPolygonF
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from usta.config import OS
from usta.i18n import _


class TrayHint(QWidget):
    def __init__(self):
        super().__init__(
            None,
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedWidth(280)
        self._arrow_top = True
        self._arrow_x = 140
        self._macos_rules = None
        if OS == "Darwin" and QGuiApplication.platformName() == "cocoa":
            from usta.ui.platform.macos.overlay import MacOSOverlayRules

            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
            self._macos_rules = MacOSOverlayRules(self)
        self.content = QVBoxLayout(self)
        self.content.setSpacing(4)
        title = QLabel("USTA")
        font = title.font()
        font.setBold(True)
        title.setFont(font)
        self.content.addWidget(title)
        self.message = QLabel(_("You can access the USTA menu here."))
        self.message.setWordWrap(True)
        self.content.addWidget(self.message)
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.setTimerType(Qt.PreciseTimer)
        self.dismiss_timer.timeout.connect(self.hide)

    def show_at(self, anchor):
        screen = QGuiApplication.screenAt(anchor.center()) or QGuiApplication.primaryScreen()
        if screen is None or anchor.isEmpty():
            return False
        available = screen.availableGeometry()
        self._arrow_top = anchor.center().y() < available.center().y()
        self.content.setContentsMargins(
            14, 22 if self._arrow_top else 14, 14, 14 if self._arrow_top else 22
        )
        self.adjustSize()
        x = max(
            available.left() + 4,
            min(anchor.center().x() - self.width() // 2, available.right() - self.width() - 3),
        )
        y = anchor.bottom() + 4 if self._arrow_top else anchor.top() - self.height() - 4
        y = max(available.top(), min(y, available.bottom() - self.height() + 1))
        self._arrow_x = max(18, min(anchor.center().x() - x, self.width() - 18))
        self.move(x, y)
        if self._macos_rules is not None:
            self._macos_rules.start()
            self._macos_rules.prepare()
        self.show()
        if self._macos_rules is not None:
            self._macos_rules.order_front_without_activation()
        self.dismiss_timer.start(10_000)
        return True

    def hideEvent(self, event):
        self.dismiss_timer.stop()
        if self._macos_rules is not None:
            self._macos_rules.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        body = QRectF(self.rect()).adjusted(
            0.5, 8.5 if self._arrow_top else 0.5, -0.5, -0.5 if self._arrow_top else -8.5
        )
        path = QPainterPath()
        path.addRoundedRect(body, 8, 8)
        edge = body.top() if self._arrow_top else body.bottom()
        tip = 0.5 if self._arrow_top else self.height() - 0.5
        path.addPolygon(
            QPolygonF(
                [
                    QPointF(self._arrow_x - 7, edge),
                    QPointF(self._arrow_x, tip),
                    QPointF(self._arrow_x + 7, edge),
                ]
            )
        )
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.palette().color(QPalette.Mid), 1))
        painter.setBrush(self.palette().color(QPalette.Window))
        painter.drawPath(path.simplified())
