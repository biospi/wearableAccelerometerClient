# coding:utf-8
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import asyncio
from qasync import QEventLoop

from PyQt5.QtCore import Qt, QTranslator
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from src.gallery.app.common.config import cfg
from src.gallery.app.view.main_window import MainWindow

# from bleak import BleakScanner, BleakClient


def main():
    # enable dpi scale
    if cfg.get(cfg.dpiScale) == "Auto":
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    else:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # create application
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    # internationalization
    locale = cfg.get(cfg.language).value
    translator = FluentTranslator(locale)
    galleryTranslator = QTranslator()
    galleryTranslator.load(locale, "gallery", ".", ":/gallery/i18n")

    app.installTranslator(translator)
    app.installTranslator(galleryTranslator)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    # create main window
    w = MainWindow()
    w.connectInterface.toolBar
    w.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()