#Rise of the Tomb Raider [PC/X360] - ".tr2mesh" Loader
#By Gh0stblade
#v1.5
#Special thanks: Chrrox
#Options: These are bools that enable/disable certain features! They are global and affect ALL platforms!
#Var							Effect
#Misc
#Mesh Global
fDefaultMeshScale = 1.0 		#Override mesh scale (default is 1.0)
bOptimizeMesh = 0				#Enable optimization (remove duplicate vertices, optimize lists for drawing) (1 = on, 0 = off)
#bMaterialsEnabled = 1			#Materials (1 = on, 0 = off)
bRenderAsPoints = 0				#Render mesh as points without triangles drawn (1 = on, 0 = off)
#Vertex Components
bNORMsEnabled = 1				#Normals (1 = on, 0 = off)
bUVsEnabled = 1					#UVs (1 = on, 0 = off)
bCOLsEnabled = 0				#Vertex colours (1 = on, 0 = off)
bSkinningEnabled = 1			#Enable skin weights (1 = on, 0 = off)
#Gh0stBlade ONLY
debug = 0 						#Prints debug info (1 = on, 0 = off)

from inc_noesis import *
import math

def registerNoesisTypes():
	handle = noesis.register("Rise of the Tomb Raider 3D Mesh [PC/X360]", ".tr2mesh")
	noesis.setHandlerTypeCheck(handle, meshCheckType)
	noesis.setHandlerLoadModel(handle, meshLoadModel)
	
	handle = noesis.register("Rise of the Tomb Raider 2D Texture [X360]", ".tr2x360")
	noesis.setHandlerTypeCheck(handle, x360CheckType)
	noesis.setHandlerLoadRGBA(handle, x360LoadDDS)
	
	handle = noesis.register("Rise of the Tomb Raider 2D Texture [PC]", ".tr2pcd")
	noesis.setHandlerTypeCheck(handle, pcdCheckType)
	noesis.setHandlerLoadRGBA(handle, pcdLoadDDS)
	
	noesis.logPopup()
	return 1

def meshCheckType(data):
	bs = NoeBitStream(data)
	uiMagic = bs.readUInt()
	
	global iPlatform
	global iMeshType
	
	iPlatform = -1
	
	if uiMagic == 0x4:#PC I'm betting this is extremely unstable but oh well!
		iPlatform = 0
		bs.seek(0x10, NOESEEK_ABS)
		numOffsets = bs.readInt()
		bs.seek(0x18, NOESEEK_ABS)
		dataSize = bs.readInt()
		bs.seek(((numOffsets * 0x4) + 0x34) + dataSize, NOESEEK_ABS)
		return 1
	elif uiMagic == 0x4D657368:#X360
		iPlatform = 1
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(uiMagic) + " expected 'hsem'!"))
		return 0

def pcdCheckType(data):
	bs = NoeBitStream(data)
	uiMagic = bs.readUInt()
	if uiMagic == 0x39444350:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(uiMagic) + " expected PCD!"))
		return 0
		
