#Tomb Raider: Underworld/Lara Croft and The Guardian Of Light [PC/X360] - ".tr8mesh" Loader
#By Gh0stblade
#v2.4
#Special thanks: Chrrox
#Options: These are bools that enable/disable certain features! They are global and affect ALL platforms!
#Var							Effect
#Misc
#Mesh Global
fDefaultMeshScale = 1.0 		#Override mesh scale (default is 1.0)
bOptimizeMesh = 0				#Enable optimization (remove duplicate vertices, optimize lists for drawing) (1 = on, 0 = off)
bMaterialsEnabled = 1			#Materials (1 = on, 0 = off)
bRenderAsPoints = 0				#Render mesh as points without triangles drawn (1 = on, 0 = off)
#Vertex Components
bNORMsEnabled = 1				#Normals (1 = on, 0 = off)
bUVsEnabled = 1					#UVs (1 = on, 0 = off)
bCOLsEnabled = 0				#Vertex colours (1 = on, 0 = off)
bSkinningEnabled = 1			#Enable skin weights (1 = on, 0 = off)
#Gh0stBlade ONLY
debug = 0 						#Prints debug info (1 = on, 0 = off)
bDumpTris = 0					#Dump triangles to binary file

from inc_noesis import *
import math

def registerNoesisTypes():
	handle = noesis.register("Tomb Raider: Underworld/Lara Croft and The Guardian Of Light 3D Mesh [PC/X360]", ".tr8mesh")
	noesis.setHandlerTypeCheck(handle, meshCheckType)
	noesis.setHandlerLoadModel(handle, meshLoadModel)
	
	handle = noesis.register("Tomb Raider: Underworld/Lara Croft and The Guardian Of Light 2D Texture [PC]", ".tr8pcd9")
	noesis.setHandlerTypeCheck(handle, pcd9CheckType)
	noesis.setHandlerLoadRGBA(handle, pcd9LoadDDS)

	handle = noesis.register("Tomb Raider: Underworld/Lara Croft and The Guardian Of Light 2D Texture [X360]", ".tr8x360")
	noesis.setHandlerTypeCheck(handle, x360CheckType)
	noesis.setHandlerLoadRGBA(handle, x360LoadDDS)
	
	noesis.logPopup()
	return 1
	
def meshCheckType(data):
	bs = NoeBitStream(data)
	uiMagic = bs.read("IIII")
	
	global iPlatform
	global iMeshType
	
	iPlatform = -1
	iMeshType = -1
	
	if uiMagic[0] == 0xBEEBBEEB and uiMagic[1] == 0xBEEBBEEB and uiMagic[2] == 0xBEEBBEEB and uiMagic[3] == 0xBEEBBEEB:#RenderMesh LE
		if debug:
			print("Render Mesh LE!")
		iPlatform = 0#PC
		iMeshType = 0#RenderMesh
		return 1
	elif uiMagic[0] == 0xEBBEEBBE and uiMagic[1] == 0xEBBEEBBE and uiMagic[2] == 0xEBBEEBBE and uiMagic[3] == 0xEBBEEBBE:#RenderMesh BE
		if debug:
			print("Render Mesh BE!")
		iPlatform = 1#XENON
		iMeshType = 0#RenderMesh
		return 1
	elif uiMagic[0] != 0xBEEBBEEB and uiMagic[1] == 0xBEEBBEEB and uiMagic[2] == 0xBEEBBEEB and uiMagic[3] == 0xBEEBBEEB:#SceneMesh LE
		if debug:
			print("Scene Mesh LE!")
		iPlatform = 0#PC
		iMeshType = 1#RenderMesh
		return 1
	elif uiMagic[0] != 0xEBBEEBBE and uiMagic[1] == 0xEBBEEBBE and uiMagic[2] == 0xEBBEEBBE and uiMagic[3] == 0xEBBEEBBE:#SceneMesh BE
		if debug:
			print("Scene Mesh BE!")
		iPlatform = 1#XENON
		iMeshType = 1#RenderMesh
		return 1
	else:
		print("Fatal Error: Unsupported Mesh header! " + str(uiMagic))
	return 0

def pcd9CheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	if magic == 0x39444350:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected PCD9!"))
		return 0
		
def x360CheckType(data):
	bs = NoeBitStream(data, NOE_BIGENDIAN)
	magic = bs.readUInt()
	if magic == 0x58333630:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected X360!"))
		return 0
		
