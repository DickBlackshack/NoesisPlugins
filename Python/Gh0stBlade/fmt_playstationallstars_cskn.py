#PlayStation All-Stars Battle Royale [Vita] - ".cskn" Loader
#By Gh0stblade
#v1.0
#Special thanks: Chrrox
#Options: These are bools that enable/disable certain features! They are global and affect ALL platforms!
#Var								Effect
#Misc
#Mesh Global
bOptimizeMesh = False				#Enable optimization (remove duplicate vertices, optimize lists for drawing) (True = on, False = off)
bMaterialsEnabled = True			#Materials (True = on, False = off)
#Render
bRenderAsPoints = False				#Render mesh as points without triangles drawn (True = on, False = off)
#Vertex Components
bNORMsEnabled = True				#Normals (True = on, False = off)
bUVsEnabled = True					#UVs (True = on, False = off)
bCOLsEnabled = True					#Vertex colours (True = on, False = off)
bSkinningEnabled = True				#Enable skin weights (True = on, False = off)
#Gh0stBlade ONLY
bDebug = True						#Prints debug info (True = on, False = off)
bDebugNormals = False and bDebug	#Debug normals (True = on, False = off)
bForceLoadModel = bDebug			#Force Load Model regardless of errors (True = on, False = off)

from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("PlayStation All-Stars Battle Royale [Vita]", ".cskn")
	noesis.setHandlerTypeCheck(handle, csknCheckType)
	noesis.setHandlerLoadModel(handle, csknLoadModel)
	
	if bDebug:
		noesis.logPopup()
	return 1

def csknCheckType(data):
	bs = NoeBitStream(data)
	if bs.readUInt() != 0x4C444F4D:
		print("Fatal Error: Unknown file magic: expected 0x4C444F4D!")
		return 0
	return 1

def swap32(i):
    return struct.unpack("<I", struct.pack(">I", i))[0]
	