def pcdLoadDDS(data, texList):
	bs = NoeBitStream(data)
	uiMagic = bs.readUInt()
	uiPcdType = bs.readUInt()
	uiPcdLength = bs.readUInt()
	uiPcdUnk00 = bs.readUInt()
	uiPcdWidth = bs.readUShort()
	uiPcdHeight = bs.readUShort()
	uiPcdFlags = bs.readUShort()
	uiPcdMipCount = bs.readUShort()
	uiPcdFlags2 = bs.readUShort()
	uiPcdUnk01 = bs.readUShort()
	if uiPcdFlags2 & 0x2000:
		szPcdName = bs.readBytes(0x100)
	bPcdData = bs.readBytes(uiPcdLength)
	gPcdFmt = None
	
	if uiPcdType == 0x31:#FIXME
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, noesis.FOURCC_DXT1NORMAL)
	elif uiPcdType == 0x3D:#FIXME
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodePVRTC(bPcdData, uiPcdWidth, uiPcdHeight, 4)
	elif uiPcdType == 0x47:#CORRECT
		gPcdFmt = noesis.NOESISTEX_DXT1
	elif uiPcdType == 0x48:#CORRECT
		gPcdFmt = noesis.NOESISTEX_DXT1
	elif uiPcdType == 0x4E:#CORRECT
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, noesis.NOESISTEX_DXT5)
	elif uiPcdType == 0x50:#CORRECT
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, noesis.FOURCC_ATI1)
	elif uiPcdType == 0x53:#CORRECT
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, noesis.FOURCC_ATI2)
	elif uiPcdType == 0x57:#VERIFY
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeRaw(bPcdData, uiPcdWidth, uiPcdHeight, "r8g8b8a8")
	elif uiPcdType == 0x5B:#CORRECT
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeRaw(bPcdData, uiPcdWidth, uiPcdHeight, "r8g8b8a8")
	elif uiPcdType == 0x63:#FIXME
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, noesis.NOESISTEX_DXT1)
		#bPcdData = rapi.imageDecodePVRTC(bPcdData, uiPcdWidth, uiPcdHeight, 4)
		#bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, noesis.FOURCC_ATI2)
	else:
		print("Fatal Error: Unsupported texture type: " + str(uiPcdType))
		
	if gPcdFmt != None:
		texList.append(NoeTexture("Texture", int(uiPcdWidth), int(uiPcdHeight), bPcdData, gPcdFmt))
	return 1
	
def x360CheckType(data):
	bs = NoeBitStream(data, NOE_BIGENDIAN)
	magic = bs.readUInt()
	if magic == 0x58333630:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected X360!"))
		return 0
		
def x360LoadDDS(data, texList):
	bs = NoeBitStream(data, NOE_BIGENDIAN)
	ddsSize = int(len(data) - 0x24)
	
	magic = bs.readUInt()
	ddsType = bs.readUInt()
	ddsLen = bs.readUInt()
	ddsUnk00 = bs.readUInt()
	ddsWidth = bs.readUShort()
	ddsHeight = bs.readUShort()
	ddsFlags = bs.readUShort()
	ddsUnk01 = bs.readUShort()
	ddsUnk02 = bs.readUInt()
	ddsUnk03 = bs.readUInt()
	ddsUnk04 = bs.readUInt()
	
	ddsData = bs.readBytes(ddsSize)
	ddsFmt = None
	if ddsType == 0x2421557C:
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 8)
		ddsData = rapi.imageDecodeDXT(ddsData, ddsWidth, ddsHeight, noesis.FOURCC_DXT1NORMAL)
		ddsFmt = noesis.NOESISTEX_RGBA32
	elif ddsType == 0x24215571:
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 16)
		ddsData = rapi.imageDecodeDXT(ddsData, ddsWidth, ddsHeight, noesis.FOURCC_ATI2)
		ddsFmt = noesis.NOESISTEX_RGBA32
	elif ddsType == 0x18280186:
		ddsData = rapi.imageUntile360Raw(ddsData, ddsWidth, ddsHeight, 4)
		ddsData = rapi.imageDecodeRaw(ddsData, ddsWidth, ddsHeight, "a8r8g8b8")
		ddsFmt = noesis.NOESISTEX_RGBA32
	elif ddsType == 0x18287FB2:
		ddsData = rapi.imageUntile360Raw(ddsData, ddsWidth, ddsHeight, 4)
		ddsData = rapi.imageDecodeRaw(ddsData, ddsWidth, ddsHeight, "a8r8g8b8")
		ddsFmt = noesis.NOESISTEX_RGBA32
	elif ddsType == 0x1A200152:#FIXME
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageDecodeDXT(ddsData, ddsWidth, ddsHeight, noesis.NOESISTEX_DXT1)
	elif ddsType == 0x1A200154:#
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 16)
		ddsData = rapi.imageDecodeDXT(ddsData, ddsWidth, ddsHeight, noesis.NOESISTEX_DXT5)
		ddsFmt = noesis.NOESISTEX_RGBA32
	elif ddsType == 0x1A207F73:#FIXME
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 8)
		ddsData = rapi.imageDecodeDXT(ddsData, ddsWidth, ddsHeight, noesis.NOESISTEX_DXT1)
		ddsFmt = noesis.NOESISTEX_RGBA32
	elif ddsType == 0x1A207F75:
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 16)
		ddsData = rapi.imageDecodeDXT(ddsData, ddsWidth, ddsHeight, noesis.NOESISTEX_DXT5)
		ddsFmt = noesis.NOESISTEX_RGBA32
	else:
		print("Fatal Error: " + "Unknown DDS type: " + str(hex(ddsType)) + " using default DXT1")
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 8)
	texList.append(NoeTexture("Texture", ddsWidth, ddsHeight, ddsData, ddsFmt))
	return 1

