#Tomb Raider: Definitive Edition [Orbis] - ".trdemesh" Loader
#By Gh0stblade
#v1.3
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

from inc_noesis import *
import math

def registerNoesisTypes():
	handle = noesis.register("Tomb Raider: Definitive Edition [PS4]", ".trdemesh")
	noesis.setHandlerTypeCheck(handle, meshCheckType)
	noesis.setHandlerLoadModel(handle, meshLoadModel)
	
	handle = noesis.register("Tomb Raider: Definitive Edition [PS4]", ".pcd")
	noesis.setHandlerTypeCheck(handle, ps4tCheckType)
	noesis.setHandlerLoadRGBA(handle, ps4tLoadDDS)
	
	noesis.logPopup()
	return 1

def meshCheckType(data):
	bs = NoeBitStream(data)
	
	uiMagic = bs.readUInt()
	if uiMagic == 0x6873654D:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(uiMagic) + " expected 'hsem'!"))
		return 0
		
def ps4tCheckType(data):
	bs = NoeBitStream(data)
	uiMagic = bs.readUInt()
	if uiMagic == 0x54345350:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(uiMagic) + " expected PS4T!"))
		return 0
		
def ps4tLoadDDS(data, texList):
	bs = NoeBitStream(data)
	
	isBlockCompressed = False
	isReOrdered = False
	isTiled = False
	dataOfs = 0
	bitsPerPixel = 8
	texFmt = noesis.NOESISTEX_RGBA32
		
	magic = bs.readUInt()
	textureDataSize = bs.readUInt()
	uiPcdUnk00 = bs.readUInt()
	
	textureType = bs.readUByte()
	bs.seek(3, NOESEEK_REL)
	
	uiPcdWidth = bs.readUInt()
	uiPcdHeight = bs.readUInt()
	uiPcdFlags = bs.readUInt()
	uiPcdUnk01 = bs.readUInt()
	
	bPcdData = bs.readBytes(textureDataSize)
	print(str(bs.getOffset()))
	if textureType == 0x23:
		isBlockCompressed = True
		isTiled = True
		bitsPerPixel = 4
		dataOfs = 32
		decode = noesis.FOURCC_DXT1
	elif textureType == 0x25:
		isBlockCompressed = True
		isTiled = True
		bitsPerPixel = 8
		dataOfs = 32
		decode = noesis.NOESISTEX_DXT5
	else:
		print("Fatal Error: Unsupported texture type: " + str(textureType))
		
	if isTiled is True:
		w, h = uiPcdWidth, uiPcdHeight
		tileW = 32 if isBlockCompressed is True else 8
		tileH = 32 if isBlockCompressed is True else 8
		w = ((w+(tileW-1)) & ~(tileW-1))
		h = ((h+(tileH-1)) & ~(tileH-1))
		#organized into tiled rows of morton-ordered blocks
		rowSize = (w*tileH*bitsPerPixel) // 8
		reorderedImageData = bytearray()
		for y in range(0, h//tileH):
			if isBlockCompressed is True:
				decodedRow = rapi.imageFromMortonOrder(data[dataOfs:dataOfs+rowSize], w>>2, tileH>>2, bitsPerPixel*2)
			else:
				decodedRow = rapi.imageFromMortonOrder(data[dataOfs:dataOfs+rowSize], w, tileH, bitsPerPixel//8)
			dataOfs += rowSize
			reorderedImageData += decodedRow
		bPcdData = reorderedImageData
		bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, decode)
	if isReOrdered is True:
		bPcdData = rapi.imageDecodeRaw(bPcdData, uiPcdWidth, uiPcdHeight, "p8r8g8b8")
	tex1 = NoeTexture(str(1), uiPcdWidth, uiPcdHeight, bPcdData, texFmt)
	texList.append(tex1)
		
	#if gPcdFmt != None:
	#	texList.append(NoeTexture("Texture", int(uiPcdWidth), int(uiPcdHeight), bPcdData, gPcdFmt))
	return 1
	
class meshFile(object):

	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.boneList = []
		self.matNames = []
		self.matList = []
		self.texList = []
		self.numMats = 0
		self.offsetBoneInfo = -1
		self.offsetBoneInfo2 = -1
		self.offsetMeshStart = 0
		self.offsetMatInfo = -1
		self.offsetStart = 0
		self.meshGroupIdx = 0

	def loadHeader(self):
		bs = self.inFile
		numOffsets = bs.readInt()
		bs.seek(0x10, NOESEEK_ABS)
		numOffsets2 = bs.readInt()
		bs.seek(0x18, NOESEEK_ABS)
		self.offsetMeshStart = bs.readInt()
		bs.seek(0x28, NOESEEK_ABS)
		self.offsetMatInfo = bs.readInt()
		bs.seek(((numOffsets * 0x8) + 0x4), NOESEEK_ABS)
		self.offsetBoneInfo = bs.readInt()
		self.offsetBoneInfo2 = bs.readInt()
		bs.seek(((0x14 + numOffsets * 0x8) + numOffsets2 * 0x4), NOESEEK_ABS)
		self.offsetStart = bs.getOffset()
		
	def loadMeshFile(self):
		bs = self.inFile
		bs.seek(self.offsetStart + self.offsetMeshStart, NOESEEK_ABS)
		
		uiMagic = bs.readUInt()
		uiUnk00 = bs.readUInt()
		uiMeshFileSize = bs.readUInt()
		uiUnk01 = bs.readUInt()
		
		bs.seek(0x60, NOESEEK_REL)#AABB MIN/MAX?
		
		uiUnk02 = bs.readUInt()
		bs.seek(4, NOESEEK_REL)#64bit
		
		uiOffsetMeshGroupInfo = bs.readUInt()
		bs.seek(4, NOESEEK_REL)#64bit
		
		uiOffsetMeshInfo = bs.readUInt()
		bs.seek(4, NOESEEK_REL)#64bit
		
		uiOffsetBoneMap = bs.readUInt()
		bs.seek(4, NOESEEK_REL)#64bit
		
		uiOffsetBoneMap = bs.readUInt()
		bs.seek(4, NOESEEK_REL)#64bit
		
		uiOffsetFaceData = bs.readUInt()
		bs.seek(4, NOESEEK_REL)#64bit
		
		usNumMeshGroups = bs.readUShort()
		usNumMesh = bs.readUShort()
		usNumBones = bs.readUShort()
		
		for i in range(usNumMesh):
			bs.seek(self.offsetStart + self.offsetMeshStart + uiOffsetMeshInfo + i * 0x50, NOESEEK_ABS)
			if debug:
				print("Mesh Info Start: " + str(bs.tell()))
			meshFile.buildMesh(self, bs.read("20I"), i, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones)
			if debug:
				print("Mesh Info End: " + str(bs.tell()))
				
	def buildSkeleton(self):
		skelFileName = rapi.getDirForFilePath(rapi.getInputName()) + "skeleton.trdemesh"
		if (rapi.checkFileExists(skelFileName)):
			print("Skeleton file detected!")
			print("Building Skeleton....")
			sd = rapi.loadIntoByteArray(skelFileName)
			sd = NoeBitStream(sd)
			sd.seek(0x3630, NOESEEK_ABS)#v2-lara
			#sd.seek(0x35E8, NOESEEK_ABS)#v1-lara
			#sd.seek(0x1B8, NOESEEK_ABS)
			uiNumBones = sd.readUInt()
			sd.seek(0x14, NOESEEK_REL)#v2-lara
			#sd.seek(0x14, NOESEEK_REL)
			#sd.seek(0xC, NOESEEK_REL)
		
			if uiNumBones > 0:
				for i in range(uiNumBones):
					#print("Bone: " + str(i) + " at: " + str(sd.getOffset()))
					sd.seek(0x10, NOESEEK_REL)
					sd.seek(0x10, NOESEEK_REL)

					fBoneXPos = sd.readFloat()
					fBoneYPos = sd.readFloat()
					fBoneZPos = sd.readFloat()
					boneUnk00 = sd.readFloat()
					
					boneUnk01 = sd.readInt()
					boneUnk03 = sd.readShort()
					boneUnk04 = sd.readShort()
					iBonePID = sd.readInt()
					sd.seek(0x14, NOESEEK_REL)
					
					quat = NoeQuat([0, 0, 0, 1])
					mat = quat.toMat43()
					mat[3] = [fBoneXPos, fBoneZPos, -fBoneYPos]
					#print("X: " + str(fBoneXPos) + " Y: " + str(fBoneZPos) + " Z: " + str(fBoneYPos))
					if iBonePID == -1:
						iBonePID = 0
					self.boneList.append(NoeBone(i, "b_" + str(iBonePID) + "_" + str(i), mat, None, iBonePID))
				self.boneList = rapi.multiplyBones(self.boneList)
			
	def buildMesh(self, meshInfo, meshIndex, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones):
		bs = self.inFile
		
		bs.seek(self.offsetStart + self.offsetMeshStart + meshInfo[12] + 0x8, NOESEEK_ABS)
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

		for i in range(usNumVertexComponents):
			uiEntryHash = bs.readUInt()
			usEntryValue = bs.readUShort()
			ucEntryType = bs.readUByte()
			ucEntryNull = bs.readUByte()
			
			if uiEntryHash == 0xD2F7D823:#Position
				iMeshVertPos = usEntryValue
			elif uiEntryHash == 0x36F5E414:#Normal
				if iMeshNrmPos == -1:
					iMeshNrmPos = usEntryValue
			elif uiEntryHash == 0x3E7F6149:#TessellationNormal
				if debug:
					print("Unsupported Vertex Component: TessellationNormal! " + "Pos: " + str(usEntryValue))
			#	iMeshTessNrmPos = usEntryValue
			elif uiEntryHash == 0xF1ED11C3:#Tangent
				if iMeshTangPos == -1:
					iMeshTangPos = usEntryValue
			elif uiEntryHash == 0x64A86F01:#Binormal
				if debug:
					print("Unsupported Vertex Component: BiNormal! " + "Pos: " + str(usEntryValue))
				if iMeshBiNrmPos == -1:
					iMeshBiNrmPos = usEntryValue
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
				if iMeshUV1Pos == -1:
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
				
		if meshInfo[2] != 0 and bSkinningEnabled != 0:
			bs.seek(self.offsetStart + self.offsetMeshStart + meshInfo[3], NOESEEK_ABS)
			boneMap = []
			for i in range(meshInfo[2]):
				boneMap.append(bs.readInt())
			rapi.rpgSetBoneMap(boneMap)
		
		for i in range(meshInfo[0]):
			bs.seek(self.offsetStart + self.offsetMeshStart + uiOffsetMeshGroupInfo + self.meshGroupIdx * 0x70, NOESEEK_ABS)
			self.meshGroupIdx += 1
			
			meshGroupInfo = bs.read("28I")
			print("Mesh_" + "_" + str(self.meshGroupIdx))
			print(meshGroupInfo)
			#rapi.rpgSetName(str(meshGroupInfo[14]))
			#rapi.rpgSetName("Mesh_" + str(self.meshGroupIdx))
			rapi.rpgSetName("Mesh_" + str(self.meshGroupIdx-1) + "_" + str(i) + "_Mat_" + str(meshGroupInfo[14]))
			
			rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))
			
			if bMaterialsEnabled != 0:
				#Create material
				material = NoeMaterial("MAT_" + str(meshIndex) + "_" + str(i), "")
				material.setTexture("Mesh_" + str(meshIndex) + "_" + str(i) + ".dds")
				self.matList.append(material)
				rapi.rpgSetMaterial("MAT_" + str(meshIndex) + "_" + str(i))
			
			bs.seek(self.offsetStart + self.offsetMeshStart + uiOffsetFaceData + meshGroupInfo[4] * 0x2, NOESEEK_ABS)
			faceBuff = bs.readBytes(meshGroupInfo[5] * 0x6)
			
			bs.seek(self.offsetStart + self.offsetMeshStart + meshInfo[4], NOESEEK_ABS)
			vertBuff = bs.readBytes(meshInfo[14] * ucMeshVertStride)
			
			rapi.rpgSetUVScaleBias(NoeVec3 ((16.0, 16.0, 16.0)), NoeVec3 ((16.0, 16.0, 16.0)))
			rapi.rpgSetTransform(NoeMat43((NoeVec3((1, 0, 0)), NoeVec3((0, 0, 1)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, 0)))))
			
			if iMeshVertPos != -1:
				rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, ucMeshVertStride, iMeshVertPos)
			if iMeshNrmPos != -1 and bNORMsEnabled != 0: #Orbis normals are encoded the same as TR8,TRAS Xenon normals, just little endian.
				decodedNormals = rapi.decodeNormals32(vertBuff[iMeshNrmPos:], ucMeshVertStride, -10, -10, -10, NOE_LITTLEENDIAN)
				rapi.rpgBindNormalBufferOfs(decodedNormals, noesis.RPGEODATA_FLOAT, 0xC, 0x0)
				
				#normList = []
				#for n in range(meshInfo[14]):
				#	idx = n * 3
				#	tx = decodedNormals[idx]
				#	ty = decodedNormals[idx + 1]
				#	tz = decodedNormals[idx + 2]
				#	#normList.append(tx/255.0))
				#	#normList.append(ty/.0))
				#	#normList.append(tz))
				#	#normList.append(1.0)
				#print(str(decodedNormals[0]))
				#print(str(decodedNormals[1]))
				#print(str(decodedNormals[2]))
				#print(str(normList[0]))
				#print(str(normList[1]))
				#print(str(normList[2]))
				#normBuff = struct.pack("<" + 'f'*len(normList), *normList)
					
				#rapi.rpgBindColorBufferOfs(normBuff, noesis.RPGEODATA_BYTE, 4, 0x0, 4)
			#if iMeshTessNrmPos != -1:
			#	print("Unsupported")
			if iMeshTangPos != -1:
				decodedTangents = rapi.decodeNormals32(vertBuff[iMeshNrmPos:], ucMeshVertStride, -10, -10, -10, NOE_LITTLEENDIAN)
				#rapi.rpgBindNormalBufferOfs(decodedTangents, noesis.RPGEODATA_FLOAT, 0xC, 0x0)
				#rapi.rpgBindColorBufferOfs(decodedNormals, noesis.RPGEODATA_FLOAT, 0xC, 0x0, 3)
				
			#if iMeshBiNrmPos != -1:
			#	print("Unsupported")
			#if iMeshPckNTBPos != -1:
			#	print("Unsupported")
			if iMeshBwPos != -1 and bSkinningEnabled != 0:
				#weightList = []
				#for w in range(meshInfo[14]):
				#	idx = ucMeshVertStride * w + iMeshBwPos
				#	weightList.append(float((vertBuff[idx]) / 255.0))
				#	weightList.append(float((vertBuff[idx + 1]) / 255.0))
				#	weightList.append(float((vertBuff[idx + 2]) / 255.0))
				#	weightList.append(float((vertBuff[idx + 3]) / 255.0))
				#weightBuff = struct.pack("<" + 'f'*len(weightList), *weightList)
				#rapi.rpgBindBoneWeightBufferOfs(weightBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0, 0x4)
				rapi.rpgBindBoneWeightBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, ucMeshVertStride, iMeshBwPos, 0x4)
			if iMeshBiPos != -1 and bSkinningEnabled != 0:
				rapi.rpgBindBoneIndexBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, ucMeshVertStride, iMeshBiPos, 0x4)	
			#if iMeshCol1Pos != -1 and bCOLsEnabled != 0:
			#	rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, ucMeshVertStride, iMeshCol1Pos, 0x4)	
			#if iMeshCol2Pos != -1:
			#	print("Unsupported")
			
			if iMeshUV1Pos != -1 and bUVsEnabled != 0:
				#uvList = []
				#for w in range(meshInfo[14]):
				#	idx = ucMeshVertStride * w + iMeshUV1Pos
				#	uvList.append((struct.unpack('<h',vertBuff[idx:(idx+2)])[0]/2048.0))
				#	uvList.append(((struct.unpack('<h',vertBuff[(idx+2):(idx+4)])[0]/2048.0)))
				#	uvList.append(0.0)
				#print(uvList)
				#uvBuff = struct.pack("<" + 'f'*len(uvList), *uvList)
				#rapi.rpgBindUV1BufferOfs(uvBuff, noesis.RPGEODATA_FLOAT, 12, 0)
				rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_SHORT, ucMeshVertStride, iMeshUV1Pos)
			#if iMeshUV2Pos != -1 and bUVsEnabled != 0:
			#	rapi.rpgBindUV2BufferOfs(vertBuff, noesis.RPGEODATA_SHORT, ucMeshVertStride, iMeshUV2Pos)
			#if iMeshUV3Pos != -1:
			#	print("Unsupported")
			#if iMeshUV4Pos != -1:
			#	print("Unsupported")
			#if iMeshIIDPos != -1:
			#	print("Unsupported")
			if bRenderAsPoints:
				rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_POINTS, 0x1)
			else:
				rapi.rpgSetStripEnder(0x10000)
				rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, int(meshGroupInfo[5] * 0x3), noesis.RPGEO_TRIANGLE, 0x1)
			if bOptimizeMesh:
				rapi.rpgOptimize()
			rapi.rpgClearBufferBinds()
			
def meshLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	mesh = meshFile(data)
	#mesh.loadHeader()
	mesh.loadMeshFile()
	mesh.buildSkeleton()
	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()
	mdl.setBones(mesh.boneList)
	mdl.setModelMaterials(NoeModelMaterials(mesh.texList, mesh.matList))
	mdlList.append(mdl);
	return 1
	