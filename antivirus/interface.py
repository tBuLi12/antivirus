import curses
import time
from pathlib import Path


class Interface():
    def getDirOpt(self, content):
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
        return (dirNames + fileNames), current, length, len(dirNames), color

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

    def __init__(self, stdscr):
        self.quit = False
        self.stdscr = stdscr
        self.progress = 0
        self.filProgress = 0
        self.cpth = ''
        self.status = ''
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

    def drawLegend(self, legend):
        maxY, maxX = self.stdscr.getmaxyx()
        self.stdscr.addstr(
            maxY-1,
            0,
            '  '.join(legend)
        )
        if self.status:
            self.stdscr.addstr(
                maxY-1,
                maxX-1-len(self.status),
                self.status,
                curses.color_pair(2)
            )

    def getScanType(self):
        choices = ['standard scan', 'periodic scan']
        menu = ChoiceMenu(2, 1, 0, choices, self.stdscr, False)
        while True:
            self.stdscr.erase()
            self.stdscr.addstr(0, 0, 'Choose:')
            menu.draw()
            self.drawLegend([
                'ESC - quit',
                'ENTER - select'
            ])
            self.stdscr.refresh()
            choice = menu.get()
            if choice is not None:
                return choice

    def getFast(self):
        menu = ChoiceMenu(2, 1, 0, ['Yes', 'No'], self.stdscr, False)
        while True:
            self.stdscr.erase()
            self.stdscr.addstr(0, 0, 'Do you wish to use fast scanning?')
            menu.draw()
            self.drawLegend([
                'ESC - back',
                'ENTER - select'
            ])
            self.stdscr.refresh()
            choice = menu.get()
            if choice is not None:
                return choice

    def getTime(self):
        nextRed = False
        color = curses.color_pair(0)
        scanTime = list('00:00')
        curses.curs_set(1)
        cursor = 0
        curLocs = [0, 1, 3, 4]
        while True:
            self.stdscr.erase()
            self.drawLegend([
                'ESC - back',
                'ENTER - confirm'
            ])
            msg = 'Enter time between periodic scans: (hh:mm)'
            self.stdscr.addstr(0, 0, msg)
            if nextRed:
                color = curses.color_pair(1)
                nextRed = False
            self.stdscr.addstr(1, 0, ''.join(scanTime), color)
            color = curses.color_pair(0)
            self.stdscr.move(1, curLocs[cursor])
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if 47 < key < 58:
                if cursor == 2 and key > 53:
                    continue
                scanTime[curLocs[cursor]] = chr(key)
                if cursor < 3:
                    cursor += 1
                continue
            if key == curses.KEY_LEFT:
                if cursor > 0:
                    cursor -= 1
                continue
            if key == curses.KEY_RIGHT:
                if cursor < 3:
                    cursor += 1
                continue
            if key in (curses.KEY_ENTER, 10, 13):
                scanTime = ''.join(scanTime)
                ret = int(scanTime[:2])*3600 + int(scanTime[-2:])*60
                if ret != 0:
                    curses.curs_set(0)
                    return ret
                nextRed = True
                scanTime = list('00:00')
            if key == 27:
                curses.curs_set(0)
                return 'back'

    def getPath(self):
        nextRed = False
        inText = True
        menu = ChoiceMenu(0, 2, -1, [], self.stdscr, True)
        curses.curs_set(1)
        text = PathTyper(0, 1, self.stdscr)
        color = curses.color_pair(0)
        shift = 0
        while True:
            if inText:
                opts = self.getDirOpt(text.content)
                options, current, length, chInd, color = opts
                menuLen = max([min(20, len(o)) for o in options]+[0])
                disLen = max(menuLen+length, len(text.content)) + 4
                disLen -= self.stdscr.getmaxyx()[1]
                shift = max(disLen, 0)
                text.begin = shift
                menu.options = options
                menu.maxCur = len(options) - 1
                menu.xLoc = length-shift
                menu.changeIndex = chInd
            self.stdscr.erase()
            self.stdscr.addstr(0, 0, 'Enter path here:')
            self.drawLegend([
                'ESC - back',
                'ENTER - confirm',
                'DOWN - enter menu'
            ])
            menu.draw()
            if nextRed:
                text.draw(curses.color_pair(1))
                nextRed = False
            else:
                text.draw(color)
            self.stdscr.refresh()
            if inText:
                stat = text.getstr()
                if stat is not None:
                    if stat == 'back':
                        curses.curs_set(0)
                        return stat
                    elif stat == 'fill':
                        curStr = str(current)
                        if len(curStr) == 1:
                            text.content = '/'+menu.options[0]
                        else:
                            text.content = curStr+'/'+menu.options[0]
                        if Path(text.content).is_dir():
                            text.content += '/'
                        text.cursor = len(text.content)
                        continue
                    elif stat == 'menu':
                        if menu.maxCur == -1:
                            continue
                        menu.cursor = 0
                        curses.curs_set(0)
                        inText = False
                        continue
                    path = Path(text.content)
                    if path.exists():
                        curses.curs_set(0)
                        return path
                    else:
                        nextRed = True
            else:
                menuStat = menu.get()
                if menuStat is not None:
                    if type(menuStat) == int:
                        curStr = str(current)
                        if len(curStr) == 1:
                            text.content = '/'+menu.options[menuStat]
                        else:
                            text.content = curStr+'/'+menu.options[menuStat]
                        if Path(text.content).is_dir():
                            text.content += '/'
                        text.cursor = len(text.content)
                        curses.curs_set(1)
                        inText = True
                    if menuStat == 'out':
                        curses.curs_set(1)
                        inText = True
                    if menuStat == 'quit':
                        return 'back'

    def scanWindow(self, scanTh):
        self.stdscr.timeout(0)
        while True:
            self.stdscr.erase()
            msg = f'scanning:{self.cpth} ({self.filProgress}%)'
            self.stdscr.addstr(0, 0, msg)
            self.stdscr.addstr(1, 0, f'{self.progress}% done')
            self.drawLegend([
                'ESC - abort scan'
            ])
            self.stdscr.refresh()
            scanTh.join(0.05)
            if scanTh.isAlive():
                key = self.stdscr.getch()
                if key == 27:
                    self.quit = True
            else:
                self.stdscr.timeout(-1)
                self.quit = False
                self.progress = 0
                break

    def displayReport(self, report, scanner):
        triedFix = False
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
        drawBegin = 0
        lRep = len(reportLines)
        while True:
            self.stdscr.erase()
            counter = 0
            space, maxX = self.stdscr.getmaxyx()
            space -= 3
            for line in reportLines[drawBegin:drawBegin+space]:
                if len(line) > maxX:
                    dLine = '...'+line[-(maxX-3):]
                else:
                    dLine = line
                self.stdscr.addstr(counter, 0, dLine)
                counter += 1
            self.drawLegend([
                'ESC - back',
                'S - save report',
                'F - fix infexted files'
            ])
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == curses.KEY_DOWN:
                if drawBegin+space < lRep:
                    drawBegin += 1
                continue
            if key == curses.KEY_UP:
                if drawBegin > 0:
                    drawBegin -= 1
                continue
            if key == 27:
                self.status = ''
                break
            if key == ord('s'):
                c = 0
                savePath = Path('./scanReports/report.txt')
                while savePath.exists():
                    c += 1
                    savePath = Path(f'./scanReports/report{c}.txt')
                savePath.write_text('\n'.join(reportLines))
                self.status = f'Saved to {savePath.name}'
            if key == ord('f'):
                if triedFix:
                    continue
                triedFix = True
                fixed = []
                for fixable in report[0]:
                    if scanner.cutOut(fixable):
                        fixed.append(str(fixable[0]))
                if fixed:
                    reportLines.append('The following files were fixed:')
                    reportLines.extend(fixed)
                else:
                    reportLines.append('No files could be fixed')
                lRep = len(reportLines)

    def periodicScanMenu(self, path, period):
        self.stdscr.timeout(30)
        scanTime = period + time.time()
        while True:
            remaining = int(scanTime-time.time())
            if remaining < 1:
                self.stdscr.timeout(-1)
                return 'scan'
            self.stdscr.erase()
            self.drawLegend([
                'ESC - back'
            ])
            pathStr = str(path)
            maxL = self.stdscr.getmaxyx()[1]-9
            if len(str(path)) > maxL:
                pathStr = '...'+pathStr[-(maxL-3):]
            self.stdscr.addstr(0, 0, f'To scan: {pathStr}')
            self.stdscr.addstr(1, 0, f'Time to next scan: {remaining}s')
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key == 27:
                self.stdscr.timeout(-1)
                return 'back'


