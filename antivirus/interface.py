import curses
import time
from pathlib import Path
BACK_KEY = 27
ENTER_KEY = 10


class Interface():
    def __init__(self, stdscr):
        self.quit = False
        self.stdscr = stdscr
        self.progress = 0
        self.filProgress = 0
        self.cpth = ''
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.curs_set(0)

    def setProgress(self, val, cpth):
        self.progress = val
        self.cpth = cpth
        return self.quit

    def setFilProgress(self, val):
        self.filProgress = val
        return self.quit

    def setQuit(self, val):
        self.quit = val

    def getProg(self):
        return (self.progress, self.filProgress, self.cpth)

    def getScanType(self):
        choices = ['standard scan', 'periodic scan']
        with SimpleChoice(self.stdscr, choices, 'Choose:') as win:
            action = win.get()
        return action

    def getFast(self):
        choices = ['Yes', 'No']
        msg = 'Do you wish to use fast scanning?'
        with SimpleChoice(self.stdscr, choices, msg) as win:
            action = win.get()
        return action

    def getTime(self):
        with TimeMenu(self.stdscr) as win:
            return win.get()

    def getPath(self):
        with PathMenu(self.stdscr) as win:
            action = win.get()
        return action

    def scanWindow(self, scanTh):
        with ScanWin(scanTh, self.stdscr, self.setQuit, self.getProg) as win:
            win.get()
        self.progress = 0
        self.filProgress = 0
        self.cpth = ''

    def displayReport(self, scanner):
        with ReportWin(self.stdscr, scanner) as win:
            win.get()

    def periodicScanMenu(self, path, period, lastOk):
        with PeriodicMenu(self.stdscr, path, period, lastOk) as win:
            return win.get()


class Window():
    def __init__(self, stdscr, actions, legend):
        maxY = stdscr.getmaxyx()[0]
        self.legend = Text(stdscr, 0, maxY-1, legend)
        self.status = Text(stdscr, 0, maxY-1, '')
        self.stdscr = stdscr
        self.actions = actions
        self.items = []

    def getAction(self):
        key = self.stdscr.getch()
        if key in self.actions:
            return self.actions[key]()
        return None

    def setStatus(self, status, color=None):
        if color:
            self.status.color = color
        self.status.text = status

    def draw(self):
        self.stdscr.erase()
        maxY, maxX = self.stdscr.getmaxyx()
        self.status.xLoc = maxX - 1 - len(self.status.text)
        self.status.yLoc = maxY-1
        self.legend.yLoc = maxY-1
        self.status.draw()
        self.legend.draw()
        for item in self.items:
            item.draw()
        self.stdscr.refresh()

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, type, value, traceback):
        raise NotImplementedError


class ChoiceMenu():
    def down(self):
        if self.maxCur == -1:
            return None
        if self.cursor != self.maxCur:
            maxY = self.stdscr.getmaxyx()[0]
            if self.cursor == (maxY+self.drawBegin-self.yLoc-3):
                self.drawBegin += 1
            self.cursor += 1
        return None

    def up(self):
        if self.cursor > 0:
            if self.cursor == self.drawBegin:
                self.drawBegin -= 1
            self.cursor -= 1
        elif self.out and self.cursor == 0:
            self.cursor = -1
            return 'out'
        return None

    def confirm(self):
        self.drawBegin = 0
        ret = self.cursor
        self.cursor = -1
        return ret

    def back(self):
        return 'back'

    def __init__(self, xLoc, yLoc, cStart, options, stdscr, out):
        self.actions = {
            BACK_KEY: self.back,
            curses.KEY_DOWN: self.down,
            curses.KEY_UP: self.up,
            ENTER_KEY: self.confirm
        }
        self.stdscr = stdscr
        self.cursor = cStart
        self.xLoc = xLoc
        self.yLoc = yLoc
        self.maxCur = len(options) - 1
        self.options = options
        self.changeIndex = 0
        self.color = curses.color_pair(2)
        self.out = out
        self.drawBegin = 0

    def draw(self):
        counter = self.drawBegin
        if counter > self.changeIndex:
            self.color = curses.color_pair(0)
        else:
            self.color = curses.color_pair(2)
        maxY = self.stdscr.getmaxyx()[0] - 1
        optLast = maxY+self.drawBegin-(self.yLoc+1)
        for entry in self.options[self.drawBegin:optLast]:
            if counter == self.changeIndex:
                self.color = curses.color_pair(0)
            if len(entry) > 20:
                dEntry = '...'+entry[-17:]
            else:
                dEntry = entry
            if counter == self.cursor:
                self.stdscr.addstr(
                    self.yLoc + counter - self.drawBegin,
                    self.xLoc,
                    dEntry,
                    curses.A_REVERSE
                )
            else:
                self.stdscr.addstr(
                    self.yLoc + counter - self.drawBegin,
                    self.xLoc,
                    dEntry,
                    self.color
                )
            counter += 1


