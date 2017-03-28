#*******************************************************************************
#   Ledger Blue
#   (c) 2016 Ledger
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#*******************************************************************************

APPNAME = Entropy
TARGET_ID = 0x31100002 #Nano S
ICON_DATA = 0100ffffff00000000000000000c3184231009200540038811fc3f48132005100984230c3100000000
APP_LOAD_PARAMS=--appFlags 0x40
# max length of derivation path
MAX_BIP32_PATH=5


################
# Default rule #
################

all: default

# consider every intermediate target as final to avoid deleting intermediate files
.SECONDARY:

# disable builtin rules that overload the build process (and the debug log !!)
.SUFFIXES:
MAKEFLAGS += -r

SHELL =       /bin/bash
#.ONESHELL:


############
# Platform #
############
PROG     := token

CONFIG_PRODUCTIONS := bin/$(PROG)

SOURCE_PATH   := src $(BOLOS_SDK)/src $(dir $(shell find $(BOLOS_SDK)/lib_stusb* | grep "\.c$$")) $(dir $(shell find $(BOLOS_SDK)/lib_bluenrg* | grep "\.c$$"))
SOURCE_FILES  := $(foreach path, $(SOURCE_PATH),$(shell find $(path) | grep "\.c$$") )
INCLUDES_PATH := src_usb $(dir $(shell find $(BOLOS_SDK)/lib_stusb* | grep "\.h$$")) include src $(BOLOS_SDK)/include $(BOLOS_SDK)/include/arm

#firmware 1.2 - uncomment below and comment includes above
#INCLUDES_PATH := src_usb $(dir $(shell find $(BOLOS_SDK)/lib_stusb* | grep "\.h$$")) $(dir $(shell find $(BOLOS_SDK)/lib_bluenrg* | grep "\.h$$")) include src $(BOLOS_SDK)/include $(BOLOS_SDK)/include/arm
#DEFINES   += HAVE_BLE HAVE_BLUENRG HCI_READ_PACKET_NUM_MAX=3 BLUENRG_MS HCI_READ_PACKET_SIZE=72

### platform definitions
DEFINES := ST31 gcc __IO=volatile

DEFINES   += OS_IO_SEPROXYHAL IO_SEPROXYHAL_BUFFER_SIZE_B=300
DEFINES   += HAVE_BAGL HAVE_SPRINTF
DEFINES   += HAVE_IO_USB HAVE_L4_USBLIB IO_USB_MAX_ENDPOINTS=6 IO_HID_EP_LENGTH=64 HAVE_USB_APDU
#DEFINES  += PRINTF=screen_printf
DEFINES   += PRINTF\(...\)=
DEFINES   += UNUSED\(x\)=\(void\)x
DEFINES   += MAX_BIP32_PATH=$(MAX_BIP32_PATH)

##############
# Compiler #
##############
GCCPATH   := $(BOLOS_ENV)/gcc-arm-none-eabi-5_3-2016q1/bin/
CLANGPATH := $(BOLOS_ENV)/clang-arm-fropi/bin
CC       := $(CLANGPATH)/clang 

CFLAGS_SHARED   := 
CFLAGS_SHARED   += -gdwarf-2  -gstrict-dwarf 
CFLAGS_SHARED   += -mcpu=cortex-m0 -mthumb 
CFLAGS_SHARED   += -fno-common -mtune=cortex-m0 -mlittle-endian 
CFLAGS_SHARED   += -std=gnu99 -Werror=int-to-pointer-cast -Wall -Wextra #-save-temps
CFLAGS_SHARED   += -fdata-sections -ffunction-sections -funsigned-char -fshort-enums 
CFLAGS_SHARED   += -mno-unaligned-access 
CFLAGS_SHARED   += -Wno-unused-parameter -Wno-duplicate-decl-specifier -Wno-macro-redefined

CFLAGS_SHARED   += -fropi --target=armv6m-none-eabi

#CFLAGS_SHARED   += -finline-limit-0 -funsigned-bitfields 

CFLAGS += -O3 -Os $(CFLAGS_SHARED)

AS     := $(GCCPATH)/arm-none-eabi-gcc
AFLAGS += -ggdb2 -O3 -Os -mcpu=cortex-m0 -fno-common -mtune=cortex-m0

