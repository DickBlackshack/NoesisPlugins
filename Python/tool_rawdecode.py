from inc_noesis import *
import os

RAWDECODE_STRING = "64;64;r8;0"

def registerNoesisTypes():
	handle = noesis.registerTool("Raw image decode", rdToolMethod, "Perform a raw image decode.")
	noesis.setToolFlags(handle, noesis.NTOOLFLAG_CONTEXTITEM)
	return 1

def rdGetOptions(optionString):
	try:
		l = optionString.split(";")
		return int(l[0]), int(l[1]), l[2], int(l[3])
	except:
		return 0, 0, None, 0
	
def rdValidateOptionString(inVal):
	options = rdGetOptions(inVal)
	if not options[0]:
		return "Invalid format string."
	return None
	
def rdToolMethod(toolIndex):
	srcName = noesis.getSelectedFile()
	if not srcName or not os.path.exists(srcName):
		noesis.messagePrompt("Selected file isn't readable through the standard filesystem.")
		return 0

	global RAWDECODE_STRING
	optionString = noesis.userPrompt(noesis.NOEUSERVAL_STRING, "Option String", "Enter the decode specification string in the format of width;height;format;offset.", RAWDECODE_STRING, rdValidateOptionString)
	if not optionString:
		return 0
	RAWDECODE_STRING = optionString
	
	width, height, format, offset = rdGetOptions(optionString)
	if not format:
		return 0

	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)

	dstName = noesis.getScenesPath() + "rawdecode_results.png"
	
	rawData = rapi.loadIntoByteArray(srcName)
	if format.startswith("bc"):
		bcModeString = format[2:].lower()
		#could potentially use software decoder for more stuff (astc, pvrtc) here
		bcModes = {
			"1" : noesis.NOESISTEX_DXT1,
			"2" : noesis.NOESISTEX_DXT3,
			"3" : noesis.NOESISTEX_DXT5,
			"4" : noesis.FOURCC_ATI1,
			"5" : noesis.FOURCC_ATI2,
			"6" : noesis.FOURCC_BC6H,
			"6s" : noesis.FOURCC_BC6S,
			"7" : noesis.FOURCC_BC7
		}
		if bcModeString not in bcModes:
			print("Unimplemented BC:", bcModeString, "Treating as BC1.")
			bcModeString = "1"
		bcMode = bcModes[bcModeString]
		rgba = rapi.imageDecodeDXT(rawData[offset:], width, height, bcMode)
	else:
		rgba = rapi.imageDecodeRaw(rawData[offset:], width, height, format)
		
	tex = NoeTexture(dstName, width, height, rgba, noesis.NOESISTEX_RGBA32)
	
	if not noesis.saveImageRGBA(dstName, tex):
		noesis.messagePrompt("Error writing decoded image.")
		return 0

	noesis.openAndRemoveTempFile(dstName)	
		
	noesis.freeModule(noeMod)

	return 0
