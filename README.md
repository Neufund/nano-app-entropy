## how it works

* a node secret is derived from master secret (expoent and chaincode parts) for derivation path provided
* public key is derived from exponent
* public key and chaincode is returned and used as master secret for completely new root bip32 node
* from this entropy a public and private key are created

## how to use

* run entropy app
* every app  can set USB device data (can pretend to be any device)
* wait for usb to settle, here is how it looks to lsusb `Bus 001 Device 049: ID 2c97:0001`
* run test.py and do what it says
* it runs inside container if you map usb correctly. if you run container in VM then you need to filter proper USB device into VM

```
docker build . -t neufund/nano
docker run -it --rm --privileged -v /dev/bus/usb:/dev/bus/usb neufund/nano python test.py
```

## install development components
start here:
https://github.com/LedgerHQ/ledger-nano-s

when cloning Nano SDK, checkout tag that corresponds to your Nano's firmware

### make virtualenv with ledger library
```
virtualenv nano
source nano/bin/activate
activate venv nano
```

### install dependencies
install secp256k1 as described here https://github.com/LedgerHQ/blue-loader-python
for more details check Dockerfile, if you install on ubuntu replace following library names
libusb-dev == libusb-1.0-0.dev
eudev-dev == libudev-dev

### prerequisites to gcc and clang building
There is a docker container with customized gcc and clang compilers, if not install following dependency
`sudo apt-get install libc6-dev-i386`
and follow guidelines

### set environment variables
```
export BOLOS_ENV=/home/rudolfix/src/nano/blue-devenv
export BOLOS_SDK=/home/rudolfix/src/nano/nanos-secure-sdk
```


## how to build and deploy
token.hex is included and may be deployed without main.c compilation
check Makefile for load and delete targets


## what to set in Makefile
ledger provides a sample makefile, a few things must be set
APPNAME = Entropy
TARGET_ID = 0x31100002 #Nano S
ICON_FILE = icon_bw.gif
APP_LOAD_PARAMS=--appFlags 0x40

if invalid target is set, you'll get Exception : Invalid status 6484
more on app programing here http://ledger.readthedocs.io/en/latest/bolos/introduction.html
os headers: https://github.com/LedgerHQ/blue-secure-sdk/blob/master/include/os.h


## how to create an icon

* create 16x16 bw gif
* execute `python icon.py 16 16 <icon name> hexbitmaponly`
* local icon.py is modified by me to run on python3
* replace in --icon for load target
* when drawing icon leave 2px frame around your stuff

