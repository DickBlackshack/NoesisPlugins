#Just Dance 5 .ckd [X360] - ".ckd" Loader
#By Gh0stblade
#v1.0
#Special thanks: Chrrox

from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("Just Dance 5 2D Texture [X360]", ".ckd")
	noesis.setHandlerTypeCheck(handle, ckdCheckType)
	noesis.setHandlerLoadRGBA(handle, ckdLoadDDS)
	noesis.logPopup()
	return 1
		
def ckdCheckType(data):
	bs = NoeBitStream(data, NOE_BIGENDIAN)
	fileVersion = bs.readUInt()
	fileMagic = bs.readUInt()
	if fileMagic == 0x54455800:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(fileMagic) + " expected 0x54455800!"))
		return 0

def ckdLoadDDS(data, texList):
	bs = NoeBitStream(data, NOE_BIGENDIAN)
	fileVersion = bs.readUInt()
	fileMagic = bs.readUInt()
	ddsOffsetFlags = bs.readUInt()
	ddsUnk00 = bs.readUShort()
	ddsUnk01 = bs.readUShort()
	
	ddsWidth = bs.readUShort()
	ddsHeight = bs.readUShort()
	#ddsWidth = ddsHeight for some reason helps an error regarding wrong array size? #weird
	ddsUnk02 = bs.readUShort()
	ddsUnk03 = bs.readUByte()
	ddsUnk04 = bs.readUShort()
	ddsSize = bs.readUShort()
	bs.seek(ddsOffsetFlags, NOESEEK_ABS)
	ddsFlags = bs.readUInt()
	
	ddsData = None
	ddsType = None
	
	if ddsFlags == 0x3:
		bs.seek(0x4C, NOESEEK_ABS)
		ddsType = bs.readUInt()
	elif ddsFlags ==  0x20101FF:
		bs.seek(0x44, NOESEEK_ABS)
		ddsType = bs.readUInt()
	else:
		print("Fatal Error: Unknown DDS Flags: " + str(hex(ddsFlags)))
	
	if ddsType == 0x52:
		bs.seek(0x60, NOESEEK_ABS)
		ddsData = bs.readBytes(ddsSize * 0x100)
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), int(ddsWidth / 2), int(ddsHeight / 2), 8)
	elif ddsType == 0x53:
		bs.seek(0x60, NOESEEK_ABS)
		ddsData = bs.readBytes(ddsSize * 0x100)
		ddsFmt = noesis.NOESISTEX_DXT3
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), int(ddsWidth / 2), int(ddsHeight / 2), 16)
	elif ddsType == 0x54:
		bs.seek(0x60, NOESEEK_ABS)
		ddsData = bs.readBytes(ddsSize * 0x100)
		ddsFmt = noesis.NOESISTEX_DXT5
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), int(ddsWidth / 2), int(ddsHeight / 2), 16)
	elif ddsType == 0x86:
		bs.seek(0x60, NOESEEK_ABS)
		ddsData = bs.readBytes(ddsSize * 0x100)
		ddsData = rapi.imageUntile360Raw(rapi.swapEndianArray(ddsData, 2), int(ddsWidth / 2), int(ddsHeight / 2), 4)
		ddsData = rapi.imageDecodeRaw(ddsData, int(ddsWidth / 2), int(ddsHeight / 2), "a8r8g8b8")
		ddsFmt = noesis.NOESISTEX_RGBA32
	elif ddsType == 0x86010200:
		bs.seek(0xAC, NOESEEK_ABS)
		ddsData = bs.readBytes(ddsSize * 0x100)
		#ddsData = rapi.imageUntile360Raw(ddsData, int(ddsWidth / 6), int(ddsHeight / 6), 4)
		ddsData = rapi.imageDecodeRaw(ddsData, int(ddsWidth / 2), int(ddsHeight / 2), "a8r8g8b8")
		ddsFmt = noesis.NOESISTEX_RGBA32
	else:
		print("Fatal Error: " + "Unknown DDS type: " + str(hex(ddsType)) + " using default DXT1")
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), int(ddsWidth / 2), int(ddsHeight / 2), 8)
	texList.append(NoeTexture("Texture", int(ddsWidth / 2), int(ddsHeight / 2), ddsData, ddsFmt))
	return 1
	