#!/usr/bin/env python
from ledgerblue.comm import getDongle
from ledgerblue.commException import CommException
from pycoin.key.BIP32Node import BIP32Node
from pycoin.key import Key
from pycoin import encoding
import struct
import time
import hid
from secp256k1 import PublicKey, PrivateKey

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


def is_nano_present():
    for hidDevice in hid.enumerate(0, 0):
        if hidDevice['vendor_id'] == 0x2c97:
            return True
    return False


def _test_spoof_nano_key(path, mask, debug=False):
    secp_privkey = PrivateKey()
    raw_privkey = bytearray(32) if mask & key_part_priv_key == 0 else secp_privkey.private_key
    raw_pubkey = bytearray(65) if mask & key_part_pub_key == 0 else secp_privkey.pubkey.serialize(compressed=False)
    chaincode = bytearray(32) if mask & key_part_chaincode == 0 else secp_privkey.private_key
    return raw_pubkey, raw_privkey, chaincode


def _test_signature(public_key, private_key, msg):
    print('uncompressed pub key %i bytes: %s' % (len(public_key), public_key.hex()))
    comp_pubkey = Key.from_sec(public_key)
    print('compressed pub key: %s' % comp_pubkey.sec_as_hex(use_uncompressed=False))
    secp_pubkey = PublicKey(public_key, raw=True)
    secp_privkey = PrivateKey(private_key, raw=True)
    print('checking signature')
    signature = secp_privkey.ecdsa_sign(msg)
    if(secp_pubkey.ecdsa_verify(msg, signature)):
        print('signature OK')
    else:
        raise Exception('signature test failed')


def test_key_pair(path, f_get_key):
    print('get public and private keys for path %s' % path)
    public_key, private_key, chain_code = f_get_key(path, key_part_pub_key+key_part_priv_key)
    _test_signature(public_key, private_key, 'NEUFUND'.encode('ascii'))
    print('checking if chaincode is 0')
    if bytearray(32) != chain_code:
        raise Exception('chaincode is not 0')
    print('chaincode OK')


def test_pub_master_derivation(netcode, path, f_get_key):
    print('get public key for path %s' % path)
    _, depth = parse_bip32_path(path)
    public_key, private_key, chain_code = f_get_key(path, key_part_pub_key + key_part_chaincode)
    bip32_wallet = BIP32Node(netcode, chain_code, depth, public_pair=Key.from_sec(public_key, netcode).public_pair())
    print("master public key: %s" % bip32_wallet.wallet_key(as_private=False))
    if private_key != bytearray(32):
        raise Exception('private key should be 0')


def test_priv_master_derivation(netcode, path, f_get_key):
    print('get private key for path %s' % path)
    _, depth = parse_bip32_path(path)
    public_key, private_key, chain_code = f_get_key(path, key_part_priv_key + key_part_chaincode)
    bip32_wallet = BIP32Node(netcode, chain_code, depth, secret_exponent=encoding.from_bytes_32(private_key))
    print("master private key: %s" % bip32_wallet.wallet_key(as_private=True))
    if public_key != bytearray(65):
        raise Exception('public key should be 0')


def test_master_key_pair(netcode, path, f_get_key):
    print('test if master pub and priv keys match')
    _, depth = parse_bip32_path(path)
    public_key, private_key, chain_code = f_get_key(path, key_part_pub_key + key_part_priv_key + key_part_chaincode)
    pub_wallet = BIP32Node(netcode, chain_code, depth, public_pair=Key.from_sec(public_key, netcode).public_pair())
    priv_wallet = BIP32Node(netcode, chain_code, depth, secret_exponent=encoding.from_bytes_32(private_key))
    if pub_wallet.wallet_key(as_private=False) != priv_wallet.wallet_key(as_private=False):
        raise Exception('pub wallet and pub wallet derived from private do not match')
    print('master pub key and master pub key derived from priv wallet are identical')
    print('derive child keys and test signatures')
    pub_child = pub_wallet.subkey_for_path("198731")
    priv_child = priv_wallet.subkey_for_path("198731")
    _test_signature(pub_child.sec(use_uncompressed=True), encoding.to_bytes_32(priv_child.secret_exponent()),
                    'NEUFUND'.encode('ascii'))


print('do not use your production nano, a lot of secret stuff will be displayed')
path = "44'/0'/0'"  # input("derivation path ie. 44'/0'/0' :")
_f_key_prod_func = nano_get_key
try:

    test_key_pair(path, _f_key_prod_func)
    test_pub_master_derivation('BTC', path, _f_key_prod_func)
    test_priv_master_derivation('BTC', path, _f_key_prod_func)
    test_master_key_pair('BTC', path, _f_key_prod_func)
    print('---------------------------------------------------------------')
    print('remove nano to continue')
    while is_nano_present():
        time.sleep(0.3)
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
except OSError as oserr:
    if str(oserr) == 'open failed':
        print('cannot open usb - wait for device to settle')