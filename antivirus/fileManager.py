import sigBase
import hashlib
import json
from pathlib import Path


class Scanner():
    def clearDeleted(self):
        files = [Path(path) for path in self.fileIndex.keys]
        toDelete = []
        for path in files:
            if not path.exists():
                toDelete.append(str(path))
        for path in toDelete:
            del self.fileIndex[path]

    def __init__(self, bodySigPath, hashSigPath, callbacks):
        self.aborted = False
        self.callbacks = callbacks
        self.report = ScanReport()
        self._signatures = sigBase.SigBase(bodySigPath, hashSigPath)
        try:
            with open('index.json') as jsonIndex:
                self.fileIndex = json.load(jsonIndex)
        except FileNotFoundError:
            with open('index.json', 'w') as jsonIndex:
                self.fileIndex = {}
                json.dump(self.fileIndex, jsonIndex)

    def updateIndex(self):
        with open('index.json', 'w') as jsonIndex:
            json.dump(self.fileIndex, jsonIndex, indent=4)

    def scanFile(self, toScan, fast):
        strToScan = str(toScan)
        try:
            fileBytes = toScan.read_bytes()
        except PermissionError:
            self.report.addDenied(toScan)
            return
        fileHash = hashlib.md5()
        fileHash.update(fileBytes)
        fileHash = fileHash.hexdigest()
        if fast and strToScan in self.fileIndex:
            fileInfo = self.fileIndex[strToScan]
            if fileInfo[1] == fileHash:
                if fileInfo[0]:
                    if len(fileInfo) == 4:
                        args = toScan, fileInfo[2], fileInfo[3]
                        self.report.addFixable(*args)
                    else:
                        self.report.addUnfixable(toScan, fileInfo[2])
                return
        cbs = None if self.callbacks is None else self.callbacks[1]
        args = (
            fileHash,
            toScan.stat().st_size,
            fileBytes.hex(),
            cbs
        )
        scanResult, resType = self._signatures.scanFile(*args)
        if scanResult is None:
            return
        self.fileIndex[strToScan] = scanResult
        if resType:
            self.report.addFixable(toScan, scanResult[2], scanResult[3])
        if resType is False:
            self.report.addUnfixable(toScan, scanResult[2])

    def findFiles(self, path):
        files = []
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            try:
                directory = list(path.iterdir())
            except PermissionError:
                self.report.addDenied(path)
                return []
            for entry in directory:
                files.extend(self.findFiles(entry))
        return files

    def scan(self, toScan, fast):
        progress = 0
        cpth = ''
        scanList = self.findFiles(toScan)
        fileNum = len(scanList)
        counter = 0
        for filePath in scanList:
            if self.callbacks is not None:
                progress = (100*counter)//fileNum
                cpth = str(filePath)
                if self.callbacks[0](progress, cpth):
                    self.aborted = True
                    return
            self.scanFile(filePath, fast)
            counter += 1
        self.aborted = False

    def cutOut(self, fixableInfo):
        path = fixableInfo[0]
        try:
            fileHex = path.read_bytes().hex()
        except (PermissionError, FileNotFoundError):
            return False
        start, end = fixableInfo[2]
        fixed = bytes.fromhex(fileHex[:start] + fileHex[end:])
        try:
            path.write_bytes(fixed)
        except PermissionError:
            return False
        return True

    def simpleScan(self, toScan, fast):
        self.report.clear()
        self.scan(toScan.resolve(), fast)
        self.updateIndex()

    def getReport(self):
        return self.report.report()


class ScanReport():
    def __init__(self):
        self._denied = []
        self._fixable = []
        self._unfixable = []

    def addDenied(self, path):
        self._denied.append(path)

    def addFixable(self, path, malware, span):
        self._fixable.append((path, malware, span))

    def addUnfixable(self, path, malware):
        self._unfixable.append((path, malware))

    def report(self):
        return (
            self._fixable.copy(),
            self._unfixable.copy(),
            self._denied.copy()
        )

    def clear(self):
        self._denied = []
        self._fixable = []
        self._unfixable = []