def pcd9LoadDDS(data, texList):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	ddsType = bs.readUInt()
	ddsSize = bs.readUInt()
	bs.seek(0x4, NOESEEK_REL)
	ddsWidth = bs.readUShort()
	ddsHeight = bs.readUShort()
	ddsFlags = bs.readByte()
	ddsMipCount = bs.readByte()
	ddsType2 = bs.readUShort()
	ddsData = bs.readBytes(ddsSize)
	ddsFmt = None
	if ddsType == 0x31545844:
		ddsFmt = noesis.NOESISTEX_DXT1
	elif ddsType == 0x35545844:
		ddsFmt = noesis.NOESISTEX_DXT5
	elif ddsType == 0x15:
		ddsData = rapi.imageDecodeRaw(ddsData, ddsWidth, ddsHeight, "a8a8a8a8")
		ddsFmt = noesis.NOESISTEX_RGBA32
	else: 
		print("Fatal Error: " + "Unknown DDS type: " + str(hex(ddsType)) + " using default DXT1")
	texList.append(NoeTexture("Texture", ddsWidth, ddsHeight, ddsData, ddsFmt))
	return 1

def x360LoadDDS(data, texList):
	bs = NoeBitStream(data, NOE_BIGENDIAN)
	ddsSize = int(len(data) - 0x18)
	magic = bs.readUInt()
	ddsType = bs.readUInt()
	ddsUnk00 = bs.readUInt()
	ddsUnk01 = bs.readUInt()
	ddsWidth = bs.readUShort()
	ddsHeight = bs.readUShort()
	ddsFlags = bs.readUShort()
	ddsUnk01 = bs.readUShort()
	ddsData = bs.readBytes(ddsSize)
	ddsFmt = None
	if ddsType == 0x1A200152:
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 8)
	elif ddsType == 0x1A200153:
		ddsFmt = noesis.NOESISTEX_DXT3
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 16)
	elif ddsType == 0x1A200154:
		ddsFmt = noesis.NOESISTEX_DXT5
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 16)
	elif ddsType == 0x1A200171:
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 16)
		ddsData = rapi.imageDecodeDXT(ddsData, ddsWidth, ddsHeight, noesis.FOURCC_ATI2)
		ddsFmt = noesis.NOESISTEX_RGBA32
	elif ddsType == 0x1A20017C:
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 8)
		ddsData = rapi.imageDecodeDXT(ddsData, ddsWidth, ddsHeight, noesis.FOURCC_DXT1NORMAL)
		ddsFmt = noesis.NOESISTEX_RGBA32
	elif ddsType == 0x18280186:
		ddsData = rapi.imageUntile360Raw(ddsData, ddsWidth, ddsHeight, 4)
		ddsData = rapi.imageDecodeRaw(ddsData, ddsWidth, ddsHeight, "a8r8g8b8")
		ddsFmt = noesis.NOESISTEX_RGBA32
	else:
		print("Fatal Error: " + "Unknown DDS type: " + str(hex(ddsType)) + " using default DXT1")
		ddsFmt = noesis.NOESISTEX_DXT1
		ddsData = rapi.imageUntile360DXT(rapi.swapEndianArray(ddsData, 2), ddsWidth, ddsHeight, 8)
	texList.append(NoeTexture("Texture", ddsWidth, ddsHeight, ddsData, ddsFmt))
	return 1
	