class ChoiceMenu():
    def __init__(self, xLoc, yLoc, cStart, options, stdscr, out):
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

    def get(self):
        while True:
            key = self.stdscr.getch()
            if key == curses.KEY_DOWN:
                if self.maxCur == -1:
                    continue
                if self.cursor != self.maxCur:
                    maxX = self.stdscr.getmaxyx()[0]
                    if self.cursor == (maxX+self.drawBegin-self.yLoc-3):
                        self.drawBegin += 1
                    self.cursor += 1
                return None
            elif key == curses.KEY_UP:
                if self.cursor > 0:
                    if self.cursor == self.drawBegin:
                        self.drawBegin -= 1
                    self.cursor -= 1
                elif self.out and self.cursor == 0:
                    self.cursor = -1
                    return 'out'
                return None
            elif key in (curses.KEY_ENTER, 10, 13):
                self.drawBegin = 0
                ret = self.cursor
                self.cursor = -1
                return ret
            elif key == 27:
                return 'quit'


class PathTyper():
    def contInsert(self, toInsert):
        self.content = self.content[:self.cursor] +\
                        toInsert +\
                        self.content[self.cursor:]

    def __init__(self, x, y, stdscr):
        self.stdscr = stdscr
        self.xLoc = x
        self.yLoc = y
        self.content = '/'
        self.cursor = 1
        self.done = False
        self.begin = 0

    def draw(self, color):
        prnt = self.content[self.begin:]
        self.stdscr.addstr(self.yLoc, self.xLoc, prnt, color)
        self.stdscr.move(self.yLoc, self.cursor+self.xLoc-self.begin)

    def getstr(self):
        while True:
            key = self.stdscr.getch()
            if 177 > key > 40:
                if key == ord('/') and self.content[-1] == '/':
                    continue
                self.contInsert(chr(key))
                self.cursor += 1
                return None
            elif key == curses.KEY_BACKSPACE:
                if self.cursor != 1:
                    self.content = self.content[:self.cursor - 1] +\
                                    self.content[self.cursor:]
                    self.cursor -= 1
                    return None
            elif key == curses.KEY_LEFT:
                if self.cursor != max(1, self.begin):
                    self.cursor -= 1
                    mvX = self.cursor+self.xLoc-self.begin
                    self.stdscr.move(self.yLoc, mvX)
            elif key == curses.KEY_RIGHT:
                if self.cursor != len(self.content):
                    self.cursor += 1
                    mvX = self.cursor+self.xLoc-self.begin
                    self.stdscr.move(self.yLoc, mvX)
            elif key == curses.KEY_DOWN:
                return 'menu'
            elif key == 9:
                return 'fill'
            elif key in (curses.KEY_ENTER, 10, 13):
                return True
            elif key == 27:
                return 'back'


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
