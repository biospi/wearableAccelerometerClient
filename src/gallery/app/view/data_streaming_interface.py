# coding:utf-8
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QFileDialog

from qfluentwidgets import DatePicker, TimePicker, AMTimePicker, ZhDatePicker, CalendarPicker, isDarkTheme, SpinBox, \
    Dialog, InfoBar, InfoBarPosition
from random import randint
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.config import cfg
from datetime import datetime, timedelta
from scipy.interpolate import interp1d


class ActivityCounter:
    def __init__(self, threshold, window_size_sec):
        self.threshold = threshold
        self.window_size_sec = window_size_sec
        self.buffer_x = []
        self.buffer_y = []
        self.buffer_z = []
        self.activity_counts = []

    def add_data(self, x, y, z):
        # Append the incoming data point to buffers
        self.buffer_x.append(x)
        self.buffer_y.append(y)
        self.buffer_z.append(z)

        # Process if we have enough data for at least one window
        if len(self.buffer_x) >= self.window_size_sec:
            # Extract window data
            window_x = self.buffer_x[:self.window_size_sec]
            window_y = self.buffer_y[:self.window_size_sec]
            window_z = self.buffer_z[:self.window_size_sec]

            # Remove the processed window data from the buffers
            self.buffer_x = self.buffer_x[self.window_size_sec:]
            self.buffer_y = self.buffer_y[self.window_size_sec:]
            self.buffer_z = self.buffer_z[self.window_size_sec:]

            # Calculate magnitude of the window
            magnitude = np.sqrt(np.square(window_x) + np.square(window_y) + np.square(window_z))

            # Count the number of times the magnitude exceeds the threshold
            count = np.sum(magnitude > self.threshold)
            self.activity_counts.append(int(count))

    def get_activity_counts(self):
        return self.activity_counts