class Text():
    def __init__(self, stdscr, x, y, text):
        self.stdscr = stdscr
        self.text = text
        self.xLoc = x
        self.yLoc = y
        self.color = curses.color_pair(0)

    def draw(self):
        maxX = self.stdscr.getmaxyx()[1]
        if len(self.text) + self.xLoc + 1 > maxX:
            prnt = '...'+self.text[-(maxX-4-self.xLoc):]
        else:
            prnt = self.text
        self.stdscr.addstr(self.yLoc, self.xLoc, prnt, self.color)


class TimeMenu(Window):
    def __init__(self, stdscr):
        self.stdscr = stdscr
        msg = 'Enter time between periodic scans: (hh:mm)'
        self.text = Text(stdscr, 0, 0, msg)
        self.time = TimeField(1, 1, self.stdscr)
        legend = 'ESC: back, ENTER: confirm'
        super().__init__(stdscr, self.time.actions, legend)
        self.items = [self.text, self.time]

    def get(self):
        while True:
            self.draw()
            action = self.getAction()
            if action is not None:
                if action == 'back':
                    return action
                elif action == 'invalid':
                    self.setStatus('Time cannot be 0', curses.color_pair(1))
                    continue
                return int(action[:2])*3600 + int(action[-2:])*60
            else:
                self.setStatus('')

    def getAction(self):
        key = self.stdscr.getch()
        if 47 < key < 58:
            self.actions['input'](key)
            return None
        if key in self.actions:
            return self.actions[key]()
        return None

    def __enter__(self):
        curses.curs_set(1)
        return self

    def __exit__(self, type, value, traceback):
        curses.curs_set(0)
        return False


