#Demon's Souls .TPF [X360] - ".TPF" Loader
#By Gh0stblade
#v1.0
#Special thanks: Chrrox

from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("Demon's Souls 2D Texture [X360]", ".tpf")
	noesis.setHandlerTypeCheck(handle, tpfCheckType)
	noesis.setHandlerLoadRGBA(handle, tpfLoadDDS)
	noesis.logPopup()
	return 1
		
def tpfCheckType(data):
	bs = NoeBitStream(data, NOE_BIGENDIAN)
	fileMagic = bs.readUInt()
	if fileMagic == 0x54504600:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(fileMagic) + " expected 0x54455800!"))
		return 0

def tpfLoadDDS(data, texList):
	bs = NoeBitStream(data, NOE_BIGENDIAN)
	
	fileMagic = bs.readUInt()
	fileUnk00  = bs.readUShort()
	fileUnk01  = bs.readUShort()
	numTextures  = bs.readUInt()
	fileUnk02  = bs.readUByte()
	fileUnk03  = bs.readUByte()
	fileUnk04  = bs.readUByte()
	fileUnk05  = bs.readUByte()
	
	for i in range (numTextures):
		bs.seek(0x10 + i * 0x20, NOESEEK_ABS)#Entry start

		ddsOffset = bs.readUInt()
		ddsSize = bs.readUInt() #They use 0x48 padding after each texture
		ddsUnk01 = bs.readUInt() #Texture type?
		ddsWidth = bs.readUShort()
		ddsHeight = bs.readUShort()
		
		ddsUnk08 = bs.readUInt()
		ddsUnk09 = bs.readUInt()
		ddsNameOffset = bs.readUInt()
		ddsUnk10 = bs.readUInt()
		
		bs.seek(ddsNameOffset, NOESEEK_ABS)
		ddsName = bs.readString()
		
		bs.seek(ddsOffset, NOESEEK_ABS)
		ddsData = bs.readBytes(ddsSize)
		
		ddsFmt = noesis.NOESISTEX_DXT1
		texList.append(NoeTexture(ddsName, ddsWidth, ddsHeight, ddsData, ddsFmt))
	return 1
	