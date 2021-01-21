import os

expectedOut = [
    '/mnt/c/Users/Jeremi/Desktop/anti/testFiles/scanTest/ba.txt -> Win Test EICAR_HDB-1\n',
    '\n'.join([
        '/mnt/c/Users/Jeremi/Desktop/anti/testFiles/scanTest/ba.txt -> Win Test EICAR_HDB-1',
        'denied access to:',
        '/mnt/c/Users/Jeremi/Desktop/anti/testFiles/scanTest/hyh',
        '/mnt/c/Users/Jeremi/Desktop/anti/testFiles/scanTest/ttt.txt\n',
    ])
]


def test_cmdScan():
    stream = os.popen('python3 antivirus.py testFiles/scanTest')
    assert stream.read() == expectedOut[0]


def test_cmdScanDenied():
    stream = os.popen('python3 antivirus.py testFiles/scanTest -denied')
    assert stream.read() == expectedOut[1]
