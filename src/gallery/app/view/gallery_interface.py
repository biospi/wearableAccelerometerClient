# coding:utf-8
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QEvent
from PyQt5.QtGui import QDesktopServices, QPainter, QPen, QColor, QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QStackedLayout, QSizePolicy, QSpacerItem, \
    QApplication

from qfluentwidgets import (ScrollArea, PushButton, ToolButton, FluentIcon,
                            isDarkTheme, IconWidget, Theme, ToolTipFilter, TitleLabel, CaptionLabel,
                            StrongBodyLabel, BodyLabel, toggleTheme, IndeterminateProgressBar, InfoBadge,
                            FluentStyleSheet, SwitchButton, TransparentPushButton, RoundMenu, SplitPushButton, Action,
                            DropDownPushButton, SpinBox, DatePicker, ProgressBar, InfoBar, InfoBarPosition,
                            IndeterminateProgressRing)
from ..common.config import cfg, FEEDBACK_URL, HELP_URL, EXAMPLE_URL
from ..common.icon import Icon
from ..common.style_sheet import StyleSheet
from ..common.signal_bus import signalBus
from pathlib import Path

from ..global_store import GlobalStore


class SeparatorWidget(QWidget):
    """ Seperator widget """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(6, 16)

    def paintEvent(self, e):
        painter = QPainter(self)
        pen = QPen(1)
        pen.setCosmetic(True)
        c = QColor(255, 255, 255, 21) if isDarkTheme() else QColor(0, 0, 0, 15)
        pen.setColor(c)
        painter.setPen(pen)

        x = self.width() // 2
        painter.drawLine(x, 0, x, self.height())

class BatteryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.layout.setSpacing(1)  # Remove spacing between widgets
        self.label1 = QLabel("Battery")
        self.label1.setStyleSheet(f"""
            QLabel {{
            color: gray; /* Set the text color for QLabel */
            }}
        """)

        self.label2 = QLabel("100")
        self.label2.setAlignment(Qt.AlignCenter)
        self.label2.setFixedSize(30, 15)

        self.label2_layout = QHBoxLayout()
        self.label2_layout.setContentsMargins(2, 0, 0, 0)  # Move label2 5px to the right
        self.label2_layout.addWidget(self.label2)
        self.label2_layout.setAlignment(Qt.AlignLeft)

        self.layout.addWidget(self.label1)
        battery_icon_path = (Path(__file__).parent.parent / "resource" / "images" / "battery.png").as_posix()
        self.label2.setStyleSheet(f"""
        QWidget {{
            background-image: url({battery_icon_path});
            background-repeat: no-repeat;
            background-position: center;
            background-size: cover;
        }}
        QLabel {{
        color: white; /* Set the text color for QLabel */
        font-size: 9px; /* Set the font size for QLabel */
        font-weight: bold; /* Optional: set the font weight */
        }}
    """)
        self.layout.addLayout(self.label2_layout)
        self.setLayout(self.layout)
        self.setStyle(QApplication.style())


class BatteryWidget2(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 8, 0, 0)  # Remove margins
        self.layout.setSpacing(0)  # Remove spacing between widgets
        self.label1 = QLabel("98%")
        self.label1.setStyleSheet(f"""
            QLabel {{
            color: gray; /* Set the text color for QLabel */
            }}
        """)

        self.label2 = QLabel("")
        self.label2.setAlignment(Qt.AlignCenter)
        self.label2.setFixedSize(8, 16)

        self.label2_layout = QHBoxLayout()
        self.label2_layout.setContentsMargins(2, 0, 0, 0)  # Move label2 5px to the right
        self.label2_layout.addWidget(self.label2)
        self.label2_layout.setAlignment(Qt.AlignLeft)

        self.layout.addWidget(self.label1)
        battery_icon_path = (Path(__file__).parent.parent / "resource" / "images" / "empty-battery.png").as_posix()
        self.label2.setStyleSheet(f"""
        QWidget {{
            background-image: url({battery_icon_path});
            background-repeat: no-repeat;
            background-position: center;
            background-size: cover;
        }}
        QLabel {{
        color: white; /* Set the text color for QLabel */
        font-size: 9px; /* Set the font size for QLabel */
        font-weight: bold; /* Optional: set the font weight */
        }}
    """)
        self.layout.addLayout(self.label2_layout)
        self.setLayout(self.layout)

