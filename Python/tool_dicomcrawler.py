from inc_noesis import *
import os

RENAME_IF_NO_EXTENSION = False
CHECK_PHOTOMETRIC_INTERPRETATIONS = False
HEADER_CLIP_SIZE = 2048 #assumes that group2 element containing transfer syntax is somewhere in the first (this many) bytes

def registerNoesisTypes():
	handle = noesis.registerTool("DICOM Crawler", dwToolMethod, "Crawl through DICOM files.")
	return 1

def dwToolMethod(toolIndex):
	noesis.logPopup()

	baseDir = noesis.userPrompt(noesis.NOEUSERVAL_FOLDERPATH, "Open Folder", "Select a folder to crawl.", noesis.getSelectedDirectory(), None)
	if baseDir is None:
		return 0
		
	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)

	try:
		for root, dirs, files in os.walk(baseDir):
			for fileName in files:
				fullPath = os.path.join(root, fileName)
				doRename = False
				with open(fullPath, "rb") as f:
					data = f.read(-1 if CHECK_PHOTOMETRIC_INTERPRETATIONS else HEADER_CLIP_SIZE)
					transferSyntax = rapi.callExtensionMethod("getDicomTransferSyntax", data)
					if transferSyntax:
						print(fullPath, "-", transferSyntax)
						if CHECK_PHOTOMETRIC_INTERPRETATIONS:
							photometricInterpretation = rapi.callExtensionMethod("getDicomPhotometricInterpretation", data)
							print("PI:", photometricInterpretation)
						if RENAME_IF_NO_EXTENSION:
							doRename = True
				#needs to be out here so we don't try to rename with an open file handle
				if doRename:
					path, ext = os.path.splitext(fullPath)
					if ext.lower() != ".dcm":
						os.rename(fullPath, fullPath + ".dcm")
	except:
		print("Encountered an error during the DICOM crawl.")
		
	noesis.freeModule(noeMod)
		
	return 0
