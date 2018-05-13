from ledgerblue.comm import getDongle
from ledgerblue.commException import CommException
from eth_utils import keccak, to_checksum_address, big_endian_to_int, int_to_big_endian
from pycoin.key.BIP32Node import BIP32Node
from pycoin.key import Key
from pycoin import encoding
import struct
import hid
import time
from functools import wraps


# key parts to be returned as defined in main.c
key_part_priv_key = 1
key_part_pub_key = 2
key_part_chaincode = 4


def pycoin_to_pub(key):
    x, y = key.public_pair()
    return int_to_big_endian(x) + int_to_big_endian(y)
    
    
def pycoin_to_priv(key):
    assert(key.is_private())
    return int_to_big_endian(key.secret_exponent())
    

def pub_to_address(pubkey: bytes) -> str:
    """
    Gets checksummed Ethereum address from public key
    :param pubkey: 64 bytes public key
    :return: Ethereum address string
    """
    return to_checksum_address(keccak(pubkey[0:])[12:])

def load_priv_wallet(wallet_key):
    """
    create private BIP32 wallet from private master key
    :param wallet_key: contains private wallet key prefixed 'tprv'. check README.md
    """
    return BIP32Node.BIP32Node.from_wallet_key(wallet_key)

def parse_bip32_path(path):
    """
    parse derivation path as a array of unsigned 32bit ints, hardening specified as '
    :param path: path to parse
    :return: parsed path and depth tuple
    """
    result = b''
    elements = path.split('/')
    for pathElement in elements:
        element = pathElement.split('\'')
        # little endian! why Ledger used big endian and converted in main.c???
        if len(element) == 1:
            result = result + struct.pack("<I", int(element[0]))
        else:
            result = result + struct.pack("<I", 0x80000000 | int(element[0]))
    return result, len(elements)


def nano_get_key(path, key_mask, debug=False):
    """
    derive and obtain master key from nano
    :param path: derivation path
    :param key_mask: which parts of key to return
    :param debug: dump transission in hex
    :return: a tuple (uncompressed pub key, priv key, chaincode) as specified in mask, if not specidied 0x0 string
    is returned
    """
    dongle = None
    try:
        # todo: make dogle a resource managed with "with"
        dongle = getDongle(debug)
        parsed, elements = parse_bip32_path(path)
        print('confirm on device...')
        b = dongle.exchange(bytes.fromhex("8004") + struct.pack('BB', key_mask, elements) + parsed)
        # returned map pubkey (65) priv key (32) chain code (32)
        return bytes(b[:65]), bytes(b[65:65+32]), bytes(b[65+32:])
    finally:
        if dongle is not None and dongle.opened:
            dongle.close()


def nano_get_pub_wallet(path, netcode='BTC'):
    """
    get bip32 wallet with derivable public master key
    :param path: derivation path
    :param netcode: BTC for main net
    :return: wallet string in xpub.... format
    """
    _, depth = parse_bip32_path(path)
    public_key, _, chain_code = nano_get_key(path, key_part_pub_key + key_part_chaincode)
    wallet = BIP32Node(netcode, chain_code, depth, public_pair=Key.from_sec(public_key, netcode).public_pair())
    return wallet.wallet_key(as_private=False)


def nano_get_priv_wallet(path, netcode='BTC'):
    """
    get bip32 wallet with derivable private master key
    :param path: derivation path
    :param netcode: BTC for main net
    :return: wallet string in xprv.... format
    """
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
    """
    safe wrapper for functions exchanging data with nano entropy app
    handles all interesting exceptional cases
    please note that entropy requires admin to confirm derivation so handler works in interactive mode
    as a precaution it will not exit until you disconnect nano from usb to prevent leaving nano unlocked and connected
    :param f: function to wrap
    """
    @wraps(f)
    def _wrap(*args, **kwargs):
        try:
            r = f(*args, **kwargs)
            print('---------------------------------------------------------------')
            print('remove nano to continue')
            while nano_is_present():
                time.sleep(0.3)
            # input("Press Enter to continue...")
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