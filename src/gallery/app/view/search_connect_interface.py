# coding:utf-8
import time
from typing import List

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QUrl
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QLabel, QWidget, QHBoxLayout, QFileDialog, QMessageBox
from dateutil.relativedelta import relativedelta

from qfluentwidgets import (FluentIcon, IconWidget, FlowLayout, isDarkTheme,
                            Theme, SmoothScrollArea, SearchLineEdit, Dialog, MessageBox, InfoBar, InfoBarPosition,
                            ColorDialog, Action, TitleLabel, TeachingTip, InfoBarIcon, TeachingTipTailPosition,
                            SubtitleLabel, MessageBoxBase, BodyLabel)

from .gallery_interface import GalleryInterface
# from .home_interface import BannerWidget

from ..common.translator import Translator
from ..common.config import cfg
from ..common.style_sheet import StyleSheet
from ..common.trie import Trie

import asyncio
from dataclasses import dataclass
from functools import cached_property
import sys
from pathlib import Path

import qasync

from bleak import BleakScanner, BleakClient, BleakError
from bleak.backends.device import BLEDevice
from ..ble.ble_client import QBleakClient
from datetime import datetime
from PIL import ImageColor

from ..global_store import GlobalStore


class LineEdit(SearchLineEdit):
    """ Search line edit """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(self.tr(''))
        self.setFixedWidth(304)
        self.textChanged.connect(self.search)


class IconCard(QFrame):
    """ Icon card """

    clicked = pyqtSignal(FluentIcon)

    def __init__(self, icon: FluentIcon, parent=None, device=None):
        super().__init__(parent=parent)
        self.icon = icon
        self.device = device
        self.isSelected = False

        self.iconWidget = IconWidget(FluentIcon.BLUETOOTH, self)
        self.nameLabel = QLabel(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.setFixedSize(96, 96)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(8, 28, 8, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.iconWidget.setFixedSize(28, 28)
        self.vBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignHCenter)
        self.vBoxLayout.addSpacing(14)
        self.vBoxLayout.addWidget(self.nameLabel, 0, Qt.AlignHCenter)

        text = self.nameLabel.fontMetrics().elidedText(icon.value, Qt.ElideRight, 90)
        self.nameLabel.setText(device.name[0:10])

    def mouseReleaseEvent(self, e):
        if self.isSelected:
            return

        self.clicked.emit(self.icon)

    def setSelected(self, isSelected: bool, force=False):
        if isSelected == self.isSelected and not force:
            return

        self.isSelected = isSelected

        if not isSelected:
            self.iconWidget.setIcon(FluentIcon.BLUETOOTH)
        else:
            icon = FluentIcon.BLUETOOTH.icon(Theme.LIGHT if isDarkTheme() else Theme.DARK)

            self.iconWidget.setIcon(icon)

        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())


class IconInfoPanel(QFrame):
    """ Icon info panel """

    def __init__(self, icon: FluentIcon, parent=None, device=None):
        super().__init__(parent=parent)
        self.nameLabel = QLabel("", self)
        self.iconWidget = IconWidget(icon, self)
        self.iconNameTitleLabel = QLabel(self.tr(''), self)
        self.enumNameTitleLabel = QLabel(self.tr('No device detected'), self)
        self.enumNameLabel = QLabel("Click 'Scan'...", self)

        if device is not None:
            self.iconNameTitleLabel = QLabel(self.tr(''), self)
            self.enumNameTitleLabel = QLabel(self.tr(''), self)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(16, 20, 16, 20)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.vBoxLayout.addWidget(self.nameLabel)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addWidget(self.iconWidget)
        self.vBoxLayout.addSpacing(45)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addSpacing(34)
        self.vBoxLayout.addWidget(self.enumNameTitleLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.enumNameLabel)

        self.iconWidget.setFixedSize(48, 48)
        self.setFixedWidth(216)

        self.nameLabel.setObjectName('nameLabel')
        self.iconNameTitleLabel.setObjectName('subTitleLabel')
        self.enumNameTitleLabel.setObjectName('subTitleLabel')

    def setIcon(self, icon: FluentIcon, device:BLEDevice):

        self.iconWidget.setIcon(FluentIcon.BLUETOOTH)
        self.nameLabel.setText("")
        #self.iconNameLabel.setText(device.name)
        print(device.name)
        self.enumNameLabel.setText(device.address)
        self.iconNameTitleLabel.setText('Name')
        self.enumNameTitleLabel.setText('Address')


