import fileManager
import interface
import sys
import argparse
from pathlib import Path
from curses import wrapper
import threading
bodyPath = 'signatures/main.ndb'
hashPath = 'signatures/main.hdb'


class ScanThread(threading.Thread):
    def __init__(self, scanner, toScan, fast):
        threading.Thread.__init__(self)
        self.scanner = scanner
        self.toScan = toScan
        self.fast = fast

    def run(self):
        self.scanner.simpleScan(self.toScan, self.fast)


def main(arguments):
    if len(arguments) == 0:
        wrapper(interactiveMain)
    else:
        cmdMain(arguments)


def cmdMain(arguments):
    scanner = fileManager.Scanner(bodyPath, hashPath, None)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path',
        help='path to the file or directory to be scanned'
    )
    parser.add_argument(
        '-slow',
        action='store_true',
        help='scan all files, not just new, unscanned or changed files'
    )
    parser.add_argument(
        '-cut',
        action='store_true',
        help='cut out the malware from infected files, if possible'
    )
    parser.add_argument(
        '-denied',
        action='store_true',
        help='print the files/directories to which access was denied'
    )
    args = parser.parse_args(arguments)
    path = Path(args.path)
    if not path.exists():
        print('Path invalid')
        return
    scanner.simpleScan(path, not args.slow)
    report = scanner.getReport()
    if args.cut:
        fixed = []
        for fixable in report[0]:
            if scanner.cutOut(fixable):
                fixed.append(str(fixable[0]))
    else:
        fixed = None
    interface.printCmdResult(report, fixed, args.denied)


def interactiveMain(stdscr):
    ui = interface.Interface(stdscr)
    scanner = fileManager.Scanner(
        bodyPath,
        hashPath,
        (ui.setProgress, ui.setFilProgress)
    )
    while True:
        scanType = ui.getScanType()
        if scanType == 'quit':
            return
        elif scanType == 0:
            path = ui.getPath()
            if path == 'back':
                continue
            else:
                fast = ui.getFast()
                if fast == 'quit':
                    continue
                scanTh = ScanThread(scanner, path, not fast)
                scanTh.start()
                ui.scanWindow(scanTh)
                report = scanner.getReport()
                ui.displayReport(report, scanner)
                continue
        else:
            path = ui.getPath()
            if path == 'back':
                continue
            else:
                time = ui.getTime()
                if time == 'back':
                    continue
                while True:
                    act = ui.periodicScanMenu(path, time)
                    if act == 'back':
                        break
                    scanTh = ScanThread(scanner, path, True)
                    scanTh.start()
                    ui.scanWindow(scanTh)
                    report = scanner.getReport()
                    if len(report[0] + report[1]) != 0:
                        ui.displayReport(report, scanner)
                    else:
                        ui.status = 'Last scan: ok'
                ui.status = ''


if __name__ == '__main__':
    main(sys.argv[1:])
