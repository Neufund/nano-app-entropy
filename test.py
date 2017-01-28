#!/usr/bin/env python
from secp256k1 import PublicKey, PrivateKey
from nano_utils.nano import *


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


@nanohandler
def test_nano(path, _f_key_prod_func):
    test_key_pair(path, _f_key_prod_func)
    test_pub_master_derivation('BTC', path, _f_key_prod_func)
    test_priv_master_derivation('BTC', path, _f_key_prod_func)
    test_master_key_pair('BTC', path, _f_key_prod_func)


print('do not use your production nano, a lot of secret stuff will be displayed')
# input("derivation path ie. 44'/0'/0' :")
test_nano("44'/0'/0'", nano_get_key)
