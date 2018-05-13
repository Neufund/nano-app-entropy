import pyperclip
from nano_utils.nano import *
from pycoin.key.BIP32Node import BIP32Node


@nanohandler
def entropy_to_clip(path):
    print('entropy for path %s' % path)
    _, private_key, chain_code = nano_get_key(path, key_part_priv_key + key_part_chaincode)
    _, depth = parse_bip32_path(path)
    bip32_wallet = BIP32Node("BTC", chain_code, depth, secret_exponent=encoding.from_bytes_32(private_key))
    address = pub_to_address(pycoin_to_pub(bip32_wallet))
    # address = pub_to_address(public_key)
    print('Ethereum address %s' % address)
    # private_key = pycoin_to_priv(priv_wallet)
    # print(private_key.hex().upper())
    pyperclip.copy(private_key.hex().upper())
    print('entropy in clipboard and will be erased when you disconnect')

try:
    pyperclip.copy('test')
except Exception as e:
    print(str(e))
    print('please have clipboard method installed')
    print('sudo apt-get install xsel')
    exit()

print('Get ethereum address and private key (in clipboard)')
entropy_to_clip(input('derivation path:'))
pyperclip.copy('')