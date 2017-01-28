import pyperclip
from nano_utils.nano import *


@nanohandler
def entropy_to_clip(path):
    print('entropy for path %s' % path)
    public_key, _, chain_code = nano_get_key(path, key_part_pub_key+key_part_chaincode)
    compPK = Key.from_sec(public_key)
    entropy = compPK.sec(use_uncompressed=False)[1:] + chain_code
    pyperclip.copy(entropy.hex())
    print('entropy in clipboard')

try:
    pyperclip.copy('test')
except Exception as e:
    print(str(e))
    print('please have clipboard method installed')
    print('sudo apt-get install xsel')
    exit()

entropy_to_clip(input('your keepass file derivation path:'))