class PathMenu(Window):
    def getCorrect(self, path):
        parent = path.parent
        if parent.exists():
            return parent
        else:
            return self.getCorrect(parent)

    def getCorrectStr(self, pathStr):
        if pathStr[-1] == '/':
            path = Path(pathStr + 'a')
            search = ''
        else:
            path = Path(pathStr)
            search = path.name
        if path.parent.exists():
            ret = path.parent
            color = curses.color_pair(0)
        else:
            ret = self.getCorrect(path.parent)
            search = ''
            color = curses.color_pair(1)
        length = len(str(ret))
        if length > 1:
            length += 1
        return ret, search, length, color

    def refreshMenu(self, content):
        current, search, length, color = self.getCorrectStr(content)
        sLen = len(search)
        dirNames = []
        fileNames = []
        try:
            d = list(current.iterdir())
        except PermissionError:
            return [], current, length, len(dirNames), color
        except NotADirectoryError:
            return [], current, length, len(dirNames), curses.color_pair(1)
        for entry in d:
            try:
                if entry.name[:sLen] == search:
                    if entry.is_file():
                        fileNames.append(entry.name)
                    elif entry.is_dir():
                        dirNames.append(entry.name)
            except PermissionError:
                pass
        if len(dirNames) + len(fileNames) == 0 and search:
            color = curses.color_pair(1)
            for entry in d:
                try:
                    if entry.is_file():
                        fileNames.append(entry.name)
                    elif entry.is_dir():
                        dirNames.append(entry.name)
                except PermissionError:
                    pass
        dirNames.sort()
        fileNames.sort()
        self.menu.options = (dirNames + fileNames)
        self.menu.maxCur = len(self.menu.options) - 1
        menuLen = max([min(20, len(o)) for o in self.menu.options]+[0])
        disLen = max(menuLen+length, len(content)) + 4
        disLen -= self.stdscr.getmaxyx()[1]
        shift = max(disLen, 0)
        self.content.begin = shift
        self.menu.xLoc = max(0, length-shift)
        self.menu.changeIndex = len(dirNames)
        self.content.color = color

    def confirm(self):
        path = Path(self.content.content)
        if path.exists():
            return path
        else:
            self.content.color = curses.color_pair(1)
            return None

    def fillWith(self, i):
        fixedContent = str(self.getCorrect(Path(self.content.content+"a")))
        if len(fixedContent) != 1:
            fixedContent = fixedContent + '/'
        self.content.content = fixedContent + self.menu.options[i]
        if Path(self.content.content).is_dir():
            self.content.content += '/'
        self.content.cursor = len(self.content.content)

    def fill(self):
        col = self.content.color != curses.color_pair(1)
        con = len(self.menu.options) != 0
        if col and con:
            self.fillWith(0)
            self.refreshMenu(self.content.content)
        return None

    def enterMenu(self):
        if self.menu.maxCur == -1:
            return None
        self.menu.cursor = 0
        curses.curs_set(0)
        self.location = 'menu'
        self.actions = self.menu.actions
        return None

    def leaveMenu(self):
        curses.curs_set(1)
        self.location = 'text'
        self.actions = self.content.actions
        return None

    def __init__(self, stdscr):
        self.objActions = {
            'back': lambda: 'back',
            True: self.confirm,
            'fill': self.fill,
            'menu': self.enterMenu,
            'out': self.leaveMenu
        }
        self.menu = ChoiceMenu(1, 1, -1, [], stdscr, True)
        self.content = PathText(stdscr, 0, 0)
        self.location = 'text'
        legend = 'ESC: back, ENTER: confirm, DOWN: enter menu, TAB: autofill'
        super().__init__(stdscr, self.content.actions, legend)
        self.items = [self.menu, self.content]
        self.refreshMenu('/')

    def getAction(self):
        key = self.stdscr.getch()
        if 177 > key > 40:
            if 'input' in self.actions:
                self.actions['input'](key)
                self.refreshMenu(self.content.content)
                return None
        if key in self.actions:
            act = self.actions[key]()
            if key == curses.KEY_BACKSPACE:
                self.refreshMenu(self.content.content)
            return act
        return None

    def get(self):
        while True:
            self.draw()
            action = self.getAction()
            if action is not None:
                if type(action) is int:
                    self.fillWith(action)
                    self.refreshMenu(self.content.content)
                    self.leaveMenu()
                    continue
                action = self.objActions[action]()
            if action is not None:
                return action

    def __enter__(self):
        curses.curs_set(1)
        return self

    def __exit__(self, type, value, traceback):
        curses.curs_set(0)
        return False


class TimeField():
    def left(self):
        if self.cursor != 0:
            self.cursor -= 1
        return None

    def right(self):
        if self.cursor < 3:
            self.cursor += 1
        return None

    def confirm(self):
        time = ''.join(self.time)
        if time != '00:00':
            return time
        return 'invalid'

    def back(self):
        return 'back'

    def inp(self, key):
        if key < 54 or self.cursor != 2:
            self.time[[0, 1, 3, 4][self.cursor]] = chr(key)
            self.right()
        return None

    def __init__(self, xLoc, yLoc, stdscr):
        self.time = list('00:00')
        self.actions = {
            BACK_KEY: self.back,
            curses.KEY_LEFT: self.left,
            curses.KEY_RIGHT: self.right,
            ENTER_KEY: self.confirm,
            'input': self.inp
        }
        self.stdscr = stdscr
        self.cursor = 0
        self.xLoc = xLoc
        self.yLoc = yLoc

    def draw(self):
        self.stdscr.addstr(self.yLoc, self.xLoc, ''.join(self.time))
        self.stdscr.move(self.yLoc, self.xLoc+[0, 1, 3, 4][self.cursor])