class DataStreamingInterface(GalleryInterface):

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title="Streaming",
            subtitle='View real-time data.',
            parent=parent
        )
        self.timer = QtCore.QTimer()
        self.setObjectName('Data')
        self.toolBar.exportButton.setVisible(True)
        self.toolBar.connectButton.setVisible(False)
        self.toolBar.downloadButton.setVisible(False)
        self.toolBar.refreshButton.setVisible(False)
        self.toolBar.formatButton.setVisible(False)
        self.toolBar.scanButton.setVisible(False)
        self.toolBar.disconnectButton.setVisible(False)
        if self.toolBar.batteryWidget is not None:
            self.toolBar.batteryWidget.setVisible(True)
        self.toolBar.helpButton.setVisible(False)
        self.toolBar.batteryWidget.setVisible(False)
        self.refresh_interval = 1
        self.controlInterface = None
        self.incoming_data = False
        self.ble_data = [[datetime.now(), 0, 0, 0, None]]
        self.time_xyz = []
        self.win_size = 60 * 30
        self.add_xyz_plot(self)
        self.add_count_plot(self)
        self.toolBar.exportButton.clicked.connect(self.clicked_export)
        self.update_background_color()
        activity_counter = ActivityCounter(threshold=0, window_size_sec=0)
        self.activity_counter = activity_counter
        self.bargraph = pg.BarGraphItem(x = [], height = [], width = 0.6, brush ='#64B4BE')
        self.plot_count_graph.addItem(self.bargraph)
        self.hwid = "unknown"
        self.timer.timeout.connect(self.update_plot)
        self.update_timer()
        self.first_packet_received = False

    def is_timestamp_in_range(self, timestamp, window_seconds=2):
        current_time = datetime.now()
        start_time = current_time - timedelta(seconds=window_seconds)
        end_time = current_time + timedelta(seconds=window_seconds)
        return start_time <= timestamp <= end_time

    def parse_ble_data(self, msg):
        activity_count = None
        components = msg.split(',')
        timestamp_str = components[0]
        timestamp_ = datetime.strptime(timestamp_str, "%y%m%d%H%M%S")
        timestamp = int(timestamp_.timestamp())

        try:
            x = float(components[1])
            y = float(components[2])
            z = float(components[3])
            if len(components) > 4:
                activity_count = int(components[4])
        except Exception as e:
            print(e)
            activity_count = int(components[1])
            x = 0
            y = 0
            z = 0
        print("parse_ble_data", [timestamp, x, y, z, activity_count])
        return [timestamp, x, y, z, activity_count]

    def edit_threshold(self):
        #value = self.toolBar.thresholdButton.value()
        value = 0
        self.activity_counter.threshold = value
        print(f"threshold: {value}")

    def edit_count_w(self):
        value = self.toolBar.countWindowButton.value()
        self.activity_counter.window_size_sec = value
        print(f"count window: {value}")

    def clicked_theme(self):
        self.update_background_color()

    def update_background_color(self):
        if isDarkTheme():
            self.plot_xyz_graph.setBackground("#202020")
            self.plot_count_graph.setBackground("#202020")
            self.plot_xyz_graph.setTitle("Accelerometer", color="white", size="10pt")
            styles = {"color": "white", "font-size": "11px"}
            self.plot_xyz_graph.setLabel("left", "Acc", **styles)
            self.plot_xyz_graph.setLabel("bottom", "", **styles)
            self.plot_count_graph.setTitle("Activity", color="white", size="10pt")
            styles = {"color": "white", "font-size": "11px"}
            self.plot_count_graph.setLabel("left", "Amp", **styles)
            self.plot_count_graph.setLabel("bottom", "", **styles)
        else:
            self.plot_xyz_graph.setTitle("Accelerometer", color="black", size="10pt")
            styles = {"color": "b", "font-size": "11px"}
            self.plot_xyz_graph.setLabel("left", "Acc", **styles)
            self.plot_xyz_graph.setLabel("bottom", "", **styles)

            self.plot_count_graph.setTitle("Activity", color="black", size="10pt")
            styles = {"color": "b", "font-size": "11px"}
            self.plot_count_graph.setLabel("left", "Amp", **styles)
            self.plot_count_graph.setLabel("bottom", "", **styles)

            self.plot_xyz_graph.setBackground("#F1F3F6")
            self.plot_count_graph.setBackground("#F1F3F6")

    def export_data(self, df):
        print("exporting...")
        last_folder = cfg.get(cfg.downloadFolder)
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), last_folder)
        if not folder:
            return
        cfg.set(cfg.downloadFolder, folder)
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.hwid}_{datetime_string}.csv"
        filepath = Path(folder) / filename
        print(f"Export to {filepath}")
        df.to_csv(filepath, index=False)
        InfoBar.success(
            title=self.tr('Export Success'),
            content=self.tr(filepath.as_posix()),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=5000,  # won't disappear automatically
            parent=self
        )

    def clicked_export(self):
        print("clicked_export")
        df = pd.DataFrame(self.ble_data, columns=['timestamp', 'x', 'y', 'z', 'activity_count'])
        print(df)
        if len(df) <= 10:
            print("No much data to export.")
            title = self.tr("Data content warning")
            content = self.tr(
                f"There is only {len(df)} data points to export.\nWould you like to proceed with the export?")
            w = Dialog(title, content, self.window())
            w.setContentCopyable(True)
            if w.exec():
                print('Yes button is pressed')
                self.export_data(df)
            else:
                print('Cancel button is pressed')
        else:
            self.export_data(df)

    # def clicked_timeWindow(self):
    #     time_str = self.toolBar.timeWindowButton.text().split(' ')[0]
    #     if time_str.isdigit():
    #         tw = int(time_str)
    #         print(f"Time window={tw}")
    #         self.win_size = 60 * tw
    #     else:
    #         self.win_size = 60 * 30

    def add_xyz_plot(self, parent):
        self.plot_xyz_graph = pg.PlotWidget()
        #self.plot_graph.setStyleSheet("border :3px solid blue;padding :15px")
        #self.plot_xyz_graph.setBackground("#F1F3F6")
        #pen = pg.mkPen(color=(255, 0, 0))
        self.plot_xyz_graph.setTitle("Accelerometer", color="black", size="10pt")
        styles = {"color": "b", "font-size": "12px"}
        self.plot_xyz_graph.setLabel("left", "Acc", **styles)
        self.plot_xyz_graph.setLabel("bottom", "", **styles)
        self.plot_xyz_graph.addLegend()
        self.plot_xyz_graph.showGrid(x=True, y=True)
        #self.plot_xyz_graph.setYRange(-200,200, 0)
        legend = self.plot_xyz_graph.addLegend()
        legend.setOffset(5)  # Adjust these values (x, y) to move the legend

        self.xaxis = []
        # Get a line reference
        self.lineX = self.plot_xyz_graph.plot(
            self.time_xyz,
            self.xaxis,
            name="X axis",
            pen=pg.mkPen(color=(150, 150, 150))
        )
        self.yaxis = []
        self.lineY = self.plot_xyz_graph.plot(
            self.time_xyz,
            self.yaxis,
            name="Y axis",
            pen=pg.mkPen(color=(100, 180, 190))
        )
        self.zaxis = []
        self.lineZ = self.plot_xyz_graph.plot(
            self.time_xyz,
            self.zaxis,
            name="Z axis",
            pen=pg.mkPen(color=(100, 127, 227))
        )
        #self.update_timer()

        # calendar picker
        self.card1 = self.addExampleCard(
            # title=self.tr(Accelerometer'),
            title='',
            widgets=[self.plot_xyz_graph],
            fig=True,
            spacing=0
        )

    def add_count_plot(self, parent):
        self.counts = []
        self.plot_count_graph = pg.PlotWidget()
        self.plot_count_graph.setTitle("Activity", color="black", size="10pt")
        #self.plot_count_graph.setBackground("#F1F3F6")
        styles = {"color": "b", "font-size": "12px"}
        self.plot_count_graph.setLabel("left", "Amp", **styles)
        self.plot_count_graph.setLabel("bottom", "", **styles)
        self.plot_count_graph.addLegend()
        self.plot_count_graph.showGrid(x=True, y=True)
        # self.timer = QtCore.QTimer()
        # if self.controlInterface is not None:
        #     self.refresh_interval = int(self.controlInterface.accSamplingButton.text()[:-2]) * 1000
        #     if self.controlInterface.activitySwitchButton.isChecked():
        #         self.refresh_interval = 1000
        # self.timer.setInterval(self.refresh_interval)
        # #self.timer.timeout.connect(self.update_plot)
        # self.timer.start()
        #self.update_timer()

        self.card2 = self.addExampleCard(
            # title=self.tr('Activity'),
            title='',
            widgets=[self.plot_count_graph],
            fig=True
        )

    def update_timer(self):
        if self.controlInterface is not None:
            if self.controlInterface.accSamplingButton.text()[:-2].isdigit():
                self.refresh_interval = int((1 / int(self.controlInterface.accSamplingButton.text()[:-2]))*1000)+10
            if self.controlInterface.activitySwitchButton.isChecked():
                self.refresh_interval = 1000

        print(f"update_timer refresh_interval:{self.refresh_interval}")
        self.timer.setInterval(self.refresh_interval)
        if not self.timer.isActive():
            self.timer.start()
        self.trigger_resize()

    def find_last_non_zero(self, lst):
        for value in reversed(lst):
            if value != 0:
                return value
        return None

    def update_plot(self):
        timestamp, x, y, z, activity = None, 0, 0, 0, 0
        if not self.first_packet_received:
            return
        # if len(self.ble_data) > 1:
        #     print(f"self.ble_data[-1]={self.ble_data[-1]}")
        #print(f"refresh_interval:{self.refresh_interval}")
        if len(self.xaxis) > 100000:
            print("Reset data buffer")
            self.xaxis = []
            self.yaxis = []
            self.zaxis = []
            self.counts = []
            self.ble_data = []

        lx = self.find_last_non_zero(self.xaxis)
        ly = self.find_last_non_zero(self.yaxis)
        lz = self.find_last_non_zero(self.zaxis)
        la = self.find_last_non_zero(self.counts)
        #print(f"lx={lx} ly={ly} lz={lz} la={la}")

        if len(self.ble_data) > 1:
            timestamp, x, y, z, activity = self.ble_data[-1]

        if lx == x and ly == y and lz == z: #incoming data but not acc x y z #todo clean
            x, y, z, activity = 0, 0, 0, 0

        if not self.incoming_data:
            # print("No data to plot")
            x, y, z, activity = 0, 0, 0, 0
            self.counts.append(activity)
            #return
        # print(f"timestamp={timestamp} x={x} y={y} z={z} activity={activity}")
        self.xaxis.append(x)
        self.yaxis.append(y)
        self.zaxis.append(z)
        #self.time_xyz.append(timestamp)
        self.time_xyz = list(range(len(self.xaxis)))
        start_xyz = len(self.xaxis)-self.win_size
        if start_xyz < 0:
            start_xyz = 0
        self.lineX.setData(self.time_xyz[start_xyz: len(self.xaxis)], self.xaxis[start_xyz: len(self.xaxis)])
        self.lineY.setData(self.time_xyz[start_xyz: len(self.xaxis)], self.yaxis[start_xyz: len(self.xaxis)])
        self.lineZ.setData(self.time_xyz[start_xyz: len(self.xaxis)], self.zaxis[start_xyz: len(self.xaxis)])

        if self.controlInterface.activitySwitchButton.isChecked():
            #self.plot_count_graph.setVisible(True)
            self.card2.setVisible(True)
            if activity is None:
                self.activity_counter.add_data(x, y, z)
                self.counts = self.activity_counter.get_activity_counts()
            else:
                self.counts.append(activity)

            self.time_count = list(range(len(self.counts)))
            start_count = len(self.counts)-self.win_size
            if start_count < 0:
                start_count = 0
            # print(f"counts:{len(self.counts)} xaxis:{len(self.xaxis)} yaxis:{len(self.yaxis)} zaxis:{len(self.zaxis)}")
            self.plot_count_graph.removeItem(self.bargraph)
            self.time_count = self.time_count[start_count: len(self.counts)]
            self.counts = self.counts[start_count: len(self.counts)]

            self.bargraph = pg.BarGraphItem(x=self.time_count, height=self.counts, width=0.6, brush='#64B4BE')
            # print("add...")
            self.plot_count_graph.addItem(self.bargraph)
            # self.incoming_data = False
            #QTimer.singleShot(1500, lambda: setattr(self, 'incoming_data', False))
        else:
            #self.plot_count_graph.setVisible(False)
            self.card2.setVisible(False)

        # print(f"counts:{len(self.counts)} xaxis:{len(self.xaxis)} yaxis:{len(self.yaxis)} zaxis:{len(self.zaxis)}")

    def add_control_interface(self, interface):
        self.controlInterface = interface

    def trigger_resize(self):
        event = QResizeEvent(self.size(), self.size())
        self.resizeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # self.plot_count_graph.setMinimumHeight(int(event.size().height()/2-100))
        # self.plot_xyz_graph.setMinimumHeight(int(event.size().height()/2-100))

    def interpolate_list(self, data):
        #print(data)
        data_array = np.array(data, dtype=float)
        x = np.arange(len(data_array))
        mask = ~np.isnan(data_array)
        if np.all(~mask):
            #print("All values are missing, cannot interpolate.")
            return data
        # if np.all(mask):
        #     return data
        interpolator = interp1d(x[mask], data_array[mask], kind='linear', fill_value="extrapolate")
        data_interpolated = interpolator(x)
        return list(data_interpolated)

    def remove_duplicates(self, lst):
        a = np.array(lst)
        return np.unique(a).tolist()
