import re


class BodySignature():
    @staticmethod
    def prepStr(sigStr):
        return sigStr.replace('*', '(..)*').replace('?', '.')\
            .replace('-', ',').replace('{', '(..){')

    def __init__(self, name, sig):
        self._signature = re.compile(self.prepStr(sig))
        self.malwareName = name

    def match(self, hexFile):
        return self._signature.search(hexFile)


class HashSignature():
    def __init__(self, name, sig, fileSize):
        self.malwareName = name
        self._signature = sig
        self._fileSize = int(fileSize)

    def getSize(self):
        return self._fileSize

    def match(self, fileHash):
        if self._signature == fileHash:
            return True
        return False


class SigBase():
    @staticmethod
    def getFields(line, fieldIndices):
        fields = line[:-1].split(':')
        return [fields[index] for index in fieldIndices]

    def __init__(self, bodyPath, hashPath):
        self._bodySignatures = []
        self._hashSignatures = []
        with open(bodyPath) as sigFile:
            for line in sigFile:
                self._bodySignatures.append(
                    BodySignature(*self.getFields(line, [0, 3]))
                )
        with open(hashPath) as sigFile:
            for line in sigFile:
                self._hashSignatures.append(
                    HashSignature(*self.getFields(line, [2, 0, 1]))
                )

    def bodySigInFile(self, hexFile, callback):
        lenBase = len(self._bodySignatures)
        count = 0
        for sig in self._bodySignatures:
            if callback is not None:
                if callback((count*100)//lenBase):
                    return False
            match = sig.match(hexFile)
            if match:
                return match, sig.malwareName
            count += 1
        return None

    def fileHashMatch(self, fileHash, fileSize):
        for sig in self._hashSignatures:
            if sig.getSize() == fileSize:
                if sig.match(fileHash):
                    return sig.malwareName
        return None

    def scanFile(self, fileHash, fileSize, hexFile, callback):
        if (match := self.fileHashMatch(fileHash, fileSize)):
            match = match.replace('.', ' ')
            return (True, fileHash, match), False
        elif (match := self.bodySigInFile(hexFile, callback)):
            name = match[1].replace('.', ' ')
            return (True, fileHash, name, match[0].span()), True
        else:
            if match is None:
                return (False, fileHash), None
            else:
                return (None, None)
