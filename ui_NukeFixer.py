# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'NukeFixer.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import ui_images_rc

class Ui_NukeFixer(object):
    def setupUi(self, NukeFixer):
        if not NukeFixer.objectName():
            NukeFixer.setObjectName(u"NukeFixer")
        NukeFixer.resize(720, 417)
        icon = QIcon()
        icon.addFile(u":/images/folder.png", QSize(), QIcon.Normal, QIcon.Off)
        NukeFixer.setWindowIcon(icon)
        NukeFixer.setAutoFillBackground(False)
        NukeFixer.setStyleSheet(u"QLabel\n"
"{\n"
"    font-size: 10pt;\n"
"}\n"
"\n"
"QCheckBox\n"
"{\n"
"    font-size: 10pt;\n"
"}\n"
"\n"
"QRadioButton\n"
"{\n"
"    font-size: 10pt;\n"
"}\n"
"\n"
"\n"
"\n"
"QListView:item:hover\n"
"{\n"
" border-style: none; \n"
" background-color: #4d4d4d;\n"
"}\n"
"\n"
"QGroupBox\n"
"{\n"
"    font-weight: bold;\n"
"    border: 1px solid gray; \n"
"    border-radius: 8px;\n"
"    margin-top: 6px;\n"
"   /* border-top-left-radius: 3px;\n"
"    border-top-right-radius: 3px;*/\n"
"}\n"
"\n"
"QGroupBox::title\n"
"{\n"
"   /* background-color: transparent;*/\n"
"   /* subcontrol-position: top left;*/\n"
"    \n"
"    subcontrol-origin: margin;\n"
"    padding:0px 5px;\n"
"}\n"
"\n"
"\n"
"QToolTip\n"
"{\n"
"     border: 0px solid black;\n"
"     background-color: #ffa02f;\n"
"     padding: 0px;\n"
"     border-radius: 2px;\n"
"     opacity: 100;\n"
"	font-size: 16px;\n"
"}\n"
"\n"
"QWidget\n"
"{\n"
"    color: #b1b1b1;\n"
"    background-color: #323232;\n"
"	font-size: 10pt;\n"
"\n"
"}\n"
"\n"
"QWidget:item:h"
                        "over\n"
"{\n"
"    background-color: gray;\n"
"}\n"
"\n"
"\n"
"QWidget:item:selected\n"
"{\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"}\n"
"\n"
"QMenuBar::item\n"
"{\n"
"    background: transparent;\n"
"}\n"
"\n"
"QMenuBar::item:selected\n"
"{\n"
"    background: transparent;\n"
"    border: 1px solid #ffaa00;\n"
"}\n"
"\n"
"QMenuBar::item:pressed\n"
"{\n"
"    background: #444;\n"
"    border: 1px solid #000;\n"
"    background-color: QLinearGradient(\n"
"        x1:0, y1:0,\n"
"        x2:0, y2:1,\n"
"        stop:1 #212121,\n"
"        stop:0.4 #343434/*,\n"
"        stop:0.2 #343434,\n"
"        stop:0.1 #ffaa00*/\n"
"    );\n"
"    margin-bottom:-1px;\n"
"    padding-bottom:1px;\n"
"}\n"
"\n"
"QMenu\n"
"{\n"
"    border: 1px solid #000;\n"
"}\n"
"\n"
"QMenu::item\n"
"{\n"
"    padding: 2px 20px 2px 20px;\n"
"}\n"
"\n"
"QMenu::item:selected\n"
"{\n"
"    color: #000000;\n"
"}\n"
"\n"
"QWidget:disabled\n"
"{\n"
"    color: #404040;\n"
"    b"
                        "ackground-color: #323232;\n"
"}\n"
"\n"
"QAbstractItemView\n"
"{\n"
"   /* background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, stop: 0.1 #646464, stop: 1 #5d5d5d);*/\n"
"  background-color: #4d4d4d\n"
"}\n"
"\n"
"QTextWidget\n"
"{\n"
"    background-color: #4d4d4d\n"
"}\n"
"\n"
"QWidget:focus\n"
"{\n"
"    /*border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);*/\n"
"}\n"
"\n"
"QLineEdit\n"
"{\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, stop: 0 #646464, stop: 1 #5d5d5d);\n"
"    padding: 1px;\n"
"    border-style: solid;\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius: 2;\n"
"    padding-left: 16px;\n"
"\n"
"}\n"
"\n"
"QPushButton\n"
"{\n"
"    color: #b1b1b1;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);\n"
"    border-width: 1px;\n"
"    border-color: #1e1e1e;\n"
"    bo"
                        "rder-style: solid;\n"
"    border-radius: 4;\n"
"    padding: 3px;\n"
"    font-size: 16px;\n"
"    padding-left: 5px;\n"
"    padding-right: 5px;\n"
"	outline: 0;\n"
"}\n"
"\n"
"QPushButton:pressed\n"
"{\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);\n"
"}\n"
"\n"
"QPushButton:checked\n"
"{\n"
"	\n"
"	background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #946223, stop: 0.1 #905f22, stop: 0.5 #885a20, stop: 0.9 #80551e, stop: 1 #7d531e);\n"
"}\n"
"\n"
"QPushButton:focus\n"
"{\n"
"\n"
"}\n"
"\n"
"QComboBox\n"
"{\n"
"    selection-background-color: #ffaa00;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);\n"
"    border-style: solid;\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius: 2;\n"
"	padding-left: 16px;\n"
"\n"
"\n"
"}\n"
"\n"
"QComboBox:hover,QPushButton"
                        ":hover\n"
"{\n"
"    border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"}\n"
"\n"
"\n"
"QComboBox:on\n"
"{\n"
"    padding-top: 3px;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);\n"
"    selection-background-color: #ffaa00;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView\n"
"{\n"
"    border: 2px solid darkgray;\n"
"    /*selection-background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);*/\n"
"    selection-background-color: #ffa02f;\n"
"}\n"
"\n"
"QComboBox::drop-down\n"
"{\n"
"     subcontrol-origin: padding;\n"
"     subcontrol-position: top right;\n"
"     width: 15px;\n"
"\n"
"     border-left-width: 0px;\n"
"     border-left-color: darkgray;\n"
"     border-left-style: solid; /* just a single line */\n"
"     border-top-right-radius: 3px; /* same radius as the QComboBox */\n"
"     border-bottom-right-ra"
                        "dius: 3px;\n"
" }\n"
"\n"
"QComboBox::down-arrow\n"
"{\n"
"     image: url(:images/down_arrow.png);\n"
"}\n"
"\n"
"/*\n"
"QComboBox::up-arrow\n"
"{\n"
"     image: url(:images/up_arrow.png);\n"
"}\n"
"*/\n"
"QGroupBox:focus\n"
"{\n"
"  border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"}\n"
"\n"
"QTextEdit:focus\n"
"{\n"
"    border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"}\n"
"\n"
"QScrollBar:horizontal {\n"
"     border:  solid #222222;\n"
"     background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #121212, stop: 0.2 #282828, stop: 1 #484848);\n"
"     height: 7px;\n"
"     margin: 0px 16px 0 16px;\n"
"}\n"
"\n"
"QScrollBar::handle:horizontal\n"
"{\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ffa02f, stop: 0.5 #d7801a, stop: 1 #ffa02f);\n"
"      min-height: 20px;\n"
"      border-radius: 2px;\n"
"}\n"
"\n"
"QScrollBar::add-line:horizontal {\n"
"      border: 1"
                        "px solid #1b1b19;\n"
"      border-radius: 2px;\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"      width: 14px;\n"
"      subcontrol-position: right;\n"
"      subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::sub-line:horizontal {\n"
"      border: 1px solid #1b1b19;\n"
"      border-radius: 2px;\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"      width: 14px;\n"
"     subcontrol-position: left;\n"
"     subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::right-arrow:horizontal, QScrollBar::left-arrow:horizontal\n"
"{\n"
"      border: 1px solid black;\n"
"      width: 1px;\n"
"      height: 1px;\n"
"      background: white;\n"
"}\n"
"\n"
"QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal\n"
"{\n"
"      background: none;\n"
"}\n"
"\n"
"QScrollBar:vertical\n"
"{\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0.0 #121212, stop: 0.2 #282828, stop"
                        ": 1 #484848);\n"
"      width: 7px;\n"
"      margin: 16px 0 16px 0;\n"
"      border: 1px solid #222222;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical\n"
"{\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 0.5 #d7801a, stop: 1 #ffa02f);\n"
"      min-height: 20px;\n"
"      border-radius: 2px;\n"
"}\n"
"\n"
"QScrollBar::add-line:vertical\n"
"{\n"
"      border: 1px solid #1b1b19;\n"
"      border-radius: 2px;\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"      height: 14px;\n"
"      subcontrol-position: bottom;\n"
"      subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::sub-line:vertical\n"
"{\n"
"      border: 1px solid #1b1b19;\n"
"      border-radius: 2px;\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d7801a, stop: 1 #ffa02f);\n"
"      height: 14px;\n"
"      subcontrol-position: top;\n"
"      subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::up-arrow:vertical, QScrollB"
                        "ar::down-arrow:vertical\n"
"{\n"
"      border: 1px solid black;\n"
"      width: 1px;\n"
"      height: 1px;\n"
"      background: white;\n"
"}\n"
"\n"
"\n"
"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical\n"
"{\n"
"      background: none;\n"
"}\n"
"\n"
"QTextEdit\n"
"{\n"
"    background-color: #242424;\n"
"}\n"
"\n"
"QPlainTextEdit\n"
"{\n"
"    background-color: #242424;\n"
"}\n"
"\n"
"QHeaderView::section\n"
"{\n"
"    /*           table headers */\n"
"\n"
"    /*background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #616161, stop: 0.5 #505050, stop: 0.6 #434343, stop:1 #656565);*/\n"
"    background-color: #242424;\n"
"    color: white;\n"
"    padding-left: 4px;\n"
"    border: 1px solid #6c6c6c;\n"
"}\n"
"\n"
"QCheckBox:disabled\n"
"{\n"
"color: #414141;\n"
"}\n"
"\n"
"QDockWidget::title\n"
"{\n"
"    text-align: center;\n"
"    spacing: 3px; /* spacing between items in the tool bar */\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #323232, stop: 0.5 #24"
                        "2424, stop:1 #323232);\n"
"}\n"
"\n"
"QDockWidget::close-button, QDockWidget::float-button\n"
"{\n"
"    text-align: center;\n"
"    spacing: 1px; /* spacing between items in the tool bar */\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #323232, stop: 0.5 #242424, stop:1 #323232);\n"
"}\n"
"\n"
"QDockWidget::close-button:hover, QDockWidget::float-button:hover\n"
"{\n"
"    background: #242424;\n"
"}\n"
"\n"
"QDockWidget::close-button:pressed, QDockWidget::float-button:pressed\n"
"{\n"
"    padding: 1px -1px -1px 1px;\n"
"}\n"
"\n"
"QMainWindow::separator\n"
"{\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #161616, stop: 0.5 #151515, stop: 0.6 #212121, stop:1 #343434);\n"
"    color: white;\n"
"    padding-left: 4px;\n"
"    border: 1px solid #4c4c4c;\n"
"    spacing: 3px; /* spacing between items in the tool bar */\n"
"}\n"
"\n"
"QMainWindow::separator:hover\n"
"{\n"
"\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d7801a, stop:0."
                        "5 #b56c17 stop:1 #ffa02f);\n"
"    color: white;\n"
"    padding-left: 4px;\n"
"    border: 1px solid #6c6c6c;\n"
"    spacing: 3px; /* spacing between items in the tool bar */\n"
"}\n"
"\n"
"QToolBar::handle\n"
"{\n"
"     spacing: 3px; /* spacing between items in the tool bar */\n"
"     background: url(:images/handle.png);\n"
"}\n"
"\n"
"QMenu::separator\n"
"{\n"
"    height: 2px;\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #161616, stop: 0.5 #151515, stop: 0.6 #212121, stop:1 #343434);\n"
"    color: white;\n"
"    padding-left: 4px;\n"
"    margin-left: 10px;\n"
"    margin-right: 5px;\n"
"}\n"
"\n"
"QProgressBar\n"
"{\n"
"    border: 2px solid grey;\n"
"    border-radius: 3px;\n"
"    text-align: center;\n"
"}\n"
"\n"
"QProgressBar::chunk\n"
"{\n"
"    background-color: #d7801a;\n"
"    width: 2.15px;\n"
"    margin: 0.5px;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    color: #b1b1b1;\n"
"    border: 1px solid #444;\n"
"    border-bottom-style: none;\n"
"    background-color: #323232"
                        ";\n"
"    padding-left: 10px;\n"
"    padding-right: 10px;\n"
"    padding-top: 3px;\n"
"    padding-bottom: 2px;\n"
"    margin-right: -1px;\n"
"}\n"
"\n"
"QTabWidget::pane {\n"
"    border: 1px solid #444;\n"
"    top: 1px;\n"
"}\n"
"\n"
"QTabBar::tab:last\n"
"{\n"
"    margin-right: 0; /* the last selected tab has nothing to overlap with on the right */\n"
"    border-top-right-radius: 3px;\n"
"}\n"
"\n"
"QTabBar::tab:first:!selected\n"
"{\n"
" margin-left: 0px; /* the last selected tab has nothing to overlap with on the right */\n"
"\n"
"\n"
"    border-top-left-radius: 3px;\n"
"}\n"
"\n"
"QTabBar::tab:!selected\n"
"{\n"
"    color: #b1b1b1;\n"
"    border-bottom-style: solid;\n"
"    margin-top: 3px;\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:1 #212121, stop:.4 #343434);\n"
"}\n"
"\n"
"QTabBar::tab:selected\n"
"{\n"
"    border-top-left-radius: 3px;\n"
"    border-top-right-radius: 3px;\n"
"    margin-bottom: 0px;\n"
"}\n"
"\n"
"QTabBar::tab:!selected:hover\n"
"{\n"
"    /*bord"
                        "er-top: 2px solid #ffaa00;\n"
"    padding-bottom: 3px;*/\n"
"    border-top-left-radius: 3px;\n"
"    border-top-right-radius: 3px;\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:1 #212121, stop:0.4 #343434, stop:0.2 #343434, stop:0.1 #ffaa00);\n"
"}\n"
"\n"
"QRadioButton::indicator:checked, QRadioButton::indicator:unchecked{\n"
"    color: #b1b1b1;\n"
"    background-color: #323232;\n"
"    border: 1px solid #b1b1b1;\n"
"    border-radius: 6px;\n"
"}\n"
"\n"
"QRadioButton::indicator:checked\n"
"{\n"
"    background-color: qradialgradient(\n"
"        cx: 0.5, cy: 0.5,\n"
"        fx: 0.5, fy: 0.5,\n"
"        radius: 1.0,\n"
"        stop: 0.25 #ffaa00,\n"
"        stop: 0.3 #323232\n"
"    );\n"
"}\n"
"\n"
"QRadioButton::indicator\n"
"{\n"
"    border-radius: 1px;\n"
"}\n"
"\n"
"QRadioButton::indicator:hover, QCheckBox::indicator:hover\n"
"{\n"
"    border: 1px solid #ffaa00;\n"
"}\n"
"\n"
"QCheckBox::indicator{\n"
"    color: #b1b1b1;\n"
"    background-color: #323232;\n"
"    borde"
                        "r: 1px solid #b1b1b1;\n"
"    width: 9px;\n"
"    height: 9px;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked\n"
"{\n"
"    image:url(:images/checkbox_checked.png);\n"
"    /*color: #ffaa00;*/\n"
"    /*background-color:#ffaa00;*/\n"
"}\n"
"\n"
"QRadioButton::indicator:disabled\n"
"{\n"
"    border: 1px solid #444;\n"
"}\n"
"\n"
"QCheckBox::indicator:disabled\n"
"{\n"
"    border: 1px solid #444;\n"
"    /*image:url(:images/checkbox.png);*/\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:disabled\n"
"{\n"
"    border: 1px solid #444;\n"
"    image:url(:images/checkbox_disabled.png);\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
"QSpinBox\n"
"{\n"
"    selection-background-color: #ffaa00;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, stop: 0 #646464, stop: 1 #5d5d5d);\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius:2;\n"
"}\n"
"QAbstractSpinBox\n"
"{\n"
"    selection-background-color: #ffaa00;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, sto"
                        "p: 0 #646464, stop: 1 #5d5d5d);\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius:2;\n"
"}\n"
"\n"
"QSpinBox::up-arrow\n"
"{\n"
"	background-image: url(:images/up_arrow.png);\n"
"    width: 7px; height: 5px;\n"
"}\n"
"QAbstractSpinBox::up-arrow\n"
"{\n"
"	background-image: url(:images/up_arrow.png);\n"
"    width: 7px; height: 5px;\n"
"}\n"
"\n"
"QSpinBox::down-arrow\n"
"{\n"
"	background-image: url(:images/down_arrow.png);\n"
"     width: 7px; height: 5px;\n"
"}\n"
"QAbstractSpinBox::down-arrow\n"
"{\n"
"	background-image: url(:images/down_arrow.png);\n"
"     width: 7px; height: 5px;\n"
"}\n"
"\n"
"QSpinBox::up-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"QAbstractSpinBox::up-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"QSpinBox::down-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"QAbstractSpinBox::down-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"\n"
"QDoubleSpinBox\n"
"{\n"
"    selection-background-color: #ffaa00;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0,"
                        " y2: 1, stop: 0 #4d4d4d, stop: 0 #646464, stop: 1 #5d5d5d);\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius:2;\n"
"}\n"
"\n"
"QDoubleSpinBox::up-arrow\n"
"{\n"
"	background-image: url(:images/up_arrow.png);\n"
"    width: 7px; height: 5px;\n"
"\n"
"}\n"
"\n"
"QDoubleSpinBox::down-arrow\n"
"{\n"
"	background-image: url(:images/down_arrow.png);\n"
"     width: 7px; height: 5px;\n"
"}\n"
"\n"
"QDoubleSpinBox::up-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"\n"
"QDoubleSpinBox::down-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"\n"
"QCalendarWidget::prevmonth\n"
"{\n"
"	background-image: url(:images/left_arrow.png);\n"
"}\n"
"QCalendarWidget::nextmonth\n"
"{\n"
"	background-image: url(:images/right_arrow.png);\n"
"}\n"
"QCalendarWidget\n"
"{\n"
"	 background-color: #242424;\n"
"    color: white;\n"
"}\n"
"\n"
"")
        NukeFixer.setUnifiedTitleAndToolBarOnMac(True)
        self.centralwidget = QWidget(NukeFixer)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_38 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_38.setObjectName(u"horizontalLayout_38")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setMinimumSize(QSize(200, 150))
        self.tabWidget.setMaximumSize(QSize(16777215, 400))
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.horizontalLayout_10 = QHBoxLayout(self.tab_2)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_32 = QHBoxLayout()
        self.horizontalLayout_32.setObjectName(u"horizontalLayout_32")
        self.label_20 = QLabel(self.tab_2)
        self.label_20.setObjectName(u"label_20")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_20.sizePolicy().hasHeightForWidth())
        self.label_20.setSizePolicy(sizePolicy1)
        self.label_20.setMinimumSize(QSize(135, 25))

        self.horizontalLayout_32.addWidget(self.label_20)

        self.search_start = QLineEdit(self.tab_2)
        self.search_start.setObjectName(u"search_start")
        self.search_start.setMinimumSize(QSize(140, 25))

        self.horizontalLayout_32.addWidget(self.search_start)

        self.browse = QPushButton(self.tab_2)
        self.browse.setObjectName(u"browse")
        self.browse.setMinimumSize(QSize(75, 25))

        self.horizontalLayout_32.addWidget(self.browse)


        self.verticalLayout.addLayout(self.horizontalLayout_32)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_22 = QLabel(self.tab_2)
        self.label_22.setObjectName(u"label_22")
        sizePolicy1.setHeightForWidth(self.label_22.sizePolicy().hasHeightForWidth())
        self.label_22.setSizePolicy(sizePolicy1)
        self.label_22.setMinimumSize(QSize(135, 25))
        self.label_22.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.label_22)

        self.only_if_contains = QLineEdit(self.tab_2)
        self.only_if_contains.setObjectName(u"only_if_contains")
        self.only_if_contains.setMinimumSize(QSize(140, 25))

        self.horizontalLayout_7.addWidget(self.only_if_contains)


        self.horizontalLayout_8.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_26 = QLabel(self.tab_2)
        self.label_26.setObjectName(u"label_26")
        sizePolicy1.setHeightForWidth(self.label_26.sizePolicy().hasHeightForWidth())
        self.label_26.setSizePolicy(sizePolicy1)
        self.label_26.setMinimumSize(QSize(80, 25))
        self.label_26.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_26)

        self.search_for = QLineEdit(self.tab_2)
        self.search_for.setObjectName(u"search_for")
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.search_for.sizePolicy().hasHeightForWidth())
        self.search_for.setSizePolicy(sizePolicy2)
        self.search_for.setMinimumSize(QSize(140, 25))

        self.horizontalLayout_5.addWidget(self.search_for)


        self.horizontalLayout_8.addLayout(self.horizontalLayout_5)


        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_23 = QLabel(self.tab_2)
        self.label_23.setObjectName(u"label_23")
        sizePolicy1.setHeightForWidth(self.label_23.sizePolicy().hasHeightForWidth())
        self.label_23.setSizePolicy(sizePolicy1)
        self.label_23.setMinimumSize(QSize(135, 25))
        self.label_23.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.label_23)

        self.version_regex = QLineEdit(self.tab_2)
        self.version_regex.setObjectName(u"version_regex")
        self.version_regex.setMinimumSize(QSize(140, 25))

        self.horizontalLayout_3.addWidget(self.version_regex)


        self.horizontalLayout_4.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label = QLabel(self.tab_2)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setMinimumSize(QSize(110, 25))

        self.horizontalLayout_2.addWidget(self.label)

        self.apply_first = QRadioButton(self.tab_2)
        self.apply_first.setObjectName(u"apply_first")
        sizePolicy1.setHeightForWidth(self.apply_first.sizePolicy().hasHeightForWidth())
        self.apply_first.setSizePolicy(sizePolicy1)
        self.apply_first.setMinimumSize(QSize(50, 25))

        self.horizontalLayout_2.addWidget(self.apply_first)

        self.apply_last = QRadioButton(self.tab_2)
        self.apply_last.setObjectName(u"apply_last")
        sizePolicy1.setHeightForWidth(self.apply_last.sizePolicy().hasHeightForWidth())
        self.apply_last.setSizePolicy(sizePolicy1)
        self.apply_last.setMinimumSize(QSize(50, 25))

        self.horizontalLayout_2.addWidget(self.apply_last)

        self.apply_all = QRadioButton(self.tab_2)
        self.apply_all.setObjectName(u"apply_all")
        sizePolicy1.setHeightForWidth(self.apply_all.sizePolicy().hasHeightForWidth())
        self.apply_all.setSizePolicy(sizePolicy1)
        self.apply_all.setMinimumSize(QSize(50, 25))

        self.horizontalLayout_2.addWidget(self.apply_all)


        self.horizontalLayout_4.addLayout(self.horizontalLayout_2)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_24 = QLabel(self.tab_2)
        self.label_24.setObjectName(u"label_24")
        sizePolicy1.setHeightForWidth(self.label_24.sizePolicy().hasHeightForWidth())
        self.label_24.setSizePolicy(sizePolicy1)
        self.label_24.setMinimumSize(QSize(135, 25))
        self.label_24.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_9.addWidget(self.label_24)

        self.nuke_executable = QLineEdit(self.tab_2)
        self.nuke_executable.setObjectName(u"nuke_executable")
        self.nuke_executable.setMinimumSize(QSize(140, 25))

        self.horizontalLayout_9.addWidget(self.nuke_executable)


        self.verticalLayout.addLayout(self.horizontalLayout_9)


        self.horizontalLayout_10.addLayout(self.verticalLayout)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.horizontalLayout = QHBoxLayout(self.tab)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.python_script = QPlainTextEdit(self.tab)
        self.python_script.setObjectName(u"python_script")

        self.horizontalLayout.addWidget(self.python_script)

        self.tabWidget.addTab(self.tab, "")

        self.verticalLayout_3.addWidget(self.tabWidget)

        self.tableWidget = QTableWidget(self.centralwidget)
        self.tableWidget.setObjectName(u"tableWidget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy3)
        self.tableWidget.setMinimumSize(QSize(700, 150))
        self.tableWidget.setMaximumSize(QSize(16000, 16000))

        self.verticalLayout_3.addWidget(self.tableWidget)

        self.horizontalLayout_34 = QHBoxLayout()
        self.horizontalLayout_34.setObjectName(u"horizontalLayout_34")
        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_34.addItem(self.horizontalSpacer_14)

        self.select_all_none = QCheckBox(self.centralwidget)
        self.select_all_none.setObjectName(u"select_all_none")
        self.select_all_none.setMinimumSize(QSize(33, 25))
        self.select_all_none.setAutoFillBackground(False)
        self.select_all_none.setChecked(False)

        self.horizontalLayout_34.addWidget(self.select_all_none)


        self.verticalLayout_3.addLayout(self.horizontalLayout_34)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.execute = QPushButton(self.centralwidget)
        self.execute.setObjectName(u"execute")
        sizePolicy2.setHeightForWidth(self.execute.sizePolicy().hasHeightForWidth())
        self.execute.setSizePolicy(sizePolicy2)
        self.execute.setMinimumSize(QSize(350, 50))
        self.execute.setBaseSize(QSize(520, 51))
        self.execute.setAutoFillBackground(False)
        self.execute.setFlat(True)

        self.horizontalLayout_6.addWidget(self.execute)


        self.verticalLayout_3.addLayout(self.horizontalLayout_6)


        self.horizontalLayout_38.addLayout(self.verticalLayout_3)

        NukeFixer.setCentralWidget(self.centralwidget)

        self.retranslateUi(NukeFixer)

        self.tabWidget.setCurrentIndex(0)
        self.execute.setDefault(True)


        QMetaObject.connectSlotsByName(NukeFixer)
    # setupUi

    def retranslateUi(self, NukeFixer):
        NukeFixer.setWindowTitle(QCoreApplication.translate("NukeFixer", u"NukeFixer \u2013 Beware! Dangerous Toy", None))
#if QT_CONFIG(tooltip)
        NukeFixer.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label_20.setText(QCoreApplication.translate("NukeFixer", u"Search Root Directory:", None))
#if QT_CONFIG(tooltip)
        self.search_start.setToolTip(QCoreApplication.translate("NukeFixer", u"<html><head/><body><p>Search here and below</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.search_start.setText(QCoreApplication.translate("NukeFixer", u"z:", None))
        self.browse.setText(QCoreApplication.translate("NukeFixer", u"...", None))
        self.label_22.setText(QCoreApplication.translate("NukeFixer", u"Only if contains:", None))
#if QT_CONFIG(tooltip)
        self.only_if_contains.setToolTip(QCoreApplication.translate("NukeFixer", u"<html><head/><body><p>Only consider search results that contain this string in the path.<br/><br/>Typically /publish/render</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.only_if_contains.setText(QCoreApplication.translate("NukeFixer", u"/work/comp/", None))
        self.label_26.setText(QCoreApplication.translate("NukeFixer", u"Search for:", None))
#if QT_CONFIG(tooltip)
        self.search_for.setToolTip(QCoreApplication.translate("NukeFixer", u"<html><head/><body><p>Search for Unix style pathname pattern expansion</p><p>Typically v??? for version</p><p><br/></p><p>see https://docs.python.org/3/library/glob.html</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.search_for.setInputMask("")
        self.search_for.setText(QCoreApplication.translate("NukeFixer", u"_comp_v???.nk", None))
        self.label_23.setText(QCoreApplication.translate("NukeFixer", u"Version Regex:", None))
#if QT_CONFIG(tooltip)
        self.version_regex.setToolTip(QCoreApplication.translate("NukeFixer", u"<html><head/><body><p>Only consider search results that contain this string in the path.<br/><br/>Typically /publish/render</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.version_regex.setText(QCoreApplication.translate("NukeFixer", u"*._v(\\d{3}).nk", None))
        self.label.setText(QCoreApplication.translate("NukeFixer", u"Apply to Versions:", None))
        self.apply_first.setText(QCoreApplication.translate("NukeFixer", u"First", None))
        self.apply_last.setText(QCoreApplication.translate("NukeFixer", u"Last", None))
        self.apply_all.setText(QCoreApplication.translate("NukeFixer", u"All", None))
        self.label_24.setText(QCoreApplication.translate("NukeFixer", u"Nuke Executable:", None))
#if QT_CONFIG(tooltip)
        self.nuke_executable.setToolTip(QCoreApplication.translate("NukeFixer", u"<html><head/><body><p>Only consider search results that contain this string in the path.<br/><br/>Typically /publish/render</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.nuke_executable.setText(QCoreApplication.translate("NukeFixer", u"Nuke Executable:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("NukeFixer", u"Find Nuke Scripts", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("NukeFixer", u"Python Script", None))
#if QT_CONFIG(tooltip)
        self.tableWidget.setToolTip(QCoreApplication.translate("NukeFixer", u"<html><head/><body><p>Shows folders found by filters above.<br/></p><p>Folders with shared paths one directory up from found path are shown as one line.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.select_all_none.setToolTip(QCoreApplication.translate("NukeFixer", u"<html><head/><body><p>Allows to select or deselect all lines in the table</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.select_all_none.setText(QCoreApplication.translate("NukeFixer", u"All", None))
#if QT_CONFIG(tooltip)
        self.execute.setToolTip(QCoreApplication.translate("NukeFixer", u"<html><head/><body><p><span style=\" font-size:10pt;\">Recursively deletes all folders in Eat List.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.execute.setText(QCoreApplication.translate("NukeFixer", u"Execute", None))
    # retranslateUi

