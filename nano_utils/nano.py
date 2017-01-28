from ledgerblue.comm import getDongle
from ledgerblue.commException import CommException
from pycoin.key.BIP32Node import BIP32Node
from pycoin.key import Key
from pycoin import encoding
import struct
import hid
import time
from functools import wraps


key_part_priv_key = 1
key_part_pub_key = 2
key_part_chaincode = 4

def parse_bip32_path(path):
    result = b''
    elements = path.split('/')
    for pathElement in elements:
        element = pathElement.split('\'')
        if len(element) == 1:
            result = result + struct.pack("<I", int(element[0]))  # little endian! why they've used big endian and converted in main.c???
        else:
            result = result + struct.pack("<I", 0x80000000 | int(element[0]))
    return result, len(elements)


def nano_get_key(path, key_mask, debug=False):
    # with getDongle(debug) as dongle: #  Dongle is not managed resource, a pity..
    dongle = None
    try:
        dongle = getDongle(debug)
        parsed, elements = parse_bip32_path(path)
        print('confirm on device...')
        b = dongle.exchange(bytes.fromhex("8004") + struct.pack('BB', key_mask, elements) + parsed)
        # returned map pubkey (65) priv key (32) chain code (32)
        return bytes(b[:65]), bytes(b[65:65+32]), bytes(b[65+32:])
    finally:
        if dongle is not None and dongle.opened:
            dongle.close()


def nano_get_pub_master_key(path, netcode):
    _, depth = parse_bip32_path(path)
    public_key, _, chain_code = nano_get_key(path, key_part_pub_key + key_part_chaincode)
    wallet = BIP32Node(netcode, chain_code, depth, public_pair=Key.from_sec(public_key, netcode).public_pair())
    return wallet.wallet_key(as_private=False)


def nano_get_priv_master_key(path, netcode):
    _, depth = parse_bip32_path(path)
    _, private_key, chain_code = nano_get_key(path, key_part_priv_key + key_part_chaincode)
    bip32_wallet = BIP32Node(netcode, chain_code, depth, secret_exponent=encoding.from_bytes_32(private_key))
    return bip32_wallet.wallet_key(as_private=True)


def nano_is_present():
    for hidDevice in hid.enumerate(0, 0):
        if hidDevice['vendor_id'] == 0x2c97:
            return True
    return False


def nanohandler(f):
    @wraps(f)
    def _wrap(*args, **kwargs):
        try:
            r = f(*args, **kwargs)
            print('---------------------------------------------------------------')
            print('remove nano to continue')
            while nano_is_present():
                time.sleep(0.3)
            return r
        except CommException as comm:
            if comm.message == 'No dongle found':
                print(comm.message)
            elif comm.sw == 0x6985:
                print('Aborted by user')
            elif comm.sw == 0x6a80:
                print('invalid derivation path len')
            elif comm.sw == 0x6e00:
                print('run Entropy app')
            else:
                print('Invalid status %x' % comm.sw)
            raise
        except OSError as oserr:
            if str(oserr) == 'open failed':
                print('cannot open usb - wait for device to settle')
            raise
    return _wrap