class IconCardView(QWidget):
    """ Icon card view """

    def __init__(self, parent=None, toolBar=None):
        super().__init__(parent=parent)
        self.toolBar = toolBar
        self.trie = Trie()
        self.searchLineEdit = LineEdit(self)

        self.view = QFrame(self)
        self.scrollArea = SmoothScrollArea(self.view)
        self.scrollWidget = QWidget(self.scrollArea)
        self.infoPanel = IconInfoPanel(FluentIcon.INFO, self)

        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout(self.view)
        self.flowLayout = FlowLayout(self.scrollWidget, isTight=True)

        self.cards = []     # type:List[IconCard]
        self.icons = []
        self.devices = []
        self.currentIndex = -1

        self.__initWidget()

    def __initWidget(self):
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setViewportMargins(0, 5, 0, 5)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.searchLineEdit)
        self.vBoxLayout.addWidget(self.view)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.scrollArea)
        self.hBoxLayout.addWidget(self.infoPanel, 0, Qt.AlignRight)

        self.flowLayout.setVerticalSpacing(8)
        self.flowLayout.setHorizontalSpacing(8)
        self.flowLayout.setContentsMargins(8, 3, 8, 8)

        self.__setQss()
        cfg.themeChanged.connect(self.__setQss)
        self.searchLineEdit.clearSignal.connect(self.showAllIcons)
        self.searchLineEdit.searchSignal.connect(self.search)

    def addIcon(self, icon: FluentIcon, device: BLEDevice):
        """ add icon to view """
        card = IconCard(icon, self, device=device)
        card.clicked.connect(self.setSelectedIcon)

        self.trie.insert(icon.value, len(self.cards))
        self.cards.append(card)
        self.icons.append(icon)
        self.devices.append(device)
        self.flowLayout.addWidget(card)
    def setSelectedIcon(self, icon: FluentIcon, selected: bool=True):
        """ set selected icon """
        index = self.icons.index(icon)
        self.currentDevice = self.devices[index]
        print(f"Clicked {self.currentDevice}")
        if self.currentIndex >= 0:
            self.cards[self.currentIndex].setSelected(False)
        self.currentIndex = index
        self.cards[index].setSelected(selected)
        self.infoPanel.setIcon(icon, self.currentDevice)
        self.toolBar.connectButton.setEnabled(True)
        self.toolBar.disconnectButton.setEnabled(False)
        #self.toolBar.firmwareUpdateButton.setEnabled(False)

    def __setQss(self):
        self.view.setObjectName('iconView')
        self.scrollWidget.setObjectName('scrollWidget')

        StyleSheet.ICON_INTERFACE.apply(self)
        StyleSheet.ICON_INTERFACE.apply(self.scrollWidget)

        if self.currentIndex >= 0:
            self.cards[self.currentIndex].setSelected(True, True)

    def search(self, keyWord: str):
        """ search icons """
        items = self.trie.items(keyWord.lower())
        indexes = {i[1] for i in items}
        self.flowLayout.removeAllWidgets()

        for i, card in enumerate(self.cards):
            isVisible = i in indexes
            card.setVisible(isVisible)
            if isVisible:
                self.flowLayout.addWidget(card)

    def showAllIcons(self):
        self.flowLayout.removeAllWidgets()
        for card in self.cards:
            card.show()
            self.flowLayout.addWidget(card)


