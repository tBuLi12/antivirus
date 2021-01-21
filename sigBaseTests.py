import sigBase
import hashlib
bodyPath = './testSignatures/testMain.ndb'
hashPath = './testSignatures/testMain.hdb'
bodyTests = [
    '5850c4f4c4f135b2aa4156721392c723b61ab213b7930a1c34',
    '2c45402340264b413c4a34a104b6cc3af5c6b3'
]
bodyTestFails = [
    '5850c4f4c4f135b2aa4156721392c723b61ab213ba1c34',
    '402340264b413c4a34a104b6cc3ac6'
]
signatureBase = sigBase.SigBase(bodyPath, hashPath)


def test_bodySigInFile():

    def callback(prog):
        return False
    match = signatureBase.bodySigInFile(bodyTests[0], callback)
    assert match[0].span() == (0, len(bodyTests[0]))
    assert match[1] == 'Win.Trojan.Vecnoit-1'
    mismatch = signatureBase.bodySigInFile(bodyTestFails[0], callback)
    assert mismatch is None

    match = signatureBase.bodySigInFile(bodyTests[1], callback)
    assert match[0].span() == (4, len(bodyTests[1])-2)
    assert match[1] == 'Vbs.Tool.Svbsvc-1'
    mismatch = signatureBase.bodySigInFile(bodyTestFails[1], callback)
    assert mismatch is None


def test_fileHashMatch():
    testHash = hashlib.md5()
    testHash.update(b'This is a test, so whatever')
    match = signatureBase.fileHashMatch(testHash.hexdigest(), 27)
    assert match == 'Win.Spyware.Bispy-7'
    match = signatureBase.fileHashMatch(testHash.hexdigest(), 127)
    assert match is None
    testHash = hashlib.md5()
    testHash.update(b'That should fail')
    match = signatureBase.fileHashMatch(testHash.hexdigest(), 27)
    assert match is None


def test_scanFile():

    def callback(prog):
        return False
    testHash = hashlib.md5()
    testHash.update(bytes.fromhex(bodyTests[0]))
    testHash = testHash.hexdigest()
    args = (testHash, 25, bodyTests[0], callback)
    scanResult, resType = signatureBase.scanFile(*args)
    assert resType is False
    assert scanResult == (True, testHash, 'Win Trojan Vecnoit-1')

    testHash = hashlib.md5()
    testHash.update(bytes.fromhex(bodyTests[1]))
    testHash = testHash.hexdigest()
    args = (testHash, 38, bodyTests[1], callback)
    scanResult, resType = signatureBase.scanFile(*args)
    assert resType is True
    assert scanResult == (
        True,
        testHash,
        'Vbs Tool Svbsvc-1',
        (4, len(bodyTests[1])-2)
    )

    testHash = hashlib.md5()
    testHash.update(bytes.fromhex(bodyTestFails[0]))
    testHash = testHash.hexdigest()
    args = (testHash, 46, bodyTestFails[0], callback)
    scanResult, resType = signatureBase.scanFile(*args)
    assert resType is None
    assert scanResult == (False, testHash)

    scanResult, resType = signatureBase.scanFile(
        testHash,
        46,
        bodyTestFails[0],
        lambda x: True
    )
    assert resType is None
    assert scanResult is None