# NOT SUPPORTED BY STM3L152 CFLAGS   += -fpack-struct
#-pg --coverage
LD       := $(GCCPATH)/arm-none-eabi-gcc
LDFLAGS  := 
LDFLAGS  += -gdwarf-2  -gstrict-dwarf 
#LDFLAGS  += -O0 -g3
LDFLAGS  += -O3 -Os
#LDFLAGS  += -O0
LDFLAGS  += -Wall 
LDFLAGS  += -mcpu=cortex-m0 -mthumb 
LDFLAGS  += -fno-common -ffunction-sections -fdata-sections -fwhole-program -nostartfiles 
LDFLAGS  += -mno-unaligned-access
#LDFLAGS  += -nodefaultlibs
#LDFLAGS  += -nostdlib -nostdinc
LDFLAGS  += -T$(BOLOS_SDK)/script.ld  -Wl,--gc-sections -Wl,-Map,debug/$(PROG).map,--cref
LDLIBS   += -Wl,--library-path -Wl,$(GCCPATH)/../lib/armv6-m/
#LDLIBS   += -Wl,--start-group 
LDLIBS   += -lm -lgcc -lc  
#LDLIBS   += -Wl,--end-group
# -mno-unaligned-access 
#-pg --coverage

### computed variables
VPATH := $(dir $(SOURCE_FILES))
OBJECT_FILES := $(sort $(addprefix obj/, $(addsuffix .o, $(basename $(notdir $(SOURCE_FILES))))))
DEPEND_FILES := $(sort $(addprefix dep/, $(addsuffix .d, $(basename $(notdir $(SOURCE_FILES))))))

ifeq ($(filter clean,$(MAKECMDGOALS)),)
-include $(DEPEND_FILES)
endif

clean:
	rm -fr obj bin debug dep

prepare:
	@mkdir -p bin obj debug dep

.SECONDEXPANSION:

# default is not to display make commands
log = $(if $(strip $(VERBOSE)),$1,@$1)

default: prepare bin/$(PROG)

load: 
	python -m ledgerblue.loadApp --targetId $(TARGET_ID) --apdu --fileName bin/$(PROG).hex --appName $(APPNAME) --icon $(ICON_DATA)  $(APP_LOAD_PARAMS)

delete:
	python -m ledgerblue.deleteApp --targetId $(TARGET_ID) --appName $(APPNAME)

bin/$(PROG): $(OBJECT_FILES) $(BOLOS_SDK)/script.ld
	@echo "[LINK] 	$@"
	$(call log,$(call link_cmdline,$(OBJECT_FILES) $(LDLIBS),$@))
	$(call log,$(GCCPATH)/arm-none-eabi-objcopy -O ihex -S bin/$(PROG) bin/$(PROG).hex)
	$(call log,mv bin/$(PROG) bin/$(PROG).elf)
	$(call log,cp bin/$(PROG).elf obj)
	$(call log,$(GCCPATH)/arm-none-eabi-objdump -S -d bin/$(PROG).elf > debug/$(PROG).asm)

dep/%.d: %.c Makefile
	@echo "[DEP]    $@"
	@mkdir -p dep
	$(call log,$(call dep_cmdline,$(INCLUDES_PATH), $(DEFINES),$<,$@))

obj/%.o: %.c dep/%.d
	@echo "[CC]	$@"
	$(call log,$(call cc_cmdline,$(INCLUDES_PATH), $(DEFINES),$<,$@))

obj/%.o: %.s
	@echo "[CC]	$@"
	$(call log,$(call as_cmdline,$(INCLUDES_PATH), $(DEFINES),$<,$@))


### BEGIN GCC COMPILER RULES

# link_cmdline(objects,dest)		Macro that is used to format arguments for the linker
link_cmdline = $(LD) $(LDFLAGS) -o $(2) $(1)

# dep_cmdline(include,defines,src($<),dest($@))	Macro that is used to format arguments for the dependency creator
dep_cmdline = $(CC) -M $(CFLAGS) $(addprefix -D,$(2)) $(addprefix -I,$(1)) $(3) | sed 's/\($*\)\.o[ :]*/obj\/\1.o: /g' | sed -e 's/[:\t ][^ ]\+\.c//g' > dep/$(basename $(notdir $(4))).d 2>/dev/null

# cc_cmdline(include,defines,src,dest)	Macro that is used to format arguments for the compiler
cc_cmdline = $(CC) -c $(CFLAGS) $(addprefix -D,$(2)) $(addprefix -I,$(1)) -o $(4) $(3)

as_cmdline = $(AS) -c $(AFLAGS) $(addprefix -D,$(2)) $(addprefix -I,$(1)) -o $(4) $(3)

### END GCC COMPILER RULES

