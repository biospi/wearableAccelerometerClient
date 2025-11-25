# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel

from qfluentwidgets import (DropDownPushButton, PushButton, SwitchButton, RoundMenu, FluentIcon, SplitPushButton,
                            TransparentPushButton,
                            SpinBox, InfoBar, InfoBarPosition)
from .gallery_interface import GalleryInterface
from ..common.translator import Translator

class ControlPanelInterface(GalleryInterface):
    """ Control panel interface """

    def __init__(self, parent=None):
        translator = Translator()
        super().__init__(
            title="Settings",
            subtitle='Set up and test functionalities.',
            parent=parent
        )
        self.setObjectName('basicInputInterface')
        self.toolBar.exportButton.setVisible(False)
        self.toolBar.connectButton.setVisible(False)
        self.toolBar.scanButton.setVisible(False)
        if self.toolBar.batteryWidget is not None:
            self.toolBar.batteryWidget.setVisible(True)
        self.toolBar.disconnectButton.setVisible(False)
        self.toolBar.downloadButton.setVisible(False)
        self.toolBar.refreshButton.setVisible(False)
        self.toolBar.formatButton.setVisible(False)
        self.toolBar.helpButton.setVisible(False)
        self.toolBar.batteryWidget.setVisible(False)

        # switch button
        self.switchButton = SwitchButton(self.tr('Off'))
        self.switchButton.checkedChanged.connect(self.onSwitchCheckedChanged)

        self.colorButton = PushButton(self.tr('color'))

        # drop down button
        self.playMusicMenu = RoundMenu(parent=self)
        self.playAudioButton = DropDownPushButton(self.tr('Play sound'), self, FluentIcon.MUSIC)
        self.playAudioButton.setMenu(self.playMusicMenu)
        self.stopAudioButton = TransparentPushButton(FluentIcon.CANCEL, 'Stop', self)
        self.addCards("RGB Led Light", "Audio Speaker",[self.switchButton, self.colorButton],
                      [self.playAudioButton, self.stopAudioButton ])

        self.accSamplingMenu = RoundMenu(parent=self)
        self.accSamplingButton = SplitPushButton(self.tr('Sampling'), self, FluentIcon.SETTING)
        self.accSamplingButton.setFlyout(self.accSamplingMenu)

        self.accSensitivityMenu = RoundMenu(parent=self)
        self.accSensitivityButton = SplitPushButton(self.tr('Sensitivity'), self, FluentIcon.SETTING)
        self.accSensitivityButton.setFlyout(self.accSensitivityMenu)

        self.activitySwitchButton = SwitchButton(self.tr('Off'))
        self.activitySwitchButton.checkedChanged.connect(self.onActivitySwitchCheckedChanged)
        self.addExampleCard(
            self.tr('Accelerometer'),
            [self.accSamplingButton, self.accSensitivityButton, QLabel(self.tr('Activity count')), self.activitySwitchButton],
            xmargin=15
        )

        self.bleFlipBox = SpinBox(self)
        self.bleFlipBox.setValue(1)
        self.bleFlipBox.valueChanged.connect(self.onSpinBoxChanged)
        self.bleFlipBox.setRange(1, 100)
        #self.bleFlipBox.setEnabled(False)
        self.addExampleCard(
            self.tr('Bluetooth trigger'),
            [QLabel(self.tr('Number of times to flip device to make discoverable')), self.bleFlipBox],
            xmargin=15
        )

    def onSwitchCheckedChanged(self, isChecked):
        if isChecked:
            self.switchButton.setText(self.tr('On'))
        else:
            self.switchButton.setText(self.tr('Off'))


    def onActivitySwitchCheckedChanged(self, isChecked):
        print("onActivitySwitchCheckedChanged", isChecked)


    def onSpinBoxChanged(self, value):
        print("onSpinBoxChanged", value)
    # def showColorDialog(self):
    #     w = ColorDialog(Qt.cyan, self.tr('Choose color'), self.window())
    #     w.colorChanged.connect(lambda c: print(c.name()))
    #     w.exec()

    # def showDisconnectWarning(self):
    #     print(f"showDisconnectWarning...")
    #     InfoBar.warning(
    #         title=self.tr('Device disconnected'),
    #         content=self.tr(f"The bluetooth connection was interrupted by the device"),
    #         orient=Qt.Horizontal,
    #         isClosable=True,
    #         position=InfoBarPosition.BOTTOM,
    #         duration=10000,
    #         parent=self.parent()
    #     )