class csknFile(object): 
	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		
	def loadModel(self):
		bs = self.inFile
		self.vertBuff = None
		self.normBuff = None
		self.tangBuff = None
		self.colorBuff = None
		self.uvBuff = None
		self.boneIdxBuff = None
		self.boneWeightBuff = None
		self.faceBuff = None
		
		#FIXME: Big endian actually!
		magic = swap32(bs.readUInt())
		version = swap32(bs.readUInt())
		unk00 = swap32(bs.readUInt())
		offsetFaceData = swap32(bs.readUInt())
		
		numEntries = bs.readUInt()
		
		if bDebug:
			print("Version: " + str(version) + " Offset FD: " + str(offsetFaceData) + " Num Entries: " + str(numEntries))
		
		for i in range(numEntries):
			bs.seek((i * 0x10) + 0x14, NOESEEK_ABS) 
			entryType = bs.readUInt()
			if entryType in csknEntryTypeList:
				csknEntryTypeList[entryType](self, bs, bs.readUShort(), bs.readUShort(), bs.readUInt(), bs.readUInt())
			else:
				print("Fatal Error: Unknown entry type:" + str(hex(entryType)))
		
		bs.seek(offsetFaceData + 0x10, NOESEEK_ABS)
		
		unk01 = swap32(bs.readUInt())
		faceBuffSize = swap32(bs.readUInt())
		self.faceBuff = bs.readBytes(int(faceBuffSize * 2))
		
		print("Offset: " + str(bs.getOffset()))
		
		unk01 = swap32(bs.readUInt())
		numMaterials = swap32(bs.readUInt())
		
		#for i in range(numMaterials):
		#	matUnk00 = bs.readUInt()
		#	matUnk01 = bs.readUInt()
		#	matUnk02 = bs.readUInt()
		#	matUnk03 = bs.readUInt()
		#	matName = bs.readBytes(bs.readUByte()).decode("ASCII").rstrip("\0")
		#	bs.seek(0x2E, NOESEEK_REL)
		#	texName = bs.readBytes(bs.readUByte()).decode("ASCII").rstrip("\0")
			
	def loadPosition(self, bs, entryType, entryFlags, entryOffset, entrySize):
		print("Loading Positions....")
		bs.seek(entryOffset + 0x10, NOESEEK_ABS)
		print("XYZ Offset: " + str(bs.getOffset()))
		self.vertBuff = bs.readBytes(entrySize)
		print("XYZ End Offset: " + str(bs.getOffset()))
		print("Finished loading Positions!")
		
	def loadNormal(self, bs, entryType, entryFlags, entryOffset, entrySize):
		print("Loading Normals....")
		bs.seek(entryOffset + 0x10, NOESEEK_ABS)
		print("NRM Offset: " + str(bs.getOffset()))
		self.normBuff = bs.readBytes(entrySize)
		print("NRM End Offset: " + str(bs.getOffset()))
		print("Finished loading Normals!")
		
	def loadTangent(self, bs, entryType, entryFlags, entryOffset, entrySize):
		print("Loading Tangents....")
		bs.seek(entryOffset + 0x10, NOESEEK_ABS)
		print("TAN Offset: " + str(bs.getOffset()))
		self.tangBuff = bs.readBytes(entrySize)
		print("TAN End Offset: " + str(bs.getOffset()))
		print("Finished loading Tangents!")
		
	def loadColor(self, bs, entryType, entryFlags, entryOffset, entrySize):
		print("Loading Colors....")
		bs.seek(entryOffset + 0x10, NOESEEK_ABS)
		print("Color Offset: " + str(bs.getOffset()))
		self.colorBuff = bs.readBytes(entrySize)
		print("Color End Offset: " + str(bs.getOffset()))
		print("Finished loading Colors!")
		
	def loadTex(self, bs, entryType, entryFlags, entryOffset, entrySize):
		print("Loading UVs....")
		bs.seek(entryOffset + 0x10, NOESEEK_ABS)
		print("UV Offset: " + str(bs.getOffset()))
		self.uvBuff = bs.readBytes(entrySize)
		print("UV End Offset: " + str(bs.getOffset()))
		print("Finished loading UVs!")
		
	def loadBoneIndex(self, bs, entryType, entryFlags, entryOffset, entrySize):
		print("Loading Bone Indices....")
		bs.seek(entryOffset + 0x10, NOESEEK_ABS)
		print("Bone Index Offset: " + str(bs.getOffset()))
		self.boneIdxBuff = bs.readBytes(entrySize)
		print("Bone Index End Offset: " + str(bs.getOffset()))
		print("Finished loading Bone Indices!")
		
	def loadBoneWeight(self, bs, entryType, entryFlags, entryOffset, entrySize):
		print("Loading Bone Weights....")
		bs.seek(entryOffset + 0x10, NOESEEK_ABS)
		print("Bone Weight Offset: " + str(bs.getOffset()))
		self.boneWeightBuff = bs.readBytes(entrySize)
		print("Bone Weight End Offset: " + str(bs.getOffset()))
		print("Finished loading Bone Weight!")
			
	def buildMesh(self):
		bs = self.inFile
		
		rapi.rpgBindPositionBufferOfs(self.vertBuff, noesis.RPGEODATA_FLOAT, 0xC, 0)
		rapi.rpgBindNormalBufferOfs(self.normBuff, noesis.RPGEODATA_HALFFLOAT, 0x8, 0)#CHECK
		rapi.rpgBindTangentBufferOfs(self.tangBuff, noesis.RPGEODATA_HALFFLOAT, 0x8, 0)
		rapi.rpgBindUV1BufferOfs(self.uvBuff, noesis.RPGEODATA_HALFFLOAT, 0x4, 0)
		
		if bRenderAsPoints:
				rapi.rpgCommitTriangles(None, noesis.RPGEODATA_FLOAT, int(len(self.vertBuff) / 0xC), noesis.RPGEO_POINTS, 0x1)
		else:
				rapi.rpgCommitTriangles(rapi.swapEndianArray(self.faceBuff, 2), noesis.RPGEODATA_USHORT, int((len(self.faceBuff) / 2)/2), noesis.RPGEO_TRIANGLE, 0x1)
		return 1
		
			
csknEntryTypeList = {
0x504F5330		:	csknFile.loadPosition,   #"POS0"
0x4E524D30		:	csknFile.loadNormal,     #"NRM0"
0x54414E30		:	csknFile.loadTangent,    #"TAN0"
0x434F4C30		:	csknFile.loadColor,      #"COL0"
0x54455830		:	csknFile.loadTex,        #"TEX0"
0x424F4E49		:	csknFile.loadBoneIndex,  #"BONI"
0x424F4E57		:	csknFile.loadBoneWeight, #"BONW"
}

def csknLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	model = csknFile(data)
	model.loadModel()
	model.buildMesh()
	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()
	#mdl.setBones(model.boneList)
	#mdl.setModelMaterials(NoeModelMaterials(model.texList, model.matList))
	mdlList.append(mdl);
	return 1