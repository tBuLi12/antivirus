import fileManager
from pathlib import Path

bodyPath = './testSignatures/testMain.ndb'
hashPath = './testSignatures/testMain.hdb'
infFile1 = Path('testFiles/infFile1')
infFile2 = Path('testFiles/infFile2')
safeFile1 = Path('testFiles/safeFile1')
safeFile1 = Path('testFiles/safeFile2')

scanner = fileManager.Scanner(bodyPath, hashPath, None)


def test_simpleScanHash():
    scanner.simpleScan(infFile1, False)
    report = scanner.getReport()
    assert (len(report[0]), len(report[2])) == (0, 0)
    assert report[1][0] == (infFile1.resolve(), 'Win Trojan Vecnoit-1')


def test_simpleScanBody():
    scanner.simpleScan(infFile2, False)
    report = scanner.getReport()
    assert (len(report[1]), len(report[2])) == (0, 0)
    assert report[0][0] == (infFile2.resolve(), 'Vbs Tool Svbsvc-1', (4, 36))


def test_simpleScanSafe():
    scanner.simpleScan(safeFile1, False)
    report = scanner.getReport()
    assert (len(report[0]), len(report[2])) == (0, 0)
    assert len(report[1]) == 0


def test_cutOut():
    toCut = Path('testFiles/cut')
    toCut.write_bytes(infFile2.read_bytes())
    scanner.simpleScan(toCut, False)
    report = scanner.getReport()
    assert scanner.cutOut(report[0][0])
    assert toCut.read_bytes().hex() == '2c45b3'