class SearchAndConnectInterface(GalleryInterface):
    """ Search and connect interface """

    def connect(self):
        self.toolBar.connectButton.setEnabled(False)
        self.toolBar.bar.start()
        print("Clicked connect")
        selected_device = "xxx"
        print(f"connected to {selected_device}")

    def disconnect(self):
        self.toolBar.bar.stop()
        self.iconView.setSelectedIcon(self.iconView.icons[0], selected=False)
        print("Clicked disconnect")

    def help(self):
        print("Clicked help")
        print(self.info_string)
        TeachingTip.create(
            target=self.toolBar.helpButton,
            icon=InfoBarIcon.INFORMATION,
            title='Device Information',
            content=self.info_string,
            isClosable=True,
            tailPosition=TeachingTipTailPosition.TOP,
            duration=1000*60,
            parent=self
        )

    def showDialog(self):
        self.toolBar.connectButton.setEnabled(True)
        device = self.iconView.currentDevice
        title = self.tr('Connection failed')
        content = self.tr(f"{device.name} is not compatible or not available. Would you like to try again ?")
        w = MessageBox(title, content, self.window())
        w.setContentCopyable(True)
        if w.exec():
            print('Yes button is pressed.')
            self.handle_scan()
        else:
            print('Cancel button is pressed')


    @cached_property
    def devices(self):
        return list()

    @property
    def curr_client(self):
        return self._client

    async def build_client(self, device):
        if self._client is not None:
            await self._client.stop()
        self._client = QBleakClient(device)
        self._client.messageChanged.connect(self.handle_message_changed)
        self._client.messageDiconnect.connect(self.handle_message_disconnect)
        await self._client.start()

    async def disconnect_client(self):
        if self._client is not None:
            await self._client.stop()

    async def update_timestamp(self):
        print("Update Timestamp...")
        now = datetime.now()
        #now = now + relativedelta(months=-1)
        datetime_string = now.strftime("%y %m %d %H %M %S")
        print(datetime_string)
        await self.handle_send(datetime_string)

    async def request_batt_level(self):
        print("Request batt level...")
        msg = f"batt_level"
        await self.handle_send(msg)


    async def update_led(self, status, rgb_color):
        print("Update led...")
        stat = 'on' if status else 'off'
        msg = f"led_{stat}"
        if rgb_color is not None:
            msg = f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}"
        await self.handle_send(msg)


    async def update_flip(self, value):
        print("Update flip...")
        msg = f"flip_{value}"
        await self.handle_send(msg)

    async def update_activity_count_out(self, status):
        print("Update activity count output...")
        stat = 'on' if status else 'off'
        msg = f"actcount_{stat}"
        await self.handle_send(msg)


    async def update_song(self, song):
        print("Update song...")
        await self.handle_send(song)

    async def update_acc_setting(self, value):
        print("Update acc setting...")
        await self.handle_send(value)

    @qasync.asyncSlot()
    async def handle_ble_batt(self):
        self.toolBar.bar.start()
        await self.request_batt_lev()
        self.toolBar.bar.stop()

    @qasync.asyncSlot()
    async def handle_ble_led(self, status, rgb_color=None):
        self.toolBar.bar.start()
        await self.update_led(status, rgb_color)
        self.toolBar.bar.stop()

    @qasync.asyncSlot()
    async def handle_ble_flip(self, value):
        self.toolBar.bar.start()
        await self.update_flip(value)
        self.toolBar.bar.stop()

    @qasync.asyncSlot()
    async def handle_ble_activity(self, status):
        self.toolBar.bar.start()
        await self.update_activity_count_out(status)
        self.toolBar.bar.stop()


    @qasync.asyncSlot()
    async def handle_ble_audio(self, song):
        self.toolBar.bar.start()
        await self.update_song(song)
        self.toolBar.bar.stop()

    @qasync.asyncSlot()
    async def handle_acc_settings(self, value):
        await self.update_acc_setting(value)
        # title = self.tr('Accelerometer configuration')
        # content = self.tr(f"Setting Accelerometer configuration.\nDo you wish to continue?")
        # w = MessageBox(title, content, self.window())
        # w.setContentCopyable(True)
        # if w.exec():
        #     self.toolBar.bar.start()
        #     await self.update_acc_setting(value)
        #     self.toolBar.bar.stop()
        #     if self.current_client is not None:
        #         self.config_success()
        #
        # else:
        #     print('Cancel button is pressed')

    @qasync.asyncSlot()
    async def handle_connect(self):
        self.toolBar.bar.start()
        self.toolBar.connectButton.setEnabled(False)
        if not hasattr(self.iconView, 'currentDevice'):
            return
        device = self.iconView.currentDevice
        print("handle_connect", device)
        if device is None:
            self.toolBar.bar.stop()
            return
        if isinstance(device, BLEDevice):
            try:
                await self.build_client(device)
                print("connected")
                self.toolBar.disconnectButton.setEnabled(True)
                #self.toolBar.firmwareUpdateButton.setEnabled(True)
                if self.toolBar.batteryWidget is not None:
                    self.toolBar.batteryWidget.setVisible(True)
                    self.toolBar.helpButton.setVisible(True)

                #self.toolBar.separator.setVisible(True)

                await self.update_timestamp()
                # InfoBar.success(
                #     title=self.tr('Connected'),
                #     content=self.tr(f"You connected to {device.name} successfully."),
                #     orient=Qt.Horizontal,
                #     isClosable=True,
                #     position=InfoBarPosition.BOTTOM,
                #     duration=2000,  # won't disappear automatically
                #     parent=self
                # )
                self.disconnected = False
                # await self.request_batt_level()

            except Exception as e:
                self.toolBar.bar.stop()
                print(e)
                self.showDialog()
            self.toolBar.bar.stop()

    async def timer_task(self, seconds):
        await asyncio.sleep(seconds)

    # async def battery_monitoring_task(self):
    #     wait_event = asyncio.Event()
    #     while True:
    #         await wait_event.wait(60)  # Non-blocking wait with timeout
    #         await self.request_batt_level()
    #     # while True:
    #     #     #await asyncio.sleep(60)
    #     #     time.sleep(60)
    #     #     await self.request_batt_level()
    #     #     # if self.current_client is None:
    #     #     #     break
    #     #     # if not self.current_client.is_connected():
    #     #     #     break

    @qasync.asyncSlot()
    async def handle_disconnect(self):
        self.toolBar.bar.start()
        self.toolBar.connectButton.setEnabled(False)
        self.toolBar.disconnectButton.setEnabled(False)
        #self.toolBar.firmwareUpdateButton.setEnabled(False)
        device = self.iconView.currentDevice
        print(f"async handle_disconnect device={device}")
        await self.disconnect_client()
        self.toolBar.connectButton.setEnabled(True)
        if self.toolBar.batteryWidget is not None:
            self.toolBar.batteryWidget.setVisible(False)
            self.toolBar.helpButton.setVisible(False)
        self.toolBar.separator.setVisible(False)
        #self.toolBar.hwidButton.setVisible(False)
        self.toolBar.downloadButton.setVisible(False)
        self.toolBar.refreshButton.setVisible(False)
        self.toolBar.formatButton.setVisible(False)

        self.devices.clear()
        self.iconView.flowLayout.removeAllWidgets()
        self.iconView.icons.clear()
        self.iconView.cards = []
        self.iconView.icons = []
        self.iconView.devices = []
        self.iconView.currentIndex = -1


    @qasync.asyncSlot()
    async def handle_scan(self):
        print("handle_scan...")
        if hasattr(self, 'iconView'):
            self.vBoxLayout.removeWidget(self.iconView)
        self.iconView = IconCardView(self, toolBar=self.toolBar)
        if self.toolBar.batteryWidget is not None:
            self.toolBar.batteryWidget.setVisible(False)
        self.toolBar.bar.start()
        self.toolBar.scanButton.setEnabled(False)
        self.devices.clear()
        try:
            devices = await BleakScanner.discover()
        except Exception as e:
            print(e)
            self.toolBar.bar.stop()
            title = self.tr('Bluetooth Error')
            content = self.tr(f"It seems that bluetooth is not enabled on your computer. Please enable Bluetooth and retry.")
            w = MessageBox(title, content, self.window())
            w.setContentCopyable(True)
            if w.exec():
                print("ok button is pressed")
            else:
                print('Cancel button is pressed')
        print(devices)
        self.devices.extend(devices)
        print(self.devices)
        self.iconView.flowLayout.removeAllWidgets()
        self.iconView.icons.clear()
        # self.iconView.trie.children.clear()
        self.iconView.cards = []
        self.iconView.icons = []
        self.iconView.devices = []
        self.iconView.currentIndex = -1

        for i, device in enumerate(self.devices):
            if device.name is None:
                continue
            print(f"ID:{i} NAME:{device.name} DEVICE:{device}")
            icon = list(FluentIcon._member_map_.values())[i]
            self.iconView.addIcon(icon, device)

        if len(self.iconView.icons) == 0:
            self.toolBar.bar.stop()
            self.toolBar.scanButton.setEnabled(True)
            self.devices.clear()
            self.iconView.flowLayout.removeAllWidgets()
            self.iconView.icons.clear()
            self.iconView.cards = []
            self.iconView.icons = []
            self.iconView.devices = []
            self.iconView.currentIndex = -1
            return

        if len(self.iconView.icons) > 0:
            self.iconView.setSelectedIcon(self.iconView.icons[0])
        print("Finish scanner")
        self.toolBar.bar.stop()
        # if not self.layout_initialised:
        #     self.layout_initialised = True
        self.vBoxLayout.addWidget(self.iconView)
        self.toolBar.scanButton.setEnabled(True)

    def handle_message_disconnect(self, message):
        print(f"disconnect msg->{message}")
        if hasattr(self, 'iconView'):
            self.vBoxLayout.removeWidget(self.iconView)
        self.toolBar.bar.stop()
        self.toolBar.disconnectButton.setEnabled(False)
        #self.toolBar.firmwareUpdateButton.setEnabled(False)
        self.toolBar.connectButton.setEnabled(False)
        # InfoBar.warning(
        #     title=self.tr('Device disconnected'),
        #     content=self.tr(f"The bluetooth connection was interrupted by the device"),
        #     orient=Qt.Horizontal,
        #     isClosable=True,
        #     position=InfoBarPosition.BOTTOM,
        #     duration=10000,
        #     parent=self.parent()
        # )
        # self.dataInterface.showDisconnectWarning()
        self.showDisconnectWarning()
        self.disconnected = True
        for c in self.iconView.cards:
            c.setVisible(False)

    def handle_message_changed(self, message):
        self.dataInterface.incoming_data = True
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(1000)

        msg = message.decode()
        print(f"Decoded data incoming msg:{message}")


        if "batt" in msg:
            split = msg.split('_')[1].split(':')
            print(f"split={split}")
            batt_lvl = int(split[0])
            # batt_mV = int(split[1])
            # soc_temp = int(split[2])
            datetime_string = datetime.now().strftime("%y-%m-%dT%H:%M:%S")
            print(f"batt_lvl={batt_lvl} timestamp={datetime_string}")

            # with batt_log_file.open('a') as file:
            #     log_message = f"{datetime_string},{batt_lvl},{batt_mV},{soc_temp}\n"
            #     file.write(log_message)

            self.battlvl = batt_lvl
            GlobalStore().battlvl = self.battlvl
            self.toolBar.updateBatteryLevel()

        if "info" in msg:
            data = msg.replace("info", '')
            split = data.split(' ')
            hwid = split[0]
            self.xyz_sens = split[1]
            self.xyz_sampling = split[2]
            self.xyz_count = split[3]
            self.flip_count = split[4]
            self.msd_size = int(split[5])
            self.msd_freemem = int(split[6])
            self.battlvl = int(split[7])
            GlobalStore().battlvl = self.battlvl
            self.toolBar.updateBatteryLevel()

            if self.toolBar.batteryWidget is not None:
                self.toolBar.batteryWidget.setVisible(True)

            self.sd_used_space = (self.msd_size - self.msd_freemem) / 1000
            print(f"Acc conf: {split} xyz_sens: {self.xyz_sens} xyz_sampling: {self.xyz_sampling} "
                  f" xyz_count: {self.xyz_count} flip_count: {self.flip_count}"
                  f"sd_card_size: {self.msd_size} sd_freemem: {self.msd_freemem} sd_used_space: {self.sd_used_space} "
                  f"batt_level: {self.battlvl}")

            self.controlInterface.accSamplingButton.setText(f"{self.xyz_sampling}Hz")
            self.controlInterface.accSensitivityButton.setText(f"{self.xyz_sens}G")
            self.controlInterface.activitySwitchButton.setChecked(bool(int(self.xyz_count)))
            self.controlInterface.bleFlipBox.setValue(int(self.flip_count))

            # id, version_string = hwid.split(' ')
            # parts = version_string.split('.')
            self.info_string = f"Free space: {int(self.msd_freemem / 1000)}GB"
            self.dataInterface.hwid = hwid

        if 14 <= len(msg) <= 38 and 'hwid' not in msg and 'batt' not in msg:#todo clean up
            print(f"MSG={msg}")
            self.dataInterface.incoming_data = True
            self.dataInterface.first_packet_received = True
            self.dataInterface.ble_data.append(self.dataInterface.parse_ble_data(msg))

        if msg == -9 or msg == "-9":
            InfoBar.warning(
                title=self.tr('Device disconnected'),
                content=self.tr(f"The bluetooth connection was interrupted by the device"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=3000,  # won't disappear automatically
                parent=self.parent()
            )
            self.toolBar.batteryWidget.setVisible(False)
            self.toolBar.helpButton.setVisible(False)
            self.disconnected = True

    @qasync.asyncSlot()
    async def handle_send(self, message):
        print(f"msg->{message}")
        if self.curr_client is None:
            InfoBar.error(
                title=self.tr('No device!'),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=3000,
                parent=self.parent()
            )
            return
        #message = self.message_lineedit.text()
        if message:
            await self.curr_client.write(message.encode())

    def reset_incoming_data(self):
        self.dataInterface.incoming_data = False

    def __init__(self, parent=None):
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.reset_incoming_data)

        self.timer_files = QTimer()
        self.timer_files.setInterval(1000)
        self.timer_files.setSingleShot(True)

        self.timer_raw_data = QTimer()
        self.timer_raw_data.setInterval(1000)
        self.timer_raw_data.setSingleShot(True)

        t = Translator()
        super().__init__(
            title="Scan",
            subtitle="Ensure your device is powered on and set to discoverable mode. Tap 'Scan' and choose a device from the list below to connect.",
            parent=parent
        )
        self.setObjectName('iconInterface')
        #self.banner = BannerWidget(self)
        self.iconView = IconCardView(self)
        self.vBoxLayout.addWidget(self.iconView)
        self.layout_initialised = False
        self.toolBar.connectButton.setEnabled(False)
        self.toolBar.disconnectButton.setEnabled(False)
        self.toolBar.exportButton.setVisible(False)
        self.toolBar.helpButton.setVisible(False)
        self.toolBar.batteryWidget.setVisible(False)
        self.toolBar.downloadButton.setVisible(False)
        self.toolBar.refreshButton.setVisible(False)
        self.toolBar.formatButton.setVisible(False)
        self.toolBar.batteryWidget.setVisible(False)
        self.toolBar.scanButton.clicked.connect(self.handle_scan)
        self.toolBar.connectButton.clicked.connect(self.handle_connect)
        self.toolBar.disconnectButton.clicked.connect(self.handle_disconnect)
        self.toolBar.helpButton.clicked.connect(self.help)

        self._client = None
        self.xyz_sampling = 25
        self.xyz_sens = "1.2"
        self.xyz_count = 0
        self.flip_count = 1
        self.msd_size = 0
        self.msd_freemem = 0
        self.battlvl = -1

        self.vBoxLayout.setContentsMargins(36, 22, 36, 36)
        self.vBoxLayout.setSpacing(40)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
    def add_data_interface(self, interface):
        self.dataInterface = interface


    def add_control_interface(self, interface):
        self.controlInterface = interface
        self.controlInterface.switchButton.checkedChanged.connect(self.handle_led_on)
        self.controlInterface.activitySwitchButton.checkedChanged.connect(self.handle_activity_on)
        self.controlInterface.colorButton.clicked.connect(self.showColorDialog)
        self.controlInterface.playMusicMenu.addAction(Action(FluentIcon.PLAY, self.tr('Beep'), triggered=lambda: self.handle_audio_play('Beep')))
        self.controlInterface.stopAudioButton.clicked.connect(self.handle_audio_stop)

        self.controlInterface.accSensitivityMenu.addActions([
            Action(self.tr('8G'), triggered=lambda: self.handle_acc_sensitivity('8G')),
            Action(self.tr('6G'), triggered=lambda: self.handle_acc_sensitivity('6G')),
            Action(self.tr("4G"), triggered=lambda: self.handle_acc_sensitivity('4G')),
            Action(self.tr("2G"), triggered=lambda: self.handle_acc_sensitivity('2G')),
            Action(self.tr("1.5G"), triggered=lambda: self.handle_acc_sensitivity('1.5G')),
            Action(self.tr("1.4G"), triggered=lambda: self.handle_acc_sensitivity('1.4G')),
            Action(self.tr("1.3G"), triggered=lambda: self.handle_acc_sensitivity('1.3G')),
            Action(self.tr("1.2G"), triggered=lambda: self.handle_acc_sensitivity('1.2G')),
            Action(self.tr("1.17G"), triggered=lambda: self.handle_acc_sensitivity('1.17G')),
            Action(self.tr("1.15G"), triggered=lambda: self.handle_acc_sensitivity('1.15G')),
            Action(self.tr("1.12G"), triggered=lambda: self.handle_acc_sensitivity('1.12G')),
            Action(self.tr("1.1G"), triggered=lambda: self.handle_acc_sensitivity('1.1G'))
        ])

        self.controlInterface.accSamplingMenu.addActions([
            #Action(self.tr('100Hz'), triggered=lambda: self.handle_acc_sampling('100Hz')),
            Action(self.tr('30Hz'), triggered=lambda: self.handle_acc_sampling('30Hz')),
            Action(self.tr('25Hz'), triggered=lambda: self.handle_acc_sampling('25Hz')),
            Action(self.tr('20Hz'), triggered=lambda: self.handle_acc_sampling('20Hz')),
            Action(self.tr('15Hz'), triggered=lambda: self.handle_acc_sampling('15Hz')),
            Action(self.tr('10Hz'), triggered=lambda: self.handle_acc_sampling('10Hz')),
            Action(self.tr('5Hz'), triggered=lambda: self.handle_acc_sampling('5Hz')),
            Action(self.tr("1Hz"), triggered=lambda: self.handle_acc_sampling('1Hz'))
        ])
        self.controlInterface.bleFlipBox.valueChanged.connect(self.handle_flip_box)

    def handle_acc_sampling(self, text):
        print(f"handle_acc_sampling text={text}")
        self.controlInterface.accSamplingButton.setText(self.tr(text))
        self.xyz_sampling = text[:-2]
        print(f"sampling={self.xyz_sampling}")
        print(f"sensitivity={self.xyz_sens}")
        s2 = 0
        split = self.xyz_sens.split('.')
        s1 = int(split[0])
        if len(split) == 2:
            s2 = int(split[1])
        self.handle_acc_settings(f"{self.xyz_sampling} {s1} {s2} {0}")
        self.dataInterface.update_timer()

    def handle_acc_sensitivity(self, text):
        print(f"handle_acc_sensitivity text={text}")
        self.controlInterface.accSensitivityButton.setText(self.tr(text))
        self.xyz_sens = text[:-1]
        print(f"sensitivity={self.xyz_sens}")
        s2 = 0
        split = self.xyz_sens.split('.')
        s1 = int(split[0])
        if len(split) == 2:
            s2 = int(split[1])
        self.handle_acc_settings(f"{self.xyz_sampling} {s1} {s2} {0}")
        self.dataInterface.update_timer()

    def config_success(self):
        InfoBar.success(
            title=self.tr('Configuration updated'),
            content=self.tr(f""),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=2000,  # won't disappear automatically
            parent=self.parent()
        )
        self.toolBar.bar.stop()

    def handle_audio_play(self, song):
        if song:
            song = song.lower()
            print(f"song={song}")
            self.handle_ble_audio(song)

    def handle_audio_stop(self):
        print("stop audio")
        self.handle_ble_audio("stop")

    def handle_led_on(self):
        status = self.controlInterface.switchButton.isChecked()
        print(f"handle_led_on status={status}")
        self.handle_ble_led(status)

    def handle_flip_box(self, value):
        print(f"handle_ble_flip={value}")
        self.handle_ble_flip(value)

    def handle_activity_on(self):
        status = self.controlInterface.activitySwitchButton.isChecked()
        print(f"handle_activity_on status={status}")
        self.dataInterface.update_timer()
        self.handle_ble_activity(status)


    def showColorDialog(self):
        w = ColorDialog(Qt.cyan, self.tr('Choose color'), self.window())
        w.colorChanged.connect(self.colorChanged)
        w.exec()

    def colorChanged(self, color):
        rgb_color = ImageColor.getcolor(color.name(), "RGB")
        print(f"rgb_color={rgb_color}")
        self.handle_ble_led(True, rgb_color)