class SimpleChoice(Window):
    def __init__(self, stdscr, options, message):
        self.menu = ChoiceMenu(1, 1, 0, options, stdscr, False)
        self.message = Text(stdscr, 0, 0, message)
        legend = 'ESC: back, ENTER: confirm'
        super().__init__(stdscr, self.menu.actions, legend)
        self.items = [self.menu, self.message]

    def get(self):
        while True:
            self.draw()
            choice = self.getAction()
            if choice is not None:
                return choice

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return False


class PathText():
    def inp(self, key):
        if not(key == ord('/') and self.content[-1] == '/'):
            self.contInsert(chr(key))
            self.cursor += 1
        return None

    def bckspc(self):
        if self.cursor != 1:
            self.content = self.content[:self.cursor - 1] +\
                            self.content[self.cursor:]
            self.cursor -= 1
        return None

    def left(self):
        if self.cursor != max(1, self.begin):
            self.cursor -= 1
            mvX = self.cursor+self.xLoc-self.begin
            self.stdscr.move(self.yLoc, mvX)
        return None

    def right(self):
        if self.cursor != len(self.content):
            self.cursor += 1
            mvX = self.cursor+self.xLoc-self.begin
            self.stdscr.move(self.yLoc, mvX)
        return None

    def down(self):
        return 'menu'

    def tab(self):
        return 'fill'

    def confirm(self):
        return True

    def back(self):
        return 'back'

    def contInsert(self, toInsert):
        self.content = self.content[:self.cursor] +\
                        toInsert +\
                        self.content[self.cursor:]

    def __init__(self, stdscr, x, y):
        self.actions = {
            'input': self.inp,
            curses.KEY_BACKSPACE: self.bckspc,
            curses.KEY_DOWN: self.down,
            curses.KEY_LEFT: self.left,
            curses.KEY_RIGHT: self.right,
            ENTER_KEY: self.confirm,
            9: self.tab,
            BACK_KEY: self.back
        }
        self.color = curses.color_pair(0)
        self.stdscr = stdscr
        self.xLoc = x
        self.yLoc = y
        self.content = '/'
        self.cursor = 1
        self.done = False
        self.begin = 0

    def draw(self):
        prnt = self.content[self.begin:]
        self.stdscr.addstr(self.yLoc, self.xLoc, prnt, self.color)
        self.stdscr.move(self.yLoc, self.cursor+self.xLoc-self.begin)


class ReportText():
    def down(self):
        if self.drawBegin < self.maxBegin:
            self.drawBegin += 1
        return None

    def up(self):
        if self.drawBegin > 0:
            self.drawBegin -= 1
        return None

    def __init__(self, xLoc, yLoc, report, stdscr):
        self.stdscr = stdscr
        self.xLoc = xLoc
        self.yLoc = yLoc
        self.maxBegin = 2
        self.report = report
        self.drawBegin = 0

    def draw(self):
        counter = 0
        maxY, maxX = self.stdscr.getmaxyx()
        self.maxBegin = len(self.report) + 2 - maxY
        maxY -= 1
        optLast = maxY+self.drawBegin-(self.yLoc+1)
        for entry in self.report[self.drawBegin:optLast]:
            if len(entry) > maxX:
                dEntry = '...'+entry[-(maxX-3):]
            else:
                dEntry = entry
            self.stdscr.addstr(
                self.yLoc + counter,
                self.xLoc,
                dEntry
            )
            counter += 1


class PeriodicMenu(Window):
    def scan(self):
        if self.remaining < 1:
            return 'scan'
        return None

    def __init__(self, stdscr, pth, period, last):
        self.path = str(pth)
        self.stdscr = stdscr
        self.scanTime = period + time.time()
        self.remaining = int(self.scanTime-time.time())
        self.pathText = Text(stdscr, 0, 0, f'To scan: {self.path}')
        self.timeText = Text(stdscr, 1, 1, '')
        options = {
            BACK_KEY: lambda: 'back',
            -1: self.scan
        }
        legend = 'ESC: back'
        super().__init__(stdscr, options, legend)
        self.items = [self.pathText, self.timeText]
        if last:
            self.setStatus('Last scan: Ok', curses.color_pair(2))
        elif last is None:
            self.setStatus('scan aborted', curses.color_pair(1))

    def get(self):
        while True:
            self.remaining = int(self.scanTime-time.time())
            self.timeText.text = f'Time to next scan: {self.remaining}s'
            self.draw()
            choice = self.getAction()
            if choice is not None:
                return choice

    def __enter__(self):
        self.stdscr.timeout(30)
        return self

    def __exit__(self, type, value, traceback):
        self.stdscr.timeout(-1)
        return False


