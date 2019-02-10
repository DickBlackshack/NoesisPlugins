#Tomb Raider: 2013 [PC] - ".trasmesh" Loader
#By Gh0stblade
#v1.3
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
	handle = noesis.register("Tomb Raider 2013 [PC]", ".trasmesh")
	noesis.setHandlerTypeCheck(handle, meshCheckType)
	noesis.setHandlerLoadModel(handle, meshLoadModel)
	noesis.logPopup()
	return 1

def meshCheckType(data):
	bs = NoeBitStream(data)
	
	numOffsets = bs.readInt()
	bs.seek(0x10, NOESEEK_ABS)
	numOffsets2 = bs.readInt()
	bs.seek(0x18, NOESEEK_ABS)
	offsetMeshStart = bs.readInt()
	bs.seek(0x28, NOESEEK_ABS)
	offsetMatInfo = bs.readInt()
	bs.seek(((numOffsets * 0x8) + 0x4), NOESEEK_ABS)
	offsetBoneInfo = bs.readInt()
	offsetBoneInfo2 = bs.readInt()
	bs.seek(((0x14 + numOffsets * 0x8) + numOffsets2 * 0x4), NOESEEK_ABS)
	offsetStart = bs.getOffset()
	bs.seek(offsetStart + offsetMeshStart, NOESEEK_ABS)
	
	uiMagic = bs.readUInt()
	if uiMagic == 0x6873654D:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(uiMagic) + " expected 'hsem'!"))
		return 0
	
class meshFile(object):

	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.boneList = []
		self.offsetBoneInfo = -1
		self.offsetBoneInfo2 = -1
		self.offsetMeshStart = -1
		self.offsetMatInfo = -1
		self.offsetStart = -1
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
		uiOffsetMeshGroupInfo = bs.readUInt()
		uiOffsetMeshInfo = bs.readUInt()
		uiOffsetBoneMap = bs.readUInt()
		
		uiOffsetBoneMap = bs.readUInt()
		uiOffsetFaceData = bs.readUInt()
		usNumMeshGroups = bs.readUShort()
		usNumMesh = bs.readUShort()
		usNumBones = bs.readUShort()
		
		for i in range(usNumMesh):
			bs.seek(self.offsetStart + self.offsetMeshStart + uiOffsetMeshInfo + i * 0x30, NOESEEK_ABS)
			if debug:
				print("Mesh Info Start: " + str(bs.tell()))
			meshFile.buildMesh(self, bs.read("1i2h10i"), i, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones)
			if debug:
				print("Mesh Info End: " + str(bs.tell()))
				
	def buildSkeleton(self):
		bs = self.inFile
		bs.seek(self.offsetStart + self.offsetBoneInfo - 0x4, NOESEEK_ABS)
		
		uiNumBones = bs.readInt()
		bs.seek(0xC, NOESEEK_REL)
		
		bs.seek(self.offsetStart + self.offsetBoneInfo2, NOESEEK_ABS)
		
		if uiNumBones > 0:
			for i in range(uiNumBones):
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
		
		bs.seek(self.offsetStart + self.offsetMeshStart + meshInfo[8] + 0x8, NOESEEK_ABS)
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
				iMeshNrmPos = usEntryValue
			elif uiEntryHash == 0x3E7F6149:#TessellationNormal
				if debug:
					print("Unsupported Vertex Component: TessellationNormal! " + "Pos: " + str(usEntryValue))
			#	iMeshTessNrmPos = usEntryValue
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
				
		if meshInfo[2] != 0 and bSkinningEnabled != 0:
			bs.seek(self.offsetStart + self.offsetMeshStart + meshInfo[3], NOESEEK_ABS)
			boneMap = []
			for i in range(meshInfo[2]):
				boneMap.append(bs.readInt())
			rapi.rpgSetBoneMap(boneMap)
		
		for i in range(meshInfo[0]):
			bs.seek(self.offsetStart + self.offsetMeshStart + uiOffsetMeshGroupInfo + self.meshGroupIdx * 0x50, NOESEEK_ABS)
			self.meshGroupIdx += 1
			meshGroupInfo = bs.read("iiiiiiiiiiiiiiiiiiii")
			
			rapi.rpgSetName("Mesh_" + str(meshIndex) + "_" + str(i))
			rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))
			
			bs.seek(self.offsetStart + self.offsetMeshStart + uiOffsetFaceData + meshGroupInfo[4] * 0x2, NOESEEK_ABS)
			faceBuff = bs.readBytes(meshGroupInfo[5] * 0x6)
			
			bs.seek(self.offsetStart + self.offsetMeshStart + meshInfo[4], NOESEEK_ABS)
			vertBuff = bs.readBytes(meshInfo[9] * ucMeshVertStride)
			
			rapi.rpgSetUVScaleBias(NoeVec3 ((16.0, 16.0, 16.0)), NoeVec3 ((16.0, 16.0, 16.0)))
			rapi.rpgSetTransform(NoeMat43((NoeVec3((1, 0, 0)), NoeVec3((0, 0, 1)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, 0)))))
			
			if iMeshVertPos != -1:
				rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, ucMeshVertStride, iMeshVertPos)
			if iMeshNrmPos != -1 and bNORMsEnabled != 0: #PC, convert normals. Thanks to Dunsan from UnpackTRU just a custom version
				normList = []
				for n in range(meshInfo[9]):
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
			#if iMeshTessNrmPos != -1:
			#	print("Unsupported")
			if iMeshTangPos != -1:
				rapi.rpgBindTangentBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, ucMeshVertStride, iMeshTangPos, 0x4)
			#if iMeshBiNrmPos != -1:
			#	print("Unsupported")
			#if iMeshPckNTBPos != -1:
			#	print("Unsupported")
			if iMeshBwPos != -1 and bSkinningEnabled != 0:
				weightList = []
				for w in range(meshInfo[9]):
					idx = ucMeshVertStride * w + iMeshBwPos
					weightList.append(float((vertBuff[idx]) / 255.0))
					weightList.append(float((vertBuff[idx + 1]) / 255.0))
					weightList.append(float((vertBuff[idx + 2]) / 255.0))
					weightList.append(float((vertBuff[idx + 3]) / 255.0))
				weightBuff = struct.pack("<" + 'f'*len(weightList), *weightList)
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
				rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, meshInfo[16], noesis.RPGEO_POINTS, 0x1)
			else:
				rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, int(meshGroupInfo[5] * 0x3), noesis.RPGEO_TRIANGLE, 0x1)
			if bOptimizeMesh:
				rapi.rpgOptimize()
			rapi.rpgClearBufferBinds()
			
def meshLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	mesh = meshFile(data)
	mesh.loadHeader()
	mesh.loadMeshFile()
	mesh.buildSkeleton()
	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()
	mdl.setBones(mesh.boneList)
	mdlList.append(mdl);
	return 1
	