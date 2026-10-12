import sys
import re
import os
import subprocess
import logging
import time


from pathlib import Path
from functools import partial

from PySide2 import QtGui, QtWidgets
from ui_NukeFixer import *
from ui_images_rc import *


class MainWindow(QtWidgets.QMainWindow, Ui_NukeFixer):
    
    def __init__(self, parent = None):
        super().__init__()
        
        self.ui = Ui_NukeFixer()
        self.ui.setupUi(self)
        ui_images_rc.qInitResources()
        self.resize(1400, 300)

        print('-> init')

        # data structs
        self.found_versions = None
        self.filtered_versions = None

        # gui
        self.search_start = None
        self.only_if_contains = None
        self.search_for = None
        self.regex = None
        self.apply_first = None
        self.apply_last = None
        self.apply_all = None
        self.select_all_none = None
        self.python_script = None
        self.select_all_none = None
        self.nuke_executable = None

        self.column_titles = ['Path', 'Open', 'Apply']
        self.user_stopped = False


        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            #self.application_path = sys._MEIPASS.replace('\\', '/')
            self.application_path = os.path.dirname(
                sys.executable).replace('\\', '/')
        else:
            self.application_path = os.path.dirname(
                os.path.abspath(__file__)).replace('\\', '/')

        # settings
        prefs_pth = self.application_path + '\\settings.ini'
        print('-> init prefs')
        print('-> prefs: ' + prefs_pth)
        self.settings = QtCore.QSettings(prefs_pth, QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)    # File only
        try:
            self.settings_read()
        except:
            print('-> Failed to read preferences.')
            try:
                self.settings_set_defaults()
                self.settings_write()
                self.settings_read()
            except:
                print('-> Failed to write preferences.')

        # -------------------------------------------------------------------
        # signals
        # path
        self.ui.search_start.textChanged.connect(self.search_changed)
        self.ui.browse.clicked.connect(self.get_folder)
        # search
        self.ui.only_if_contains.textChanged.connect(
            self.search_changed)
        self.ui.search_for.textChanged.connect(self.search_changed)
        # versions
        self.ui.version_regex.textChanged.connect(
            self.versions_changed)
        self.ui.apply_first.clicked.connect(self.versions_changed)
        self.ui.apply_last.clicked.connect(self.versions_changed)
        self.ui.apply_all.clicked.connect(self.versions_changed)
        # all
        self.ui.select_all_none.clicked.connect(self.all_on_off)
        # go
        self.ui.execute.clicked.connect(self.go)
        # quit
        exit = QAction(self)

        self.stop_short = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+.'), self)
        self.stop_short.activated.connect(self.user_stop)

        logging.basicConfig(
            filename=os.path.join(self.application_path, 'NukeFixer.log')
            .replace('\\', '/'), level=logging.DEBUG)
        logging.info('Started at: ' + time.strftime("%Y-%m-%d, %H:%M"))

    def settings_set_defaults(self):
        print('-> settings_set_defaults')

        self.settings.setValue('search_start', 'C:/projects/ProjectMeridian')
        self.settings.setValue('only_if_contains', '/work/comp/')
        self.settings.setValue('search_for', '_comp_v???.nk')
        self.settings.setValue('version_regex', '.*_v(\d{3}).nk')
        self.settings.setValue('apply_all', False)
        self.settings.setValue('apply_first', False)
        self.settings.setValue('apply_last', True)
        self.settings.setValue('select_all_none', True)
        self.settings.setValue('python_script', "")
        self.settings.setValue('nuke_executable',
                               'C:/Program Files/Nuke13.2v4/Nuke13.2.exe')


    def settings_write(self):
        """
        Write display settings to file
        """
        print('-> settings_write')

        self.settings.setValue('search_start',
                               self.ui.search_start.displayText())
        self.settings.setValue('only_if_contains',
                               self.ui.only_if_contains.displayText())
        self.settings.setValue('search_for', self.ui.search_for.displayText())
        self.settings.setValue('apply_first',
                               int(self.ui.apply_first.isChecked()))
        self.settings.setValue('apply_last',
                               int(self.ui.apply_last.isChecked()))
        self.settings.setValue('apply_all',
                               int(self.ui.apply_all.isChecked()))
        self.settings.setValue('version_regex',
                               self.ui.version_regex.displayText())
        self.settings.setValue('select_all_none',
                               int(self.ui.select_all_none.isChecked()))
        self.settings.setValue('python_script',
                               self.ui.python_script.toPlainText())
        self.settings.setValue('nuke_executable',
                               self.ui.nuke_executable.displayText())

    def settings_read(self):
        """
        Read settings from file
        """
        print('-> settings_read')
        self.ui.search_start.blockSignals(True)
        self.ui.search_start.setText(self.settings.value('search_start'))
        self.ui.search_start.blockSignals(False)

        self.ui.only_if_contains.blockSignals(True)
        self.ui.only_if_contains.setText(self.settings.value('only_if_contains'))
        self.ui.only_if_contains.blockSignals(False)

        self.ui.search_for.blockSignals(True)
        self.ui.search_for.setText(self.settings.value('search_for'))
        self.ui.search_for.blockSignals(False)

        self.ui.search_for.blockSignals(True)
        self.ui.version_regex.setText(self.settings.value('version_regex'))
        self.ui.search_for.blockSignals(False)

        self.ui.apply_first.blockSignals(True)
        self.ui.apply_first.setChecked(int(self.settings.value('apply_first')))
        self.ui.apply_first.blockSignals(False)

        self.ui.apply_last.blockSignals(True)
        self.ui.apply_last.setChecked(int(self.settings.value('apply_last')))
        self.ui.apply_last.blockSignals(False)

        self.ui.apply_all.blockSignals(True)
        self.ui.apply_all.setChecked(int(self.settings.value('apply_all')))
        self.ui.apply_all.blockSignals(False)

        self.ui.select_all_none.blockSignals(True)
        self.ui.select_all_none.setChecked(int(self.settings.value('select_all_none')))
        self.ui.select_all_none.blockSignals(False)

        self.ui.python_script.blockSignals(True)
        self.ui.python_script.setPlainText(
            str(self.settings.value('python_script')))
        self.ui.python_script.blockSignals(False)

        self.ui.nuke_executable.blockSignals(True)
        self.ui.nuke_executable.setText(self.settings.value('nuke_executable'))
        self.ui.nuke_executable.blockSignals(False)

        self.search_start = str(self.ui.search_start.displayText()).replace('\\', '/')
        self.only_if_contains = str(self.ui.only_if_contains.displayText()).replace('\\', '/')
        self.search_for = str(self.ui.search_for.displayText()).replace('\\', '/')
        self.regex = str(self.ui.version_regex.displayText())
        self.apply_first = int(self.ui.apply_first.isChecked())
        self.apply_last = int(self.ui.apply_last.isChecked())
        self.apply_all = int(self.ui.apply_all.isChecked())
        self.python_script = str(self.ui.python_script.toPlainText())
        self.nuke_executable = str(self.ui.nuke_executable.displayText()).replace('\\', '/')

    def closeEvent(self, event):
        self.settings_write()
        #Quitting application
        event.accept()

    def get_folder(self):
        file_name = QFileDialog.getExistingDirectory(
            self,
            "Select Starting Folder",
            str(self.ui.search_start.displayText())
        )
        fldr = os.path.realpath(file_name).replace('\\', '/')
        self.ui.search_start.setText(fldr)
        self.search_changed()

    def search_changed(self):
        self.search_start = str(self.ui.search_start.displayText()).replace('\\', '/')
        self.only_if_contains = str(self.ui.only_if_contains.displayText()).replace('\\', '/')
        self.search_for = str(self.ui.search_for.displayText()).replace('\\', '/')
        self.regex = str(self.ui.version_regex.displayText())
        self.apply_first = int(self.ui.apply_first.isChecked())
        self.apply_last = int(self.ui.apply_last.isChecked())
        self.apply_all = int(self.ui.apply_all.isChecked())
        self.python_script = str(self.ui.python_script.toPlainText())
        self.nuke_executable = str(
            self.ui.nuke_executable.displayText()).replace('\\', '/')

        # after search, select all
        self.ui.select_all_none.setChecked(True)
        self.select_all_none = True

        # get versions
        self.find_versions()
        self.filter_versions()
        self.display_table()


    def versions_changed(self):
        self.search_start = str(self.ui.search_start.displayText()).replace('\\', '/')
        self.only_if_contains = str(self.ui.only_if_contains.displayText()).replace('\\', '/')
        self.search_for = str(self.ui.search_for.displayText()).replace('\\', '/')
        self.regex = str(self.ui.version_regex.displayText())
        self.apply_first = int(self.ui.apply_first.isChecked())
        self.apply_last = int(self.ui.apply_last.isChecked())
        self.apply_all = int(self.ui.apply_all.isChecked())
        self.select_all_none = bool(int(self.ui.select_all_none.isChecked()))
        self.nuke_executable = str(
            self.ui.nuke_executable.displayText()).replace('\\', '/')

        # get versions
        self.filter_versions()
        self.display_table()

    def explore_shot_from_table(self, row, column):
        self.explore(self.filtered_versions[row]['full'])

    def explore(self, path):

        logging.debug('-> explore')

        platform = 'win'
        if sys.platform.startswith('darwin'):
            platform = 'mac'
        elif str(os.name).startswith('posix'):
            platform = 'nix'

        if path and path != '' and os.path.exists(path):
            if platform == 'win':
                if os.path.isdir(path):
                    path = path + '/'
                subprocess.Popen('explorer /root,  \"' + path.replace('/', '\\') + '\"')
            if platform == 'mac':
                subprocess.call(['open', "-R", path])
            if platform == 'nix':
                subprocess.call(('xdg-open', path))

    def find_versions(self):
        lst = {}
        for path in Path(self.search_start).rglob(self.search_for):
            _pth = str(path).replace('\\', '/')
            if self.only_if_contains in _pth:
                try:
                    _splitted = _pth.split('/')
                    if _splitted:
                        _last = str(_splitted[-1])
                        _start = str('/'.join(_splitted[:-1]))
                        if lst.get(_start):
                            # add to the list of subfolders
                            lst[_start].append(_last)
                        else:
                            # first subfolder
                            lst[_start] = [_last]
                except:
                    pass
        # sort versions
        for k, v in lst.items():
            vs = sorted(v)
            lst[k] = vs
        self.found_versions = lst

    def filter_versions(self):

        try:
            self.regex_compiled = re.compile(self.regex)
            regex_valid = True
        except re.error:
            regex_valid = False

        self.filtered_versions = []
        if self.found_versions is not None:
            for one_path, file_list in self.found_versions.items():

                one_folder = []
                for one_file in file_list:
                    my_dict = {}
                    m = self.regex_compiled.search(one_file)
                    if m:
                        try:
                            # if user made a group
                            version = m.group(1)
                            my_dict = {
                                'path': one_path,
                                'file': one_file,
                                'version': version,
                                'full': one_path + '/' + one_file,
                                'apply': True
                            }
                            one_folder.append(my_dict)
                        except:
                            pass
                #sort folder
                folder_sorted = sorted(one_folder, key=lambda i: i['version'])
                if bool(self.apply_first):
                    self.filtered_versions.append(folder_sorted[0])
                elif bool(self.apply_last):
                    self.filtered_versions.append(folder_sorted[-1])
                else:
                    # add all
                    for one in folder_sorted:
                        self.filtered_versions.append(one)

    def all_on_off(self):
        self.select_all_none = bool(int(self.ui.select_all_none.isChecked()))
        for one_row in self.filtered_versions:
            one_row['apply'] = self.select_all_none
        self.display_table()

    def handle_apply(self, row, column):
        _apply = bool(self.filtered_versions[row]['apply'])
        if _apply:
            self.filtered_versions[row]['apply'] = False
        else:
            self.filtered_versions[row]['apply'] = True
        self.display_table()

    def display_table(self):

        # display table
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setColumnCount(0)
        self.ui.tableWidget.setRowCount(0)

        if self.filtered_versions and self.column_titles:
            self.ui.tableWidget.setSortingEnabled(False)
            self.ui.tableWidget.setColumnCount(len(self.column_titles))
            self.ui.tableWidget.setHorizontalHeaderLabels(self.column_titles)
            self.ui.tableWidget.setRowCount(len(self.filtered_versions))

            for row, line in enumerate(self.filtered_versions):
                # set row color by check list
                color = 'white'

                # for every column in a row
                for column_number, one_column in enumerate(self.column_titles):
                    my_title = str(one_column).lstrip().rstrip().lower()

                    if my_title == 'open':
                        btn = QtWidgets.QPushButton('Open', self)
                        btn.setIcon(QtGui.QIcon(":/images/system-search.png"))
                        index = QtCore.QPersistentModelIndex(self.ui.tableWidget.model().index(row, column_number))

                        # partial instead of lambda!
                        btn.clicked.connect(partial(self.explore_shot_from_table, index.row(), index.column()))
                        self.ui.tableWidget.setCellWidget(row, column_number, btn)
                    elif my_title == 'apply':
                        chbx = QtWidgets.QCheckBox('Apply ', self)
                        chbx.setChecked(line['apply'])
                        index = QtCore.QPersistentModelIndex(self.ui.tableWidget.model().index(row, column_number))
                        # partial instead of lambda!
                        chbx.clicked.connect(partial(self.handle_apply, index.row(), index.column()))
                        self.ui.tableWidget.setCellWidget(row, column_number, chbx)
                    elif my_title == 'path':
                        self.ui.tableWidget.setItem(row, column_number,
                                                    QtWidgets.QTableWidgetItem(
                                                        str(line['full'])))
                    else:
                        logging.error("Can't display table row")

                    # colorize cell
                    itm = self.ui.tableWidget.item(row, column_number)
                    if itm:
                        if color == 'green':
                            itm.setBackground(QtGui.QColor('darkgreen'))
                        elif color == 'orange':
                            itm.setBackground(QtGui.QColor('sienna'))
                        elif color == 'red':
                            itm.setBackground(QtGui.QColor('maroon'))
                        elif color == 'purple':
                            itm.setBackground(QtGui.QColor('purple'))
                        else:
                            # white
                            itm.setBackground(QtGui.QColor("#4d4d4d"))

            self.ui.tableWidget.setSortingEnabled(True)
            self.ui.tableWidget.resizeColumnsToContents()
            self.ui.tableWidget.resizeRowsToContents()

    def apply(self, nuke_root_name):

        print("-> Applying to Nuke script {}".format(nuke_root_name))
        self.nuke_executable = str(
            self.ui.nuke_executable.displayText()).replace('\\', '/')
        py_pth = self.application_path + '/scripts/nuke_run.py'

        command = [self.nuke_executable, '-q', '--pause', '-ti', py_pth, nuke_root_name]

        print(command)
        exe = subprocess.Popen(command)

    def go(self):
        total = 0
        files = []
        for one in self.filtered_versions:
            if one['apply']:
                total += 1
                files.append(one['full'])
        total_versions = len(self.filtered_versions)
        
        _go = False
        button = QtWidgets.QMessageBox.question(
            self, "Do or don't, there is no try!",
            "Are you sure to apply python script to {} Nuke scripts?".format(total))
        if button == QtWidgets.QMessageBox.Yes:
            _go = True
        if _go:

            # write Python path to file
            py_pth = self.application_path + '/scripts/runme.py'
            self.python_script = str(self.ui.python_script.toPlainText())
            with open(py_pth, 'w') as my_file:
                my_file.write(self.python_script)
            self.python_script_file = os.path.abspath(os.path.dirname(py_pth))
            sys.path.append(self.python_script_file)

            logging.info('Processing started at: ' + time.strftime("%Y-%m-%d, %H:%M"))
            cnt = 1
            go_time = time.time()
            self.ui.execute.setText('Processing ' + str(total) + ' scripts')
            self.ui.execute.setEnabled(False)
            for row, line in enumerate(self.filtered_versions):
                QApplication.processEvents()
                if self.user_stopped:
                    print("Breaking")
                    break

                if bool(line['apply']):
                    start_time = time.time()
                    self.ui.tableWidget.item(row, 0).setBackground(QtGui.QColor('darkgreen'))
                    self.ui.tableWidget.repaint()
                    logging.info(line['full'])

                    # apply
                    self.apply(line['full'])

                    last_apply_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time))
                    elapsed_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - go_time))
                    average = float(time.time() - go_time) / float(cnt)
                    time_needed = time.strftime("%H:%M:%S", time.gmtime((total - cnt) * average))
                    status = "Just Processed file {}/{}: {}.Last apply time: {}, elapsed time: {}, estimated time: {}".format(cnt, total, line['file'], last_apply_time, elapsed_time, time_needed)
                    self.ui.execute.setText(status)
                    logging.info(status)
                    cnt += 1

                    # uncheck apply for item that is done
                    self.handle_apply(row, 0)

            # Change back to ready
            self.ui.execute.setText('Execute')
            self.ui.execute.setEnabled(True)

    def user_stop(self):
        QApplication.processEvents()
        self.user_stopped = True
        print("-> User Stop!")
        QApplication.processEvents()


if __name__ == "__main__":                
    app = QtWidgets.QApplication(sys.argv)

    app.setStyle("Plastique") # Vista tablewidget header backgroundcolor bug workaround
    # This workaround is need as QApplication can only have 1 instance, at all times, and PySide will not release the
    # object when the window closes (PySide claims this is 'feature', not a bug, so does not need fixing.)
    app=app.instance() # checks if QApplication already exists
    if not app: # create QApplication if it doesnt exist
        app = QtWidgets.QApplication([])
    
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