class meshFile(object): 
	def __init__(self, data):
		self.inFile = None
		self.texExtension = ""
		
		if iPlatform == 0: 
			self.inFile = NoeBitStream(data)
			self.texExtension = ".tr8pcd9"
		elif iPlatform == 1:
			self.inFile = NoeBitStream(data, NOE_BIGENDIAN)
			rapi.rpgSetOption(noesis.RPGOPT_BIGENDIAN, 1)
			self.texExtension = ".tr8x360"
		else: 
			print("Fatal Error: Unknown Platform ID: " + str(iPlatform))
			
		self.fileSize = int(len(data))
		
		self.meshGroupIdx = 0
		self.offsetMeshStart = -1
		self.offsetStart = -1
		self.offsetMatInfo = -1
		self.numBones = -1
		self.numMeshes = 0
		
		self.meshOffsets = []
		self.boneList = []
		self.boneMap = []
		self.matList = []
		self.matNames = []
		self.texList = []
		self.texNames = []
		
	def loadMesh(self):
		bs = self.inFile
		bs.seek(0x10, NOESEEK_ABS)
		self.offsetMeshStart = bs.getOffset()
		
		uiMagic = bs.readUInt()
		uiUnk00 = bs.readUInt()
		uiOffsetMatInfo = bs.readUInt()
		uiUnk01 = bs.readUInt()
		
		bs.seek(0x5C, NOESEEK_REL)#AABB MIN/MAX?
		
		uiOffsetMeshGroupInfo = bs.readUInt()
		
		uiOffsetMeshInfo = bs.readUInt()
		uiOffsetBoneMap = bs.readUInt()
		uiOffsetFaceData = bs.readUInt()
		usNumMeshGroups = bs.readUShort()
		usNumMesh = bs.readUShort()
		self.numBones = bs.readUShort()
		
		bs.seek(self.offsetMeshStart + uiOffsetMatInfo + 0x4, NOESEEK_ABS)#why 0x4?
		#bs.seek(((bs.tell() + 0x7) & ~0x7), NOESEEK_ABS)#FIX crash on some meshes? VERIFY
		
		uiNumMatHashes = bs.readUInt()
		
		for i in range(uiNumMatHashes):#@FIXME
			bs.seek(self.offsetMeshStart + uiOffsetMatInfo + 0x8 + i * 0x4, NOESEEK_ABS)
			meshFile.loadMaterial(self, bs.readUInt())
			
		for i in range(usNumMesh):
			bs.seek(self.offsetMeshStart + uiOffsetMeshInfo + i * 0x34, NOESEEK_ABS)
			if debug:
				print("Mesh Info Start: " + str(bs.tell()))
			meshFile.buildMesh(self, [bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt()], i, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, self.numBones)
			if debug:
				print("Mesh Info End: " + str(bs.tell()))
				
				
	def loadScene(self):
		bs = self.inFile
		
		self.offsetMeshStart = bs.readUInt()
		
		bs.seek(0x10, NOESEEK_ABS)
		
		uiNumLightMaterials = bs.readUInt()
		bs.seek(uiNumLightMaterials * 0x4, NOESEEK_REL)
		
		uiNumMaterials = bs.readUInt()
		for i in range(uiNumMaterials):
			bs.seek(0x10 + 0x4 + (uiNumLightMaterials * 0x4) + 0x4 + (i * 0x4), NOESEEK_ABS)
			meshFile.loadMaterial(self, bs.readUInt())
		
		bs.seek(self.offsetMeshStart, NOESEEK_ABS)
		
		bs.seek(0x20, NOESEEK_REL)#AABB MIN/MAX?
		
		uiUnk00 = bs.readUInt()
		uiNumFaceGroups = bs.readUInt()
		uiOffsetMeshGroupInfo = bs.readUInt()
		uiNumMeshGroups = bs.readUInt()
		
		uiOffsetVertInfo = bs.readUInt()
		uiUnk05 = bs.readUInt()
		uiUnk05 = bs.readUInt()
		uiOffsetVertGroupInfo = bs.readUInt()
		
		uiNumMesh = bs.readUInt()
		uiOffsetMeshFaceGroupInfo = bs.readUInt()
		uiUnk10 = bs.readUInt()
		uiUnk11 = bs.readUInt()
		
		uiOffsetFaceData = bs.readUInt()
		uiNumFaces = bs.readUInt()
		uiUnk14 = bs.readUInt()
		uiUnk15 = bs.readUInt()
		
		meshGroupInfo = []
		bs.seek(self.offsetMeshStart + uiOffsetMeshGroupInfo, NOESEEK_ABS)
		
		for i in range(uiNumMeshGroups):
			meshGroupInfo.append([bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt()])
	
		bs.seek(self.offsetMeshStart + uiOffsetVertInfo, NOESEEK_ABS)
		meshFVF = []
		for i in range(uiNumMesh):
			FVFInfo = []
			bs.seek(0x8, NOESEEK_REL)
			usNumVertexComponents = bs.readUShort()
			ucMeshVertStride = bs.readUByte()
			bs.seek(0x5, NOESEEK_REL)
			for j in range(usNumVertexComponents):
				uiEntryHash = bs.readUInt()
				usEntryValue = bs.readUShort()
				ucEntryType = bs.readUByte()
				ucEntryNull = bs.readUByte()
				FVFInfo.append([usNumVertexComponents, ucMeshVertStride, uiEntryHash, usEntryValue, ucEntryType, ucEntryNull])
			meshFVF.append(FVFInfo)
		#@OPTIMISE, Read Mesh Vertex buffers once not multiple times!
		for i in range(uiNumMesh):
			for j in range(uiNumFaceGroups):
				bs.seek(self.offsetMeshStart + uiOffsetMeshFaceGroupInfo + (j * 0x4), NOESEEK_ABS)
				uiMeshFaceGroupOffset = bs.readUInt()
				if uiMeshFaceGroupOffset != 0x0:
					bs.seek(self.offsetMeshStart + uiMeshFaceGroupOffset, NOESEEK_ABS)
					usMeshFaceGroupCount = bs.readUShort()
					usMeshFaceGroupIndex = bs.readUShort()
					for k in range(usMeshFaceGroupCount):
						bs.seek(self.offsetMeshStart + uiMeshFaceGroupOffset + 0x4 + (k * 0x8), NOESEEK_ABS)
						meshFaceGroupInfo = [bs.readUShort(), bs.readUShort(), bs.readUInt()]
						if meshGroupInfo[meshFaceGroupInfo[0]][1] == i:
							meshFile.buildScene(self, meshFaceGroupInfo, i, uiOffsetFaceData, meshGroupInfo[meshFaceGroupInfo[0]], uiOffsetVertInfo, uiOffsetVertGroupInfo, meshFVF[i])
						
				
	def buildScene(self, meshFaceGroupInfo, meshIndex, uiOffsetFaceData, meshGroupInfo, uiOffsetVertInfo, uiOffsetVertGroupInfo, meshFVF):
		bs = self.inFile
		
		iMeshVertPos = -1
		iMeshNrmPos = -1
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
		
		for i in range(meshFVF[0][0]):
			if meshFVF[i][2] == 0xD2F7D823:#Position
				iMeshVertPos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x36F5E414:#Normal
				iMeshNrmPos = meshFVF[i][3]
			elif meshFVF[i][2] == 0xF1ED11C3:#Tangent
				iMeshTangPos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x64A86F01:#Binormal
				if debug:
					print("Unsupported Vertex Component: BiNormal! " + "Pos: " + str(meshFVF[i][3]))
			#	iMeshBiNrmPos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x9B1D4EA:#PackedNTB
				if debug:
					print("Unsupported Vertex Component: PackedNTB! " + "Pos: " + str(meshFVF[i][3]))
			#	iMeshPckNTBPos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x48E691C0:#SkinWeights
				iMeshBwPos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x5156D8D3:#SkinIndices
				iMeshBiPos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x7E7DD623:#Color1
				iMeshCol1Pos = meshFVF[i][3]
				if debug:
					print("Unsupported Vertex Component: Color1! " + "Pos: " + str(meshFVF[i][3]))
			elif meshFVF[i][2] == 0x733EF0FA:#Color2
				if debug:
					print("Unsupported Vertex Component: Color2! " + "Pos: " + str(meshFVF[i][3]))
			#	iMeshCol2Pos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x8317902A:#Texcoord1
				iMeshUV1Pos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x8E54B6F3:#Texcoord2
				iMeshUV2Pos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x8A95AB44:#Texcoord3
				if debug:
					print("Unsupported Vertex Component: Texcoord3! " + "Pos: " + str(meshFVF[i][3]))
			#	iMeshUV3Pos = meshFVF[i][3]
			elif meshFVF[i][2] == 0x94D2FB41:#Texcoord4
				if debug:
					print("Unsupported Vertex Component: Texcoord4! " + "Pos: " + str(meshFVF[i][3]))
			#	iMeshUV4Pos = meshFVF[i][3]
			elif meshFVF[i][2] == 0xE7623ECF:#InstanceID
				if debug:
					print("Unsupported Vertex Component: InstanceID! " + "Pos: " + str(meshFVF[i][3]))
				iMeshUV2Pos = meshFVF[i][3]
			else:
				if debug:
					print("Unknown Vertex Component! Hash: " + str(hex((meshFVF[i][2]))) + " value: " + str(meshFVF[i][3]))
		
		bs.seek(self.offsetMeshStart + uiOffsetVertGroupInfo + (meshIndex  * 0x10), NOESEEK_ABS)
		vertGroupInfo = [bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt()]
			
		rapi.rpgSetName("Mesh_" + str(self.numMeshes))
		self.numMeshes += 1
		rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))
			
		if bMaterialsEnabled != 0:
			rapi.rpgSetMaterial(self.matNames[meshGroupInfo[0]])
			
		bs.seek(self.offsetMeshStart + uiOffsetFaceData + meshFaceGroupInfo[2] * 0x2, NOESEEK_ABS)
		faceBuff = bs.readBytes(meshFaceGroupInfo[1] * 0x2)
					
		bs.seek(self.offsetMeshStart + vertGroupInfo[0], NOESEEK_ABS)
		vertBuff = bs.readBytes(meshFVF[i][1] * vertGroupInfo[2])
					
		rapi.rpgSetUVScaleBias(NoeVec3 ((16.0, 16.0, 16.0)), NoeVec3 ((16.0, 16.0, 16.0)))
		rapi.rpgSetTransform(NoeMat43((NoeVec3((1, 0, 0)), NoeVec3((0, 0, 1)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, 0)))))
					 
		if iMeshVertPos != -1:
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshFVF[i][1], iMeshVertPos)
		if iMeshNrmPos != -1 and bNORMsEnabled != 0: #PC, convert normals. Thanks to Dunsan from UnpackTRU just a custom version
			if iPlatform == 0:
				normList = []
				for n in range(meshInfo[10]):
					idx = meshFVF[i][1] * n + iMeshNrmPos
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
				decodedNormals = rapi.swapEndianArray(rapi.decodeNormals32(vertBuff[iMeshNrmPos:], meshFVF[i][1], -10, -10, -10, NOE_BIGENDIAN), 0x4)
				rapi.rpgBindNormalBufferOfs(decodedNormals, noesis.RPGEODATA_FLOAT, 0xC, 0x0)
		#if iMeshTessNrmPos != -1:
		#	print("Unsupported")
		#if iMeshTangPos != -1:
		#	rapi.rpgBindTangentBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshFVF[i][1], iMeshTangPos, 0x4)
		#if iMeshBiNrmPos != -1:
		#	print("Unsupported")
		#if iMeshPckNTBPos != -1:
		#	print("Unsupported")
		if iMeshBwPos != -1 and bSkinningEnabled != 0:
			rapi.rpgBindBoneWeightBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshFVF[i][1], iMeshBwPos, 0x4)
		if iMeshBiPos != -1 and bSkinningEnabled != 0:
			rapi.rpgBindBoneIndexBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshFVF[i][1], iMeshBiPos, 0x4)
		if iMeshCol1Pos != -1 and bCOLsEnabled != 0:
			rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshFVF[i][1], iMeshCol1Pos, 0x4)	
		#if iMeshCol2Pos != -1:
		#	print("Unsupported")
		if iMeshUV1Pos != -1 and bUVsEnabled != 0:
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_SHORT, meshFVF[i][1], iMeshUV1Pos)
		if iMeshUV2Pos != -1 and bUVsEnabled != 0:
			rapi.rpgBindUV2BufferOfs(vertBuff, noesis.RPGEODATA_SHORT, meshFVF[i][1], iMeshUV2Pos)
		#if iMeshUV3Pos != -1:
		#	print("Unsupported")
		#if iMeshUV4Pos != -1:
		#	print("Unsupported")
		#if iMeshIIDPos != -1:
		#	print("Unsupported")
		#bRenderAsPoints = 1
		if bRenderAsPoints:
			rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, vertGroupInfo[2], noesis.RPGEO_POINTS, 0x1)
		else:
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshFaceGroupInfo[1], noesis.RPGEO_TRIANGLE, 0x1)
		if bOptimizeMesh:
			rapi.rpgOptimize()
		rapi.rpgClearBufferBinds()
		
	def loadMaterial(self, uiMatHash):
		colourList = []
		matName = str(hex(uiMatHash) + ".matd").replace("0x","")
		matFilePath = rapi.getDirForFilePath(rapi.getInputName()) + matName
		material = NoeMaterial(matName, "")
		
		if debug:
			print("Material :" + matName)
		
		if (rapi.checkFileExists(matFilePath)):
			bs = rapi.loadIntoByteArray(matFilePath)
			
			if iPlatform == 0:
				bs = NoeBitStream(bs)
			elif iPlatform == 1:
				bs = NoeBitStream(bs, NOE_BIGENDIAN)
				
			matHdr = [bs.readUShort(), bs.readUShort(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt() , bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUInt(), bs.readUInt()]
			
			bs.seek(matHdr[1], NOESEEK_ABS)
			
			for i in range(matHdr[16] + 1):
				matEntry = [bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt()]
				bs.seek(0x1C * matEntry[2], NOESEEK_REL)
				bs.seek(((bs.tell() + 0xF) & ~0xF), NOESEEK_ABS)
				
			for i in range(matHdr[29]):
				colourList.append([bs.readFloat(), bs.readFloat(), bs.readFloat(), bs.readFloat()])
				
			diffuseDetected = 0
			temp = bs.getOffset()
			
			for i in range(matHdr[26]):
				texName = str(hex(bs.readUInt()) + self.texExtension).replace("0x","")
				
				texUnk00 = bs.readUInt()
				texType = bs.readUInt()
				texIdx = bs.readUShort()
				texFlags = bs.readShort()
				texFlags = 1
				if texType == 1 and diffuseDetected == 0:
					diffuseDetected = 1
					material.setTexture(texName)
				else:
					if debug:
						print("Fatal Error: Unknown texture type: " + str(texType))
						
			if diffuseDetected == 0: 
				bs.seek(temp, NOESEEK_ABS)
				for i in range(matHdr[26]):
					texName = str(hex(bs.readUInt()) + self.texExtension).replace("0x","")
					
					texUnk00 = bs.readUInt()
					texType = bs.readUInt()
					texIdx = bs.readUShort()
					texFlags = bs.readShort()
					
					if texType == 0:
						diffuseDetected = 1
						material.setTexture(texName)
					else:
						if debug:
							print("Fatal Error: Unknown texture type: " + str(texType))
		else:
			print("Fatal Error: Material does not exist!")
		material.setFlags(noesis.NMATFLAG_TWOSIDED, 0)
		self.matList.append(material)
		self.matNames.append(matName)
			
	def buildSkeleton(self):
		bs = self.inFile
		bs.seek(self.fileSize - self.numBones * 0x40, NOESEEK_ABS)
		
		if self.numBones > 0:
			for i in range(self.numBones):
				bs.seek(0x20, NOESEEK_REL)
				fBoneXPos = bs.readFloat()
				fBoneYPos = bs.readFloat()
				fBoneZPos = bs.readFloat()
				bs.seek(0xC, NOESEEK_REL)
				iBonePID = bs.readInt()
				bs.seek(0x4, NOESEEK_REL)
				quat = NoeQuat([0, 0, 0, 1])
				mat = quat.toMat43()
				mat[3] = [fBoneXPos, fBoneZPos, -fBoneYPos]
				self.boneList.append(NoeBone(i, "bone%03i"%i, mat, None, iBonePID))
			self.boneList = rapi.multiplyBones(self.boneList)
			
	def buildMesh(self, meshInfo, meshIndex, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones):
		bs = self.inFile

		bs.seek(self.offsetMeshStart + meshInfo[9] + 0x8, NOESEEK_ABS)
		usNumVertexComponents = bs.readUShort()
		ucMeshVertStride = bs.readUByte()
		bs.seek(0x5, NOESEEK_REL)
		
		iMeshVertPos = -1
		iMeshNrmPos = -1
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
			
		for i in range(usNumVertexComponents):
			uiEntryHash = bs.readUInt()
			usEntryValue = bs.readUShort()
			ucEntryType = bs.readUByte()
			ucEntryNull = bs.readUByte()
			
			if uiEntryHash == 0xD2F7D823:#Position
				iMeshVertPos = usEntryValue
			elif uiEntryHash == 0x36F5E414:#Normal
				iMeshNrmPos = usEntryValue
			elif uiEntryHash == 0xF1ED11C3:#Tangent
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
					
		if meshInfo[3] != 0 and bSkinningEnabled != 0:
			bs.seek(self.offsetMeshStart + meshInfo[4], NOESEEK_ABS)
			boneMap = []
			for i in range(meshInfo[3]):
				boneMap.append(bs.readInt())
			rapi.rpgSetBoneMap(boneMap)
				
		for i in range(meshInfo[2]):
			bs.seek(self.offsetMeshStart + uiOffsetMeshGroupInfo + self.meshGroupIdx * 0x40, NOESEEK_ABS)
			self.meshGroupIdx += 1
			meshGroupInfo = [bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt()]
			
			rapi.rpgSetName("Mesh_" + str(meshIndex) + "_" + str(i))
			rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))
			
			if bMaterialsEnabled != 0:
				rapi.rpgSetMaterial(self.matNames[meshGroupInfo[10]])
			
			bs.seek(self.offsetMeshStart + uiOffsetFaceData + meshGroupInfo[4] * 0x2, NOESEEK_ABS)
			faceBuff = bs.readBytes(meshGroupInfo[5] * 0x6)
					
			bs.seek(self.offsetMeshStart + meshInfo[5], NOESEEK_ABS)
			vertBuff = bs.readBytes(meshInfo[10] * ucMeshVertStride)
					
			rapi.rpgSetUVScaleBias(NoeVec3 ((16.0, 16.0, 16.0)), NoeVec3 ((16.0, 16.0, 16.0)))
			rapi.rpgSetTransform(NoeMat43((NoeVec3((1, 0, 0)), NoeVec3((0, 0, 1)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, 0)))))
					 
			if iMeshVertPos != -1:
				rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, ucMeshVertStride, iMeshVertPos)
			if iMeshNrmPos != -1 and bNORMsEnabled != 0: #PC, convert normals. Thanks to Dunsan from UnpackTRU just a custom version
				if iPlatform == 0:
					normList = []
					for n in range(meshInfo[10]):
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
			#if iMeshTangPos != -1:
			#	rapi.rpgBindTangentBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, ucMeshVertStride, iMeshTangPos, 0x4)
			#if iMeshBiNrmPos != -1:
			#	print("Unsupported")
			#if iMeshPckNTBPos != -1:
			#	print("Unsupported")
			if iMeshBwPos != -1 and bSkinningEnabled != 0:
				if iPlatform == 0:
					weightList = []
					for w in range(meshInfo[10]):
						idx = ucMeshVertStride * w + iMeshBwPos
						weightList.append(float((vertBuff[idx]) / 255.0))
						weightList.append(float((vertBuff[idx + 1]) / 255.0))
						weightList.append(float((vertBuff[idx + 2]) / 255.0))
						weightList.append(float((vertBuff[idx + 3]) / 255.0))
					weightBuff = struct.pack("<" + 'f'*len(weightList), *weightList)
					rapi.rpgBindBoneWeightBufferOfs(weightBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0, 0x4)
				else:
					weightList = []
					for w in range(meshInfo[10]):
						idx = ucMeshVertStride * w + iMeshBwPos
						weightList.append(float((vertBuff[idx]) / 255.0))
						weightList.append(float((vertBuff[idx + 1]) / 255.0))
						weightList.append(float((vertBuff[idx + 2]) / 255.0))
						weightList.append(float((vertBuff[idx + 3]) / 255.0))
					weightBuff = struct.pack(">" + 'f'*len(weightList), *weightList)
					rapi.rpgBindBoneWeightBufferOfs(weightBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0, 0x4)
			if iMeshBiPos != -1 and bSkinningEnabled != 0:
				rapi.rpgBindBoneIndexBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, ucMeshVertStride, iMeshBiPos, 0x4)
			if iMeshCol1Pos != -1 and bCOLsEnabled != 0:
				rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, ucMeshVertStride, iMeshCol1Pos, 0x4)	
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
				rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, meshInfo[10], noesis.RPGEO_POINTS, 0x1)
			else:
				rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, int(meshGroupInfo[5] * 0x3), noesis.RPGEO_TRIANGLE, 0x1)
			if bOptimizeMesh:
				rapi.rpgOptimize()
			rapi.rpgClearBufferBinds()

def meshLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	mesh = meshFile(data)
	if iMeshType == 0:
		mesh.loadMesh()
		mesh.buildSkeleton()
	elif iMeshType == 1:
		mesh.loadScene()
	else:
		print("Fatal Error: Unknown mesh type: " + str(iMeshType))
	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()
	if len(mesh.boneList):
		mdl.setBones(mesh.boneList)
	mdl.setModelMaterials(NoeModelMaterials(mesh.texList, mesh.matList))
	mdlList.append(mdl);
	return 1