class ToolBar(QWidget):
    """ Tool bar """

    def __init__(self, title, subtitle, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = TitleLabel(title, self)
        self.subtitleLabel = CaptionLabel(subtitle, self)
        self.downloadButton = PushButton(self.tr('Download'), self, FluentIcon.DOWNLOAD)
        self.refreshButton = PushButton(self.tr('Refresh'), self, FluentIcon.UPDATE)
        self.formatButton = PushButton(self.tr('Format Storage'), self, FluentIcon.DELETE)
        self.scanButton = PushButton(self.tr('Scan'), self, FluentIcon.SEARCH_MIRROR)
        self.connectButton = PushButton(self.tr('Connect'), self, FluentIcon.CONNECT)
        self.disconnectButton = PushButton(self.tr('Disconnect'), self, FluentIcon.REMOVE)
        #self.firmwareUpdateButton = PushButton(self.tr('Firmware Update'), self, FluentIcon.SETTING)
        self.exportButton = PushButton(self.tr('Export'), self, FluentIcon.SAVE)

        #self.themeButton = ToolButton(FluentIcon.CONSTRACT, self)
        self.separator = SeparatorWidget(self)
        self.helpButton = ToolButton(FluentIcon.HELP, self)
        self.bar = IndeterminateProgressRing(self)
        self.bar.stop()

        # self.downloadBar = ProgressBar(self)
        # self.downloadBar.setVisible(True)

        self.vBoxLayout = QVBoxLayout(self)
        self.buttonLayout = QHBoxLayout()

        # self.timeMenu = RoundMenu(parent=self)
        # self.timeWindowButton = DropDownPushButton(self.tr('Time Window'), self, FluentIcon.SETTING)
        # self.timeMenu.addAction(Action(self.tr('1 Minute'), triggered=lambda c, b=self.timeWindowButton: b.setText(self.tr('1 Minute'))))
        # self.timeMenu.addAction(Action(self.tr('2 Minutes'), triggered=lambda c, b=self.timeWindowButton: b.setText(self.tr('2 Minutes'))))
        # self.timeMenu.addAction(Action(self.tr('3 Minutes'), triggered=lambda c, b=self.timeWindowButton: b.setText(self.tr('3 Minutes'))))
        # self.timeMenu.addAction(Action(self.tr('4 Minutes'), triggered=lambda c, b=self.timeWindowButton: b.setText(self.tr('4 Minutes'))))
        # self.timeMenu.addAction(Action(self.tr('5 Minutes'), triggered=lambda c, b=self.timeWindowButton: b.setText(self.tr('5 Minutes'))))
        # self.timeMenu.addAction(Action(self.tr('10 Minutes'), triggered=lambda c, b=self.timeWindowButton: b.setText(self.tr('10 Minutes'))))
        # self.timeMenu.addAction(Action(self.tr('15 Minutes'), triggered=lambda c, b=self.timeWindowButton: b.setText(self.tr('15 Minutes'))))
        # self.timeMenu.addAction(Action(self.tr('30 Minutes'),triggered=lambda c, b=self.timeWindowButton: b.setText(self.tr('30 Minutes'))))
        # self.timeMenu.addAction(Action(self.tr('60 Minutes'),triggered=lambda c, b=self.timeWindowButton: b.setText(self.tr('60 Minutes'))))
        # self.timeWindowButton.setMenu(self.timeMenu)
        # self.thresholdButton = SpinBox(self)
        # self.thresholdButton.setRange(2,999)
        # self.countWindowButton = SpinBox(self)
        # self.countWindowButton.setRange(2, 999)
        #self.countSettingsButton = TransparentPushButton(self.tr('Activity Counts Threshold and Window'), self, FluentIcon.SETTING)
        # self.dateFilterButton = TransparentPushButton(self.tr('Filter by date'), self, FluentIcon.SETTING)
        # self.datePicker = DatePicker(self)
        #self.hwidButton = TransparentPushButton(self.tr(''), self, None)
        self.__initWidget()

    def __initWidget(self):
        self.setFixedHeight(170)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(36, 22, 36, 12)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addSpacing(22)
        self.vBoxLayout.addLayout(self.buttonLayout, 1)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addWidget(self.bar)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        #self.vBoxLayout.addSpacing(4)
        # self.vBoxLayout.addWidget(self.downloadBar)
        # self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.buttonLayout.setSpacing(4)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.addWidget(self.scanButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.connectButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.disconnectButton, 0, Qt.AlignLeft)
        #self.buttonLayout.addWidget(self.firmwareUpdateButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.exportButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.downloadButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.refreshButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.formatButton, 0, Qt.AlignLeft)
        # self.buttonLayout.addWidget(self.timeWindowButton, 0, Qt.AlignLeft)
        #self.buttonLayout.addWidget(self.countSettingsButton, 0, Qt.AlignLeft)
        # self.buttonLayout.addWidget(self.dateFilterButton, 0, Qt.AlignLeft)
        # self.buttonLayout.addWidget(self.datePicker, 0, Qt.AlignLeft)
        # self.buttonLayout.addWidget(self.thresholdButton, 0, Qt.AlignLeft)
        # self.buttonLayout.addWidget(self.countWindowButton, 0, Qt.AlignLeft)
        # self.buttonLayout.addStretch(1)
        # self.buttonLayout.addWidget(self.themeButton, 0, Qt.AlignRight)
        #self.buttonLayout.addWidget(self.hwidButton, 0, Qt.AlignRight)
        self.buttonLayout.addWidget(self.helpButton, 0, Qt.AlignRight)

        #self.buttonLayout.addWidget(self.separator, 0, Qt.AlignRight)

        #self.batteryWidget = BatteryWidget2()

        self.updateBatteryLevel()
        self.buttonLayout.addWidget(self.batteryWidget, 0, Qt.AlignTop)
        if self.batteryWidget is not None:
            self.batteryWidget.setVisible(False)

        self.separator.setVisible(False)
        self.buttonLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # self.themeButton.installEventFilter(ToolTipFilter(self.themeButton))
        self.helpButton.installEventFilter(ToolTipFilter(self.helpButton))

        # self.themeButton.setToolTip(self.tr('Dark/Light Mode'))
        self.helpButton.setToolTip(self.tr('Device info'))
        self.subtitleLabel.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))

        # self.themeButton.clicked.connect(self.clicked_theme_button)


    def updateBatteryLevel(self, isVisible=True):
        print("updateBatteryLevel...")
        battery_level = GlobalStore().battlvl

        # print(f"updateBatteryLevel {isDarkTheme()}...")
        bat_svg_theme = "white"
        if not isDarkTheme():
            bat_svg_theme = "black"

        if battery_level is not None:
            battery_path = (Path(__file__).parent.parent / "resource" / "images" / "battery.png").as_posix()
        print(battery_path)

        if hasattr(self, 'batteryWidget'):
            self.buttonLayout.removeWidget(self.batteryWidget)
            self.batteryWidget.deleteLater()  # Delete the widget to free resources
            # self.batteryWidget = None  # Clear the reference
        self.batteryWidget = TransparentPushButton(QIcon(battery_path), f'{battery_level}%', self)
        self.buttonLayout.addWidget(self.batteryWidget, 0, Qt.AlignTop)

    def clicked_theme_button(self):
        print("clicked_theme_button")
        toggleTheme(True)
        self.updateBatteryLevel()


class ExampleCard(QWidget):
    """ Example card """

    def __init__(self, title, widgets: list[QWidget], sourcePath, stretch=0, parent=None, fig=False, xmargin=25, spacing=12):
        super().__init__(parent=parent)
        self.widgets = widgets
        self.stretch = stretch
        self.titleLabel = StrongBodyLabel(title, self)
        self.card = QFrame(self)
        self.xmargin = xmargin
        self.spacing = spacing
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = QVBoxLayout(self.card)
        self.topLayout = QHBoxLayout()
        self.fig = fig
        if fig:
            self.topLayout = QVBoxLayout()
        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()
        self.card.setObjectName('card')

    def __initLayout(self):
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.cardLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.topLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        if self.fig:
            self.topLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.vBoxLayout.setSpacing(self.spacing)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.setContentsMargins(12, 12, 12, 12)
        #self.bottomLayout.setContentsMargins(18, 18, 18, 18)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)

        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignTop)
        if self.fig:
            self.vBoxLayout.addWidget(self.card, 1)
        else:
            self.vBoxLayout.addWidget(self.card, 0, Qt.AlignTop)

        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.cardLayout.setSpacing(0)
        self.cardLayout.setAlignment(Qt.AlignTop)
        self.cardLayout.addLayout(self.topLayout, 0)

        for widget in self.widgets:
            widget.setParent(self.card)
            widget.setContentsMargins(0, 0, self.xmargin, 0)
            self.topLayout.addWidget(widget)
        if self.stretch == 0:
            self.topLayout.addStretch(1)

        for widget in self.widgets:
            widget.show()


class GalleryInterface(ScrollArea):
    """ Gallery interface """

    def __init__(self, title: str, subtitle: str, parent=None):
        """
        Parameters
        ----------
        title: str
            The title of gallery

        subtitle: str
            The subtitle of gallery

        parent: QWidget
            parent widget
        """
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.toolBar = ToolBar(title, subtitle, self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, self.toolBar.height(), 0, 0)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)

        self.view.setObjectName('view')
        StyleSheet.GALLERY_INTERFACE.apply(self)
        self.disconnected = False

    def addExampleCard(self, title, widgets, sourcePath: str = '', stretch=0, fig=False, xmargin=25, alignCenter=False, spacing=12):
        card = ExampleCard(title, widgets, sourcePath, stretch, self.view, fig=fig, xmargin=xmargin, spacing=spacing)
        self.vBoxLayout.addWidget(card, 0, Qt.AlignTop)
        if alignCenter:
            self.vBoxLayout.addWidget(card, 0, Qt.AlignHCenter)
        else:
            self.vBoxLayout.addWidget(card, 0, Qt.AlignTop)

        return card

    def addCards(self, title1, tittle2, widget1, widget2, sourcePath: str = '', stretch=0):
        card1 = ExampleCard(title1, widget1, sourcePath, stretch, self.view)
        card2 = ExampleCard(tittle2, widget2, sourcePath, stretch, self.view)
        hBoxLayout = QHBoxLayout(self.view)
        hBoxLayout.setSpacing(30)
        hBoxLayout.setAlignment(Qt.AlignTop)
        #hBoxLayout.setContentsMargins(36, 20, 36, 36)
        hBoxLayout.addWidget(card1)
        hBoxLayout.addWidget(card2)
        self.vBoxLayout.addLayout(hBoxLayout)
        return card1, card2

    def scrollToCard(self, index: int):
        """ scroll to example card """
        w = self.vBoxLayout.itemAt(index).widget()
        self.verticalScrollBar().setValue(w.y())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.toolBar.resize(self.width(), self.toolBar.height())

    def showDisconnectWarning(self):
        print(f"showDisconnectWarning...")
        InfoBar.warning(
            title=self.tr('Device disconnected'),
            content=self.tr(f"The bluetooth connection was interrupted by the device"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=10000,
            parent=self.parent()
        )
        self.toolBar.batteryWidget.setVisible(False)
        self.toolBar.helpButton.setVisible(False)