#Shadow of the Tomb Raider [PC] - ".tr11mesh" Loader
#By Gh0stblade
#v1.2
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
bTANGsEnabled = 0				#Tangents (1 = on, 0 = off)
bUVsEnabled = 1					#UVs (1 = on, 0 = off)
bCOLsEnabled = 0				#Vertex colours (1 = on, 0 = off)
bSkinningEnabled = 1			#Enable skin weights (1 = on, 0 = off)
bDebugNormals = 0				#Debug normals as RGBA
bDebugTangents = 0				#Debug tangents as RGBA
#Gh0stBlade ONLY
debug = 0 						#Prints debug info (1 = on, 0 = off)

from inc_noesis import *
import math

def registerNoesisTypes():
	handle = noesis.register("Shadow of the Tomb Raider 3D Mesh [PC]", ".tr11mesh")
	noesis.setHandlerTypeCheck(handle, meshCheckType)
	noesis.setHandlerLoadModel(handle, meshLoadModel)
	
	handle = noesis.register("Shadow of the Tomb Raider 2D Texture [PC]", ".tr11pcd")
	noesis.setHandlerTypeCheck(handle, pcdCheckType)
	noesis.setHandlerLoadRGBA(handle, pcdLoadDDS)
	
	noesis.logPopup()
	return 1

def meshCheckType(data):
	bs = NoeBitStream(data)
	uiMagic = bs.readUInt()
	
	if uiMagic == 0x6873654D:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(uiMagic) + " expected 'mesh'!"))
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
	elif uiPcdType == 0x4D:#CORRECT
		gPcdFmt = noesis.NOESISTEX_DXT5
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
	elif uiPcdType == 0x5F:#CORRECT
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, noesis.FOURCC_BC6H)
	elif uiPcdType == 0x62:#CORRECT
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, noesis.FOURCC_BC7)
	elif uiPcdType == 0x63:#CORRECT
		gPcdFmt = noesis.NOESISTEX_RGBA32
		bPcdData = rapi.imageDecodeDXT(bPcdData, uiPcdWidth, uiPcdHeight, noesis.FOURCC_BC7)
	else:
		print("Fatal Error: Unsupported texture type: " + str(uiPcdType))
		
	if gPcdFmt != None:
		texList.append(NoeTexture("Texture", int(uiPcdWidth), int(uiPcdHeight), bPcdData, gPcdFmt))
	return 1
	
class meshFile(object): 
	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.meshGroupIdx = 0
		self.boneList = []
		self.matList = []
		self.texList = []
		self.matNames = []
		self.offsetMeshStart = 0
		self.lastModelIndex = 0
		
	def loadMeshFile(self):
		bs = self.inFile
		
		#bs.seek(self.offsetMeshStart, NOESEEK_ABS)
		
		uiMagic = bs.readUInt()
		uiUnk00 = bs.readUInt()
		uiMeshFileSize = bs.readUInt()
		uiUnk01 = bs.readUInt()
		
		bs.seek(0xE8, NOESEEK_REL)#AABB MIN/MAX?
		
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
			bs.seek(self.offsetMeshStart + uiOffsetMeshInfo + i * 0x60, NOESEEK_ABS)
			if debug:
				print("Mesh Info Start: " + str(bs.tell()))
			meshFile.buildMesh(self, [bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt()], i, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones)
			if debug:
				print("Mesh Info End: " + str(bs.tell()))
	
	def buildSkeleton(self):
		skelFileName = rapi.getDirForFilePath(rapi.getInputName()) + "skeleton.skl"
		if (rapi.checkFileExists(skelFileName)):
			print("Skeleton file detected!")
			print("Building Skeleton....")
			
			sd = rapi.loadIntoByteArray(skelFileName)
			
			sd = NoeBitStream(sd)

			numData = sd.readUInt()
			sd.seek(0x18 + numData * 8, NOESEEK_REL)
			uiNumBones = sd.readUShort()
			sd.seek(0x8E, NOESEEK_REL)
		
			if uiNumBones > 0:
				for i in range(uiNumBones):
					sd.seek(0x8, NOESEEK_REL)
					fBoneXPos = sd.readFloat()
					fBoneYPos = sd.readFloat()
					fBoneZPos = sd.readFloat()
					boneUnk00 = sd.readInt()
					
					sd.seek(0x18, NOESEEK_REL)
					
					iBonePID = sd.readInt()
					sd.seek(0xC, NOESEEK_REL)
					
					quat = NoeQuat([0, 0, 0, 1])
					mat = quat.toMat43()
					mat[3] = [fBoneXPos, fBoneZPos, -fBoneYPos]
					self.boneList.append(NoeBone(i, "bone%03i"%i, mat, None, iBonePID))
				self.boneList = rapi.multiplyBones(self.boneList)
			
	def buildMesh(self, meshInfo, meshIndex, uiOffsetMeshGroupInfo, uiOffsetBoneMap, uiOffsetFaceData, usNumBones):
		bs = self.inFile
		
		bs.seek(self.offsetMeshStart + meshInfo[14] + 0x8, NOESEEK_ABS)
		usNumVertexComponents = bs.readUShort()
		
		vertexStrideInfo = bs.read("2B")
		bs.seek(0x4, NOESEEK_REL)
			
		vertexBuffers = []
		
		iMeshVertIndex = -1
		iMeshNrmIndex = -1
		iMeshTessNrmIndex = -1
		iMeshTangIndex = -1
		iMeshBiNrmIndex = -1
		iMeshPckNTBIndex = -1
		iMeshBwIndex = -1
		iMeshBiIndex = -1
		iMeshCol1Index = -1
		iMeshCol2Index = -1
		iMeshUV1Index = -1
		iMeshUV2Index = -1
		iMeshUV3Index = -1
		iMeshUV4Index = -1
		iMeshIIDIndex = -1
		
		entryData = []
		
		for i in range(usNumVertexComponents):
			#Hash, Pos, Flags, Index
			entryData.append(bs.read("1I1H2B"))
			
			if entryData[i][0] == 0xD2F7D823:#Position
				iMeshVertIndex = i
			elif entryData[i][0] == 0x36F5E414:#Normal
				iMeshNrmIndex = i
			elif entryData[i][0] == 0x3E7F6149:#TessellationNormal
				iMeshTessNrmIndex = i
				if debug:
					print("Unsupported Vertex Component: TessellationNormal! " + "Pos: " + str(entryData[i][1]))
			elif entryData[i][0] == 0xF1ED11C3:#Tangent
				iMeshTangIndex = i
				if debug:
					print("Unsupported Vertex Component: Tangent! " + "Pos: " + str(entryData[i][1]))
			elif entryData[i][0] == 0x64A86F01:#Binormal
				iMeshBiNrmIndex = i
				if debug:
					print("Unsupported Vertex Component: BiNormal! " + "Pos: " + str(entryData[i][1]))
			elif entryData[i][0] == 0x9B1D4EA:#PackedNTB
				iMeshPckNTBIndex = i
				if debug:
					print("Unsupported Vertex Component: PackedNTB! " + "Pos: " + str(entryData[i][1]))
			elif entryData[i][0] == 0x48E691C0:#SkinWeights
				iMeshBwIndex = i
			elif entryData[i][0] == 0x5156D8D3:#SkinIndices
				iMeshBiIndex = i
			elif entryData[i][0] == 0x7E7DD623:#Color1
				iMeshCol1Index = i
			elif entryData[i][0] == 0x733EF0FA:#Color2
				iMeshCol2Index = i
				if debug:
					print("Unsupported Vertex Component: Color2! " + "Pos: " + str(entryData[i][1]))
			elif entryData[i][0] == 0x8317902A:#Texcoord1
				iMeshUV1Index = i
			elif entryData[i][0] == 0x8E54B6F3:#Texcoord2
				iMeshUV2Index = i
			elif entryData[i][0] == 0x8A95AB44:#Texcoord3
				iMeshUV3Index = i
				if debug:
					print("Unsupported Vertex Component: Texcoord3! " + "Pos: " + str(entryData[i][1]))
			elif entryData[i][0] == 0x94D2FB41:#Texcoord4
				iMeshUV4Index = i
				if debug:
					print("Unsupported Vertex Component: Texcoord4! " + "Pos: " + str(entryData[i][1]))
			elif entryData[i][0] == 0xE7623ECF:#InstanceID
				if debug:
					print("Unsupported Vertex Component: InstanceID! " + "Pos: " + str(entryData[i][1]))
				iMeshIIDIndex = i
			else:
				if debug:
					print("Unknown Vertex Component! Hash: " + str(hex((entryData[i][0]))) + " value: " + str(entryData[i][2]))
			
		if meshInfo[1] != 0 and bSkinningEnabled != 0:
			bs.seek(self.offsetMeshStart + meshInfo[2], NOESEEK_ABS)
			boneMap = []
			for i in range(meshInfo[1]):
				boneMap.append(bs.readInt())
			rapi.rpgSetBoneMap(boneMap)
			
		#VertexBuffer1
		if meshInfo[4] != 0:
			bs.seek(self.offsetMeshStart + meshInfo[4], NOESEEK_ABS)
			vertexBuffers.append(bs.readBytes(meshInfo[18] * (vertexStrideInfo[0])))
		#VertexBuffer2
		if meshInfo[8] != 0:
			bs.seek(self.offsetMeshStart + meshInfo[8], NOESEEK_ABS)
			vertexBuffers.append(bs.readBytes(meshInfo[18] * (vertexStrideInfo[1])))
		
		for i in range(meshInfo[0]):
			bs.seek(self.offsetMeshStart + uiOffsetMeshGroupInfo + self.meshGroupIdx * 0x60, NOESEEK_ABS)
			self.meshGroupIdx += 1
			meshGroupInfo = [bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt(),bs.readInt()]
			
			if debug:
				print("Mesh_" + str(self.meshGroupIdx))
				print(meshGroupInfo)
			
			rapi.rpgSetName("Mesh_" + str(self.meshGroupIdx))
			
			matName = str(self.meshGroupIdx-1) + ".matd"
			material = NoeMaterial(matName, "")
			material.setFlags(noesis.NMATFLAG_TWOSIDED, 0)
			material.setTexture(str(self.meshGroupIdx-1) + ".tga")
				
			self.matList.append(material)
			self.matNames.append(matName)
			rapi.rpgSetMaterial(self.matNames[self.meshGroupIdx-1])
			
			rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))
			
			bs.seek(self.offsetMeshStart + uiOffsetFaceData + meshGroupInfo[4] * 0x2, NOESEEK_ABS)
			faceBuff = bs.readBytes(meshGroupInfo[5] * 0x6)
			
			rapi.rpgSetUVScaleBias(NoeVec3 ((16.0, 16.0, 16.0)), NoeVec3 ((16.0, 16.0, 16.0)))
			rapi.rpgSetTransform(NoeMat43((NoeVec3((1, 0, 0)), NoeVec3((0, 0, 1)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, 0)))))
		
			if iMeshVertIndex != -1:
				rapi.rpgBindPositionBufferOfs(vertexBuffers[entryData[iMeshVertIndex][3]], noesis.RPGEODATA_FLOAT, vertexStrideInfo[entryData[iMeshVertIndex][3]], entryData[iMeshVertIndex][1])
			if iMeshNrmIndex != -1 and bNORMsEnabled != 0:
				normList = []
				for n in range(meshInfo[18]):
					idx = vertexStrideInfo[entryData[iMeshNrmIndex][3]] * n + entryData[iMeshNrmIndex][1]
					nz = float((vertexBuffers[entryData[iMeshNrmIndex][3]][idx]) / 255.0 * 2 - 1)
					ny = float((vertexBuffers[entryData[iMeshNrmIndex][3]][idx + 1]) / 255.0 * 2 - 1)
					nx = float((vertexBuffers[entryData[iMeshNrmIndex][3]][idx + 2]) / 255.0 * 2 - 1)
					l = math.sqrt(nx * nx + ny * ny + nz * nz)
					normList.append(nx / l)
					normList.append(ny / l)
					normList.append(nz / l)
					if bDebugNormals:
						normList.append(255.0)
				normBuff = struct.pack("<" + 'f'*len(normList), *normList)
				if bDebugNormals:
					rapi.rpgBindColorBufferOfs(normBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0, 0x4)
				else:
					rapi.rpgBindNormalBufferOfs(normBuff, noesis.RPGEODATA_FLOAT, 0xC, 0x0)
			if iMeshTangIndex != -1 and bTANGsEnabled != 0:
				tangList = []
				for n in range(meshInfo[18]):
					idx = vertexStrideInfo[entryData[iMeshTangIndex][3]] * n + entryData[iMeshTangIndex][1]
					tz = float((vertexBuffers[entryData[iMeshTangIndex][3]][idx]) / 255.0 * 2 - 1)
					ty = float((vertexBuffers[entryData[iMeshTangIndex][3]][idx + 1]) / 255.0 * 2 - 1)
					tx = float((vertexBuffers[entryData[iMeshTangIndex][3]][idx + 2]) / 255.0 * 2 - 1)
					tw = float((vertexBuffers[entryData[iMeshTangIndex][3]][idx + 3]) / 255.0 * 2 - 1)
					l = math.sqrt(tx * tx + ty * ty + tz * tz)
					tangList.append(tx / l)
					tangList.append(ty / l)
					tangList.append(tz / l)
					tangList.append(tw / l)
				tangBuff = struct.pack("<" + 'f'*len(tangList), *tangList)
				if bDebugTangents:
					rapi.rpgBindColorBufferOfs(tangBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0, 0x4)
				else:
					rapi.rpgBindTangentBuffer(tangBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0)
			#if iMeshTessNrmPos != -1:
			#	print("Unsupported")
			#if iMeshBiNrmIndex != -1 and bNORMsEnabled != 0:
			#	normList = []
			#	for n in range(meshInfo[18]):
			#		idx = vertexStrideInfo[entryData[iMeshBiNrmIndex][3]] * n + entryData[iMeshBiNrmIndex][1]
			#		nz = float((vertexBuffers[entryData[iMeshBiNrmIndex][3]][idx]) / 255.0 * 2 - 1)
			#		ny = float((vertexBuffers[entryData[iMeshBiNrmIndex][3]][idx + 1]) / 255.0 * 2 - 1)
			#		nx = float((vertexBuffers[entryData[iMeshBiNrmIndex][3]][idx + 2]) / 255.0 * 2 - 1)
			#		l = math.sqrt(nx * nx + ny * ny + nz * nz)
			#		normList.append(nx / l)
			#		normList.append(ny / l)
			#		normList.append(nz / l)
			#		if bDebugNormals:
			#			normList.append(255.0)
			#	normBuff = struct.pack("<" + 'f'*len(normList), *normList)
			#	if bDebugNormals:
			#		rapi.rpgBindColorBufferOfs(normBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0, 0x4)
			#	else:
			#		rapi.rpgBindNormalBufferOfs(normBuff, noesis.RPGEODATA_FLOAT, 0xC, 0x0)
			#if iMeshPckNTBPos != -1:
			#	print("Unsupported")
			if iMeshBwIndex != -1 and bSkinningEnabled != 0:
				weightList = []
				for w in range(meshInfo[18]):
					idx = vertexStrideInfo[entryData[iMeshBwIndex][3]] * w + entryData[iMeshBwIndex][1]
					weightList.append(float((vertexBuffers[entryData[iMeshBwIndex][3]][idx]) / 255.0))
					weightList.append(float((vertexBuffers[entryData[iMeshBwIndex][3]][idx + 1]) / 255.0))
					weightList.append(float((vertexBuffers[entryData[iMeshBwIndex][3]][idx + 2]) / 255.0))
					weightList.append(float((vertexBuffers[entryData[iMeshBwIndex][3]][idx + 3]) / 255.0))
				weightBuff = struct.pack("<" + 'f'*len(weightList), *weightList)
				rapi.rpgBindBoneWeightBufferOfs(weightBuff, noesis.RPGEODATA_FLOAT, 0x10, 0x0, 0x4)
			if iMeshBiIndex != -1 and bSkinningEnabled != 0:
				rapi.rpgBindBoneIndexBufferOfs(vertexBuffers[entryData[iMeshBiIndex][3]], noesis.RPGEODATA_BYTE, vertexStrideInfo[entryData[iMeshBiIndex][3]], entryData[iMeshBiIndex][1], 0x4)	
			if iMeshCol1Index != -1 and bCOLsEnabled != 0 and bDebugNormals == 0:
				rapi.rpgBindColorBufferOfs(vertexBuffers[entryData[iMeshCol1Index][3]], noesis.RPGEODATA_BYTE, vertexStrideInfo[entryData[iMeshCol1Index][3]], entryData[iMeshCol1Index][1], 0x4)
			#if iMeshCol2Pos != -1:
			#	print("Unsupported")
			if iMeshUV1Index != -1 and bUVsEnabled != 0:
				rapi.rpgBindUV1BufferOfs(vertexBuffers[entryData[iMeshUV1Index][3]], noesis.RPGEODATA_SHORT, vertexStrideInfo[entryData[iMeshUV1Index][3]], entryData[iMeshUV1Index][1])
			if iMeshUV2Index != -1 and bUVsEnabled != 0:
				rapi.rpgBindUV2BufferOfs(vertexBuffers[entryData[iMeshUV2Index][3]], noesis.RPGEODATA_SHORT, vertexStrideInfo[entryData[iMeshUV2Index][3]], entryData[iMeshUV2Index][1])
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