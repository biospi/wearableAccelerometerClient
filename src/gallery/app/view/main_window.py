# coding: utf-8
from PyQt5.QtCore import QUrl, QSize, QTimer
from PyQt5.QtGui import QIcon, QDesktopServices, QColor
from PyQt5.QtWidgets import QApplication
from pathlib import Path

from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen)
from qfluentwidgets import FluentIcon as FIF

from .gallery_interface import GalleryInterface
# from .home_interface import HomeInterface
from .control_panel_interface import ControlPanelInterface
from .data_streaming_interface import DataStreamingInterface
from .search_connect_interface import SearchAndConnectInterface

from ..common.config import ZH_SUPPORT_URL, EN_SUPPORT_URL, cfg
from ..common.icon import Icon
from ..common.signal_bus import signalBus
from ..common.translator import Translator
from ..common import resource



class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # create sub interface
        self.connectInterface = SearchAndConnectInterface(self)
        self.controlInterface = ControlPanelInterface(self)
        self.dataInterface = DataStreamingInterface(self)
        self.dataInterface.add_control_interface(self.controlInterface)

        self.connectInterface.add_control_interface(self.controlInterface)
        self.connectInterface.add_data_interface(self.dataInterface)

        # enable acrylic effect
        self.navigationInterface.setAcrylicEnabled(True)
        self.setCustomBackgroundColor(QColor(240, 244, 249), QColor(32, 32, 32))

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.splashScreen.finish())
        self.timer.start(1000)

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.switchToSampleCard.connect(self.switchToSample)
        signalBus.supportSignal.connect(self.onSupport)

    def initNavigation(self):
        # add navigation items
        self.addSubInterface(self.connectInterface, FIF.BLUETOOTH, self.tr('Scan'))
        self.navigationInterface.addSeparator()

        pos = NavigationItemPosition.SCROLL
        self.addSubInterface(self.controlInterface, FIF.SETTING, self.tr('Setting'), pos)
        self.addSubInterface(self.dataInterface, FIF.ARROW_DOWN, self.tr('XYZ'), pos)

    def initWindow(self):
        self.resize(1200, 640)
        self.setMinimumWidth(1150)
        self.setMinimumHeight(640)
        logo_path = (Path(__file__).parent.parent /"resource" / "images" / "logo.png").as_posix()
        self.setWindowIcon(QIcon(logo_path))
        self.setWindowTitle('')

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()

    def onSupport(self):
        language = cfg.get(cfg.language).value
        if language.name() == "zh_CN":
            QDesktopServices.openUrl(QUrl(ZH_SUPPORT_URL))
        else:
            QDesktopServices.openUrl(QUrl(EN_SUPPORT_URL))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def switchToSample(self, routeKey, index):
        """ switch to sample """
        interfaces = self.findChildren(GalleryInterface)
        for w in interfaces:
            if w.objectName() == routeKey:
                self.stackedWidget.setCurrentWidget(w, False)
                w.scrollToCard(index)