class meshFile(object): 
	def __init__(self, data):
		if iPlatform == 0: 
			self.inFile = NoeBitStream(data)
		elif iPlatform == 1:
			self.inFile = NoeBitStream(data, NOE_BIGENDIAN)
			rapi.rpgSetOption(noesis.RPGOPT_BIGENDIAN, 1)
		else: 
			print("Fatal Error: Unknown Platform ID: " + str(iPlatform))

		self.meshGroupIdx = 0
		self.boneList = []
		self.matList = []
		self.texList = []
		self.matNames = []
		self.offsetMeshStart = 0
	
	def loadHeader(self):
		bs = self.inFile
		bs.seek(0x10, NOESEEK_ABS)
		numOffsets = bs.readInt()
		bs.seek(0x18, NOESEEK_ABS)
		dataSize = bs.readInt()
		bs.seek(((numOffsets * 0x4) + 0x34) + dataSize, NOESEEK_ABS)
		self.offsetMeshStart = bs.getOffset()
		
	def loadMeshFile(self):
		bs = self.inFile
		
		bs.seek(self.offsetMeshStart, NOESEEK_ABS)
		
		uiMagic = bs.readUInt()
		uiUnk00 = bs.readUInt()
		uiMeshFileSize = bs.readUInt()
		uiUnk01 = bs.readUInt()
		
		bs.seek(0x78, NOESEEK_REL)#AABB MIN/MAX?
		
		uiOffsetMeshGroupInfo = bs.readUInt()
		
		uiUnk02 = bs.readUInt()
		uiOffsetMeshInfo = bs.readUInt()
		uiUnk03 = bs.readUInt()
		uiOffsetBoneMap = bs.readUInt()
		
		uiUnk04 = bs.readUInt()
		uiUnk05 = bs.readUInt()
		uiUnk06 = bs.readUInt()
		uiOffsetFaceData = bs.readUInt()
		
		uiUnk07 = bs.readUInt()
		usNumMeshGroups = bs.readUShort()
		usNumMesh = bs.readUShort()
		usNumBones = bs.readUShort()
		
		for i in range(usNumMesh):
			bs.seek(self.offsetMeshStart + uiOffsetMeshInfo + i * 0x50, NOESEEK_ABS)
			if debug:
				print("Mesh Info Start: " + str(bs.tell()))
			meshFile.buildMesh(self, [bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt()], i, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones)
			if debug:
				print("Mesh Info End: " + str(bs.tell()))
	
	def buildSkeleton(self):
		skelFileName = rapi.getDirForFilePath(rapi.getInputName()) + "skeleton.skl"
		if (rapi.checkFileExists(skelFileName)):
			print("Skeleton file detected!")
			print("Building Skeleton....")
			
			sd = rapi.loadIntoByteArray(skelFileName)
			
			if iPlatform == 0: 
				sd = NoeBitStream(sd)
			elif iPlatform == 1:
				sd = NoeBitStream(sd, NOE_BIGENDIAN)
				rapi.rpgSetOption(noesis.RPGOPT_BIGENDIAN, 1)
			else: 
				print("Fatal Error: Unknown Platform ID: " + str(iPlatform))
				return

			sd.seek(0x8C, NOESEEK_ABS)
			uiNumBones = sd.readInt()
			sd.seek(0xA0, NOESEEK_ABS)
		
			if uiNumBones > 0:
				for i in range(uiNumBones):
					sd.seek(0x10, NOESEEK_REL)
					sd.seek(0x10, NOESEEK_REL)

					boneUnk00 = sd.readFloat()
					fBoneXPos = sd.readFloat()
					fBoneYPos = sd.readFloat()
					fBoneZPos = sd.readFloat()
					
					boneUnk01 = sd.readInt()
					boneUnk02 = sd.readInt()
					boneUnk03 = sd.readShort()
					boneUnk04 = sd.readShort()
					iBonePID = sd.readInt()
					sd.seek(0x10, NOESEEK_REL)
					
					quat = NoeQuat([0, 0, 0, 1])
					mat = quat.toMat43()
					mat[3] = [fBoneXPos, fBoneZPos, -fBoneYPos]
					self.boneList.append(NoeBone(i, "bone%03i"%i, mat, None, iBonePID))
				self.boneList = rapi.multiplyBones(self.boneList)
			
	def buildMesh(self, meshInfo, meshIndex, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones):
		bs = self.inFile
		
		bs.seek(self.offsetMeshStart + meshInfo[12] + 0x8, NOESEEK_ABS)
		usNumVertexComponents = bs.readUShort()
		ucMeshVertStride = bs.readUByte()
		bs.seek(0x5, NOESEEK_REL)
			
		iMeshVertPos = -1
		iMeshNrmPos = -1
		iMeshTessNrmPos = -1
		iMeshTangPos = -1
		iMeshBiNrmPos = -1
		iMeshPckNTBPos = -1
		iMeshBwPos = -1
		iMeshBiPos = -1
		iMeshCol1Pos = -1
		iMeshCol2Pos = -1
		iMeshUV1Pos = -1
		iMeshUV2Pos = -1
		iMeshUV3Pos = -1
		iMeshUV4Pos = -1
		iMeshIIDPos = -1
		
		iMeshVertFlags = 0
		iMeshNrmFlags = 0
		iMeshTessNrmFlags = 0
		iMeshTangFlags = 0
		iMeshBiNrmFlags = 0
		iMeshPckNTBFlags = 0
		iMeshBwFlags = 0
		iMeshBiFlags = 0
		iMeshCol1Flags = 0
		iMeshCol2Flags = 0
		iMeshUV1Flags = 0
		iMeshUV2Flags = 0
		iMeshUV3Flags = 0
		iMeshUV4Flags = 0
		iMeshIIDFlags = 0
			
		for i in range(usNumVertexComponents):
			uiEntryHash = bs.readUInt()
			usEntryValue = bs.readUShort()
			ucEntryFlags = bs.readUByte()
			ucEntryNull = bs.readUByte()
			
			if uiEntryHash == 0xD2F7D823:#Position
				iMeshVertPos = usEntryValue
				iMeshVertFlags = ucEntryFlags
			elif uiEntryHash == 0x36F5E414:#Normal
				iMeshNrmPos = usEntryValue
			elif uiEntryHash == 0x3E7F6149:#TessellationNormal
				if debug:
					print("Unsupported Vertex Component: TessellationNormal! " + "Pos: " + str(usEntryValue))
			#	iMeshTessNrmPos = usEntryValue
			elif uiEntryHash == 0xF1ED11C3:#Tangent
				if debug:
					print("Unsupported Vertex Component: Tangent! " + "Pos: " + str(usEntryValue))
				iMeshTangPos = usEntryValue
			elif uiEntryHash == 0x64A86F01:#Binormal
				if debug:
					print("Unsupported Vertex Component: BiNormal! " + "Pos: " + str(usEntryValue))
			#	iMeshBiNrmPos = usEntryValue
			elif uiEntryHash == 0x9B1D4EA:#PackedNTB
				if debug:
					print("Unsupported Vertex Component: PackedNTB! " + "Pos: " + str(usEntryValue))
			#	iMeshPckNTBPos = usEntryValue
			elif uiEntryHash == 0x48E691C0:#SkinWeights
				iMeshBwPos = usEntryValue
			elif uiEntryHash == 0x5156D8D3:#SkinIndices
				iMeshBiPos = usEntryValue
			elif uiEntryHash == 0x7E7DD623:#Color1
				iMeshCol1Pos = usEntryValue
				if debug:
					print("Unsupported Vertex Component: Color1! " + "Pos: " + str(usEntryValue))
			elif uiEntryHash == 0x733EF0FA:#Color2
				if debug:
					print("Unsupported Vertex Component: Color2! " + "Pos: " + str(usEntryValue))
			#	iMeshCol2Pos = usEntryValue
			elif uiEntryHash == 0x8317902A:#Texcoord1
				iMeshUV1Pos = usEntryValue
			elif uiEntryHash == 0x8E54B6F3:#Texcoord2
				iMeshUV2Pos = usEntryValue
			elif uiEntryHash == 0x8A95AB44:#Texcoord3
				if debug:
					print("Unsupported Vertex Component: Texcoord3! " + "Pos: " + str(usEntryValue))
			#	iMeshUV3Pos = usEntryValue
			elif uiEntryHash == 0x94D2FB41:#Texcoord4
				if debug:
					print("Unsupported Vertex Component: Texcoord4! " + "Pos: " + str(usEntryValue))
			#	iMeshUV4Pos = usEntryValue
			elif uiEntryHash == 0xE7623ECF:#InstanceID
				if debug:
					print("Unsupported Vertex Component: InstanceID! " + "Pos: " + str(usEntryValue))
				iMeshUV2Pos = usEntryValue
			else:
				if debug:
					print("Unknown Vertex Component! Hash: " + str(hex((uiEntryHash))) + " value: " + str(usEntryValue))
			
		if meshInfo[1] != 0 and bSkinningEnabled != 0:
			bs.seek(self.offsetMeshStart + meshInfo[2], NOESEEK_ABS)
			boneMap = []
			for i in range(meshInfo[1]):
				boneMap.append(bs.readInt())
			rapi.rpgSetBoneMap(boneMap)
				
		for i in range(meshInfo[0]):
			bs.seek(self.offsetMeshStart + uiOffsetMeshGroupInfo + self.meshGroupIdx * 0x60, NOESEEK_ABS)
			self.meshGroupIdx += 1
			meshGroupInfo = [bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt()]
			
			rapi.rpgSetName("Mesh_" + str(meshIndex) + "_" + str(i))
			
			matName = str(self.meshGroupIdx-1) + ".matd"
			material = NoeMaterial(matName, "")
			material.setFlags(noesis.NMATFLAG_TWOSIDED, 0)
			if iPlatform == 0:
				material.setTexture(str(self.meshGroupIdx-1) + ".tr2pcd")
			else:
				material.setTexture(str(self.meshGroupIdx-1) + ".tr2x360")
				
			self.matList.append(material)
			self.matNames.append(matName)
			rapi.rpgSetMaterial(self.matNames[self.meshGroupIdx-1])
			
			rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))
			
			bs.seek(self.offsetMeshStart + uiOffsetFaceData + meshGroupInfo[4] * 0x2, NOESEEK_ABS)
			faceBuff = bs.readBytes(meshGroupInfo[5] * 0x6)
			
			bs.seek(self.offsetMeshStart + meshInfo[4], NOESEEK_ABS)
			vertBuff = bs.readBytes(meshInfo[16] * (ucMeshVertStride))
			
			rapi.rpgSetUVScaleBias(NoeVec3 ((16.0, 16.0, 16.0)), NoeVec3 ((16.0, 16.0, 16.0)))
			rapi.rpgSetTransform(NoeMat43((NoeVec3((1, 0, 0)), NoeVec3((0, 0, 1)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, 0)))))
		
			if iMeshVertPos != -1:
				if iPlatform == 0: #PC
					rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, ucMeshVertStride, iMeshVertPos)
				else:
					if iMeshVertFlags == 0x11:
						decodedVerts = rapi.swapEndianArray(rapi.decodeNormals32(vertBuff[iMeshVertPos:], ucMeshVertStride, -10, -10, -10, NOE_BIGENDIAN), 0x4)
						rapi.rpgBindPositionBufferOfs(decodedVerts, noesis.RPGEODATA_FLOAT, 0xC, 0x0)
					else:
						rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_SHORT, ucMeshVertStride, 	iMeshVertPos)
			if iMeshNrmPos != -1 and bNORMsEnabled != 0:
				if iPlatform == 0: #PC
					normList = []
					for n in range(meshInfo[16]):
						idx = ucMeshVertStride * n + iMeshNrmPos
						nz = float((vertBuff[idx]) / 255.0 * 2 - 1)
						ny = float((vertBuff[idx + 1]) / 255.0 * 2 - 1)
						nx = float((vertBuff[idx + 2]) / 255.0 * 2 - 1)
						l = math.sqrt(nx * nx + ny * ny + nz * nz)
						normList.append(nx / l)
						normList.append(ny / l)
						normList.append(nz / l)
					normBuff = struct.pack("<" + 'f'*len(normList), *normList)
					rapi.rpgBindNormalBufferOfs(normBuff, noesis.RPGEODATA_FLOAT, 0xC, 0x0)
				else:
					decodedNormals = rapi.swapEndianArray(rapi.decodeNormals32(vertBuff[iMeshNrmPos:], ucMeshVertStride, -10, -10, -10, NOE_BIGENDIAN), 0x4)
					rapi.rpgBindNormalBufferOfs(decodedNormals, noesis.RPGEODATA_FLOAT, 0xC, 0x0)
			#if iMeshTessNrmPos != -1:
			#	print("Unsupported")
			#if iMeshBiNrmPos != -1:
			#	print("Unsupported")
			#if iMeshPckNTBPos != -1:
			#	print("Unsupported")
			if iMeshBwPos != -1 and bSkinningEnabled != 0:
				weightList = []
				for w in range(meshInfo[16]):
					idx = ucMeshVertStride * w + iMeshBwPos
					weightList.append(float((vertBuff[idx]) / 255.0))
					weightList.append(float((vertBuff[idx + 1]) / 255.0))
					weightList.append(float((vertBuff[idx + 2]) / 255.0))
					weightList.append(float((vertBuff[idx + 3]) / 255.0))
				weightBuff = struct.pack("<" + 'f'*len(weightList), *weightList)
				rapi.rpgBindBoneWeightBufferOfs(weightBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0, 0x4)
			if iMeshBiPos != -1 and bSkinningEnabled != 0:
				rapi.rpgBindBoneIndexBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, ucMeshVertStride, iMeshBiPos, 0x4)	
			#if iMeshCol1Pos != -1 and bCOLsEnabled != 0:
			#	rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, ucMeshVertStride, iMeshCol1Pos, 0x4)	
			#if iMeshCol2Pos != -1:
			#	print("Unsupported")
			if iMeshUV1Pos != -1 and bUVsEnabled != 0:
				rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_SHORT, ucMeshVertStride, iMeshUV1Pos)
			if iMeshUV2Pos != -1 and bUVsEnabled != 0:
				rapi.rpgBindUV2BufferOfs(vertBuff, noesis.RPGEODATA_SHORT, ucMeshVertStride, iMeshUV2Pos)
			#if iMeshUV3Pos != -1:
			#	print("Unsupported")
			#if iMeshUV4Pos != -1:
			#	print("Unsupported")
			#if iMeshIIDPos != -1:
			#	print("Unsupported")
			if bRenderAsPoints:
				rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, meshInfo[16], noesis.RPGEO_POINTS, 0x1)
			else:
				rapi.rpgSetStripEnder(0x10000)
				rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, int(meshGroupInfo[5] * 0x3), noesis.RPGEO_TRIANGLE, 0x1)
			if bOptimizeMesh:
				rapi.rpgOptimize()
			rapi.rpgClearBufferBinds()
		
def meshLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	mesh = meshFile(data)
	if iPlatform == 0:
		mesh.loadHeader()
	mesh.loadMeshFile()
	mesh.buildSkeleton()
	try:
		mdl = rapi.rpgConstructModelSlim()
	except:
		mdl = NoeModel()
	mdl.setBones(mesh.boneList)
	mdl.setModelMaterials(NoeModelMaterials(mesh.texList, mesh.matList))
	mdlList.append(mdl);
	return 1