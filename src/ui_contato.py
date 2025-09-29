# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'contatoWHBJBd.ui'
##
## Created by: Qt User Interface Compiler version 6.4.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PyQt6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PyQt6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout,
    QHeaderView, QLCDNumber, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QPushButton,
    QSizePolicy, QSlider, QSpacerItem, QTabWidget,
    QTableView, QToolButton, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(688, 640)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.toolButton = QToolButton(self.centralwidget)
        self.toolButton.setObjectName(u"toolButton")

        self.verticalLayout.addWidget(self.toolButton)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayout = QGridLayout(self.tab)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")

        self.gridLayout.addLayout(self.verticalLayout_6, 0, 7, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_3 = QLabel(self.tab)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_4.addWidget(self.label_3)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_7 = QLabel(self.tab)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_10.addWidget(self.label_7)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            
        self.horizontalLayout_10.addItem(self.horizontalSpacer_3)

        self.comboBox_2 = QComboBox(self.tab)
        self.comboBox_2.setObjectName(u"comboBox_2")

        self.horizontalLayout_10.addWidget(self.comboBox_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_10)

        self.label_4 = QLabel(self.tab)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout_4.addWidget(self.label_4)

        self.horizontalSlider = QSlider(self.tab)
        self.horizontalSlider.setObjectName(u"horizontalSlider")
        self.horizontalSlider.setOrientation(Qt.Orientation.Horizontal)

        self.verticalLayout_4.addWidget(self.horizontalSlider)

        self.label_5 = QLabel(self.tab)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout_4.addWidget(self.label_5)

        self.horizontalSlider_2 = QSlider(self.tab)
        self.horizontalSlider_2.setObjectName(u"horizontalSlider_2")
        self.horizontalSlider_2.setOrientation(Qt.Orientation.Horizontal)

        self.verticalLayout_4.addWidget(self.horizontalSlider_2)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_8 = QLabel(self.tab)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_12.addWidget(self.label_8)


        self.horizontalLayout_11.addLayout(self.horizontalLayout_12)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.horizontalLayout_11.addItem(self.verticalSpacer)

        self.lcdNumber = QLCDNumber(self.tab)
        self.lcdNumber.setObjectName(u"lcdNumber")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lcdNumber.sizePolicy().hasHeightForWidth())
        self.lcdNumber.setSizePolicy(sizePolicy1)

        self.horizontalLayout_11.addWidget(self.lcdNumber)


        self.verticalLayout_4.addLayout(self.horizontalLayout_11)


        self.horizontalLayout.addLayout(self.verticalLayout_4)


        self.gridLayout.addLayout(self.horizontalLayout, 0, 1, 1, 1)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton = QPushButton(self.tab)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout_2.addWidget(self.pushButton)

        self.toolButton_2 = QToolButton(self.tab)
        self.toolButton_2.setObjectName(u"toolButton_2")

        self.horizontalLayout_2.addWidget(self.toolButton_2)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.label_2 = QLabel(self.tab)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_10.addWidget(self.label_2)

        self.lineEdit = QLineEdit(self.tab)
        self.lineEdit.setObjectName(u"lineEdit")

        self.verticalLayout_10.addWidget(self.lineEdit)


        self.horizontalLayout_7.addLayout(self.verticalLayout_10)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.label_6 = QLabel(self.tab)
        self.label_6.setObjectName(u"label_6")

        self.verticalLayout_9.addWidget(self.label_6)

        self.comboBox = QComboBox(self.tab)
        self.comboBox.setObjectName(u"comboBox")

        self.verticalLayout_9.addWidget(self.comboBox)


        self.horizontalLayout_7.addLayout(self.verticalLayout_9)

        self.toolButton_3 = QToolButton(self.tab)
        self.toolButton_3.setObjectName(u"toolButton_3")

        self.horizontalLayout_7.addWidget(self.toolButton_3)


        self.verticalLayout_5.addLayout(self.horizontalLayout_7)

        self.tableView = QTableView(self.tab)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout_5.addWidget(self.tableView)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_2)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.verticalLayout_5.addItem(self.horizontalSpacer)


        self.gridLayout.addLayout(self.verticalLayout_5, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_2 = QVBoxLayout(self.tab_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(self.tab_2)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.listWidget = QListWidget(self.tab_2)
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout_2.addWidget(self.listWidget)

        self.tabWidget.addTab(self.tab_2, "")

        self.verticalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Contato", None))
        self.toolButton.setText(QCoreApplication.translate("MainWindow", u"Adicionar dispositivo", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Aceler\u00f4metro", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Nota", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Sensibilidade (positiva)", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Sensibilidade (negativa)", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"    Gyro:", None))
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"descontato_d*", None))
        self.toolButton_2.setText(QCoreApplication.translate("MainWindow", u"Salvar", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Limiar", None))
        self.lineEdit.setText(QCoreApplication.translate("MainWindow", u"30", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Nota", None))
        self.comboBox.setPlaceholderText(QCoreApplication.translate("MainWindow", u"C3", None))
        self.toolButton_3.setText(QCoreApplication.translate("MainWindow", u"Adicionar", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Dispositivo 1", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Dispositivos no alcance:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Dispositivo 2", None))
    # retranslateUi