class ScanWin(Window):
    def back(self):
        self.setStatus('aborting scan...')
        self.quit(True)

    def __init__(self, scanTh, stdscr, setQuit, getProg):
        self.quit = setQuit
        self.progress = getProg
        self.scanTh = scanTh
        self.scanText = Text(stdscr, 0, 0, '')
        self.progText = Text(stdscr, 0, 1, '')
        legend = 'ESC: abort scan'
        super().__init__(stdscr, {}, legend)
        self.items = [self.scanText, self.progText]

    def get(self):
        while True:
            prog, filProg, cpth = self.progress()
            if cpth:
                self.scanText.text = f'scanning: {cpth} ({filProg}%)'
            else:
                self.scanText.text = 'processing...'
            self.progText.text = f'progress: {prog}%'
            self.draw()
            self.scanTh.join(0.05)
            if self.scanTh.isAlive():
                if self.stdscr.getch() == BACK_KEY:
                    self.back()
            else:
                break

    def __enter__(self):
        self.stdscr.timeout(0)
        return self

    def __exit__(self, type, value, traceback):
        self.stdscr.timeout(-1)
        self.quit(False)
        return False


class ReportWin(Window):
    @staticmethod
    def fromReport(report):
        reportLines = []
        if len(report[0] + report[1]) == 0:
            reportLines.append('No infected files found')
        else:
            reportLines.append('The following files were found infected:')
            for info in (report[0] + report[1]):
                reportLines.append(f'{info[0]} -> {info[1]}')
        if report[2]:
            reportLines.append('Access was denied to the following:')
            for info in report[2]:
                reportLines.append(str(info))
        return reportLines

    def save(self):
        c = 0
        savePath = Path('./scanReports/report.txt')
        while savePath.exists():
            c += 1
            savePath = Path(f'./scanReports/report{c}.txt')
        savePath.write_text('\n'.join(self.text.report))
        self.setStatus(f'saved to report{c}', curses.color_pair(2))

    def fix(self):
        if self.triedFix:
            return None
        self.triedFix = True
        fixed = []
        for toFix in self.fixable:
            if self.scanner.cutOut(toFix):
                fixed.append(str(toFix[0]))
        if fixed:
            self.text.report.append('The following files were fixed:')
            self.text.report.extend(fixed)
            self.setStatus('Fixed successfuly', curses.color_pair(2))
        else:
            self.text.report.append('No files could be fixed')
            self.setStatus('No fixes possible')
        self.text.maxBegin = len(self.text.report) - 1

    def __init__(self, stdscr, scanner):
        self.scanner = scanner
        self.triedFix = False
        rep = scanner.getReport()
        self.fixable = rep[0]
        report = self.fromReport(rep)
        self.text = ReportText(0, 0, report, stdscr)
        actions = {
            curses.KEY_UP: self.text.up,
            curses.KEY_DOWN: self.text.down,
            BACK_KEY: lambda: 'back',
            ord('s'): self.save,
            ord('f'): self.fix
        }
        legend = 'ESC: back, S: save report, F: fix files'
        super().__init__(stdscr, actions, legend)
        self.items = [self.text]
        if scanner.aborted:
            self.setStatus('scan aborted', curses.color_pair(1))

    def get(self):
        while True:
            self.draw()
            action = self.getAction()
            if action is not None:
                return action

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return False


def printCmdResult(report, fixed, denied):
    infected = [f'{info[0]} -> {info[1]}' for info in report[0] + report[1]]
    if infected:
        print('\n'.join(infected))
    if denied:
        if report[2]:
            print('denied access to:')
            print('\n'.join([str(pth) for pth in report[2]]))
    if fixed:
        print('fixed:')
        print('\n'.join(fixed))
