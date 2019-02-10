#Resident Evil 2 Remake [PC] - ".mesh" Loader
#By Gh0stblade
#v1.5
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
bTANGsEnabled = 1				#Tangents (1 = on, 0 = off)
bUVsEnabled = 1					#UVs (1 = on, 0 = off))
bSkinningEnabled = 1			#Enable skin weights (1 = on, 0 = off)
bDebugNormals = 0				#Debug normals as RGBA
bDebugTangents = 0				#Debug tangents as RGBA
#Gh0stBlade ONLY
bDebug = 0 						#Prints debug info (1 = on, 0 = off)

from inc_noesis import *
import math
import os

def registerNoesisTypes():
	handle = noesis.register("Resident Evil 2 Remake [PC]", ".1808312334")
	noesis.setHandlerTypeCheck(handle, meshCheckType)
	noesis.setHandlerLoadModel(handle, meshLoadModel)
	
	handle = noesis.register("Resident Evil 2 Remake Texture [PC]", ".10")
	noesis.setHandlerTypeCheck(handle, texCheckType)
	noesis.setHandlerLoadRGBA(handle, texLoadDDS)
	
	noesis.logPopup()
	return 1

def meshCheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	if magic == 0x4853454D:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected 'MESH'!"))
		return 0

def texCheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	if magic == 0x00584554:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected TEX!"))
		return 0
		
def texLoadDDS(data, texList):
	bs = NoeBitStream(data)
	
	magic = bs.readUInt()
	version = bs.readUInt()
	width = bs.readUShort()
	height = bs.readUShort()
	unk00 = bs.readUShort()
	mipCount = bs.readUByte()
	unk01 = bs.readUByte()
	
	format = bs.readUInt()
	unk02 = bs.readUInt()
	unk03 = bs.readUInt()
	unk04 = bs.readUInt()
	
	mipData = []
	for i in range(mipCount):
		mipData.append([bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt()])
	
	bs.seek(mipData[0][0], NOESEEK_ABS)
	texData = bs.readBytes(mipData[0][3])
		
	texFormat = None
	if bDebug:
		print(format)
	#if format == 0x2: #Actually float rgba
	#	count = int(len(texData)/4)
	#	intTexData = list(struct.unpack('I'*count, texData))
	#	for i in range(len(intTexData)):
	#		intTexData[i] += 1
	#			
	#	texData = struct.pack("<%uI" % len(intTexData), *intTexData)
	#	print(texData)
	#	texFormat = noesis.NOESISTEX_RGBA32
	#	texData = rapi.imageDecodeRaw(texData, width, height, "r32g32b32a32", 0)
	if format == 0x1C:
		texFormat = noesis.NOESISTEX_RGBA32
		texData = rapi.imageDecodeDXT(texData, width, height, noesis.FOURCC_ATI1)
	elif format == 0x1D:
		texFormat = noesis.NOESISTEX_RGBA32
		texData = rapi.imageDecodeDXT(texData, width, height, noesis.FOURCC_BC1)
	elif format == 0x47:#FIXME
		texFormat = noesis.NOESISTEX_RGBA32
		texData = rapi.imageDecodeDXT(texData, width, height, noesis.FOURCC_DXT1)
	elif format == 0x48:
		texFormat = noesis.NOESISTEX_RGBA32
		texData = rapi.imageDecodeDXT(texData, width, height, noesis.FOURCC_DXT1)
	elif format == 0x50:
		texFormat = noesis.NOESISTEX_RGBA32
		texData = rapi.imageDecodeDXT(texData, width, height, noesis.FOURCC_BC4)
	elif format == 0x5F:
		texFormat = noesis.NOESISTEX_RGBA32
		texData = rapi.imageDecodeDXT(texData, width, height, noesis.FOURCC_BC6H)
	elif format == 0x62:
		texFormat = noesis.NOESISTEX_RGBA32
		texData = rapi.imageDecodeDXT(texData, width, height, noesis.FOURCC_BC7)
	elif format == 0x63:
		texFormat = noesis.NOESISTEX_RGBA32
		texData = rapi.imageDecodeDXT(texData, width, height, noesis.FOURCC_BC7)
	else:
		print("Fatal Error: Unsupported texture type: " + str(format))
		return 0
		
	if texFormat != None:
		texList.append(NoeTexture(rapi.getInputName(), int(width), int(height), texData, texFormat))
	return 1
	
def ReadUnicodeString(bs):
	numZeroes = 0
	resultString = ""
	while(numZeroes < 2):
		c = bs.readUByte()
		if c == 0:
			numZeroes+=1
			continue
		else:
			numZeroes = 0
		resultString += chr(c)
	return resultString
		
def GetRootGameDir():
	path = rapi.getDirForFilePath(rapi.getInputName())
	while len(path) > 3:
		lastFolderName = os.path.basename(os.path.normpath(path))
		if lastFolderName == "x64":
			break
		else:
			path = os.path.normpath(os.path.join(path, ".."))
	return path	+ "\\"
	
class meshFile(object): 
	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.boneList = []
		self.matNames = []
		self.matList = []
		self.texList = []
		
	def createMaterials(self):
		materialFileName = rapi.getExtensionlessName(rapi.getInputName()) + ".mdf2.10"
		if not (rapi.checkFileExists(materialFileName)):
			print("Failed to open material file: " + materialFileName)
			return
			
		texBaseColour = []
		texRoughColour = []
		texSpecColour = []
		texAmbiColour = []
		texMetallicColour = []
		texFresnelColour = []
			
		bs = rapi.loadIntoByteArray(materialFileName)
		bs = NoeBitStream(bs)
		#Magic, Unknown, MaterialCount, Unknown, Unknown
		matHeader = [bs.readUInt(), bs.readUShort(), bs.readUShort(), bs.readUInt(), bs.readUInt()]
		
		#Parse Materials
		materialInfo = []
		for i in range(matHeader[2]):
			#MaterialNames[0], Hash[1], Unknown[2], BaseColourCount[3], TextureCount[4], Unknown[5], Unknown[6], offsetUnk00[7], offsetUnk01[8] offsetBaseColours[9]
			if bDebug:
				print("Start Offset: " + str(bs.getOffset()))
			bs.seek(0x10 + (i * 0x40), NOESEEK_ABS)
			materialInfo.append([bs.readUInt64(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt64(), bs.readUInt64(), bs.readUInt64(), bs.readUInt64()])
			
			if bDebug:
				print("End offset: " + str(bs.getOffset()))
			
			bs.seek(materialInfo[i][0], NOESEEK_ABS)
			materialName = ReadUnicodeString(bs)
			
			if bDebug:
				print("Material Name: [" + str(i) + "]-" + materialName)
			self.matNames.append(materialName)
			
			materialFlags = 0
			material = NoeMaterial(materialName, "")
			material.setDefaultBlend(0)
			#material.setBlendMode("GL_SRC_ALPHA", "GL_ONE")
			material.setAlphaTest(0)
			
			#Parse Textures
			textureInfo = []
			paramInfo = []
			
			bFoundBM = False
			bFoundNM = False
			bFoundHM = False
			bFoundBT = False
			bFoundSSSM = False
				
			bFoundBaseColour = False
			bFoundRoughColour = False
			bFoundSpecColour = False
			bFoundAmbiColour = False
			bFoundMetallicColour = False
			bFoundFresnelColour = False
			
			if bDebug:
				print(materialInfo[i])
			
			for j in range(materialInfo[i][3]):
				bs.seek(materialInfo[i][7] + (j * 0x18), NOESEEK_ABS)
				#paramType[0], Hash[1], Count[2], Offset[3]
				paramInfo.append([bs.readUInt64(), bs.readUInt64(), bs.readUInt(), bs.readUInt()])
				bs.seek(paramInfo[j][0], NOESEEK_ABS)
				paramType = ReadUnicodeString(bs)
				
				bs.seek(materialInfo[i][9] + paramInfo[j][3], NOESEEK_ABS)
				colours = []
				if paramInfo[j][2] == 4:
					colours.append(NoeVec4((bs.readFloat(), bs.readFloat(), bs.readFloat(), bs.readFloat())))
				elif paramInfo[j][2] == 1:
					colours.append(bs.readFloat())
					
				if bDebug:
					print(paramType + ":")
					print(colours)
				
				if paramType == "BaseColor" and not bFoundBaseColour:
					bFoundBaseColour = True
					texBaseColour.append(colours)
				if paramType == "Roughness" and not bFoundRoughColour:
					bFoundRoughColour = True
					texRoughColour.append(colours)
				if paramType == "PrimalySpecularColor" and not bFoundSpecColour:
					bFoundSpecColour = True
					texSpecColour.append(colours)
				if paramType == "AmbientColor" and not bFoundAmbiColour:
					bFoundAmbiColour = True
					texAmbiColour.append(colours)
				if paramType == "Metallic" and not bFoundMetallicColour:
					bFoundMetallicColour = True
					texMetallicColour.append(colours)
				if paramType == "Fresnel_DiffuseIntensity" and not bFoundFresnelColour:
					bFoundFresnelColour = True
					texFresnelColour.append(colours)
			
			#Append defaults
			if not bFoundBaseColour:
				texBaseColour.append(NoeVec4((1.0, 1.0, 1.0, 1.0)))
			if not bFoundRoughColour:
				texRoughColour.append(1.0)
			if not bFoundSpecColour:
				texSpecColour.append(NoeVec4((1.0, 1.0, 1.0, 0.8)))
			if not bFoundAmbiColour:
				texAmbiColour.append(NoeVec4((1.0, 1.0, 1.0, 1.0)))
			if not bFoundMetallicColour:
				texMetallicColour.append(1.0)
			if not bFoundFresnelColour:
				texFresnelColour.append(0.8)
				
			for j in range(materialInfo[i][4]):
				bs.seek(materialInfo[i][8] + (j * 0x18), NOESEEK_ABS)
				#TextureTypeOffset[0], Hash[1], TextureName[2]
				textureInfo.append([bs.readUInt64(), bs.readUInt64(), bs.readUInt64()])
				bs.seek(textureInfo[j][0], NOESEEK_ABS)
				textureType = ReadUnicodeString(bs)
				bs.seek(textureInfo[j][2], NOESEEK_ABS)
				textureName = ReadUnicodeString(bs)
				
				if bDebug:
					print("Texture Type: " + textureType + " Name: " + textureName)
				
				textureFilePath = self.rootDir + textureName + ".10"
				textureFilePath2 = rapi.getLocalFileName(self.rootDir + textureName).rsplit('.', 1)[0] + ".dds"
				bAlreadyLoadedTexture = False
				
				for k in range(len(self.texList)):
					if self.texList[k].name == textureFilePath2:
						bAlreadyLoadedTexture = True

				if not bAlreadyLoadedTexture:
					if not (rapi.checkFileExists(textureFilePath)):
						print("Fatal Error: Texture at path: " + str(textureFilePath) + " does not exist!")
						self.texList.append(NoeTexture("dummy", 0, 0, 0, 0))
					else:
						textureData = rapi.loadIntoByteArray(textureFilePath)
						if texLoadDDS(textureData, self.texList) == 1:
							self.texList[len(self.texList)-1].name = textureFilePath2
						else:
							self.texList.append(NoeTexture("dummy", 0, 0, 0, 0))
				
				if textureType == "BaseMetalMap" or textureType == "BaseShiftMap" or "Base" in textureType and not bFoundBM:
					bFoundBM = True
					material.setTexture(textureFilePath2)
					material.setDiffuseColor(texBaseColour[i][0])
					material.setSpecularTexture(textureFilePath2)
					materialFlags |= noesis.NMATFLAG_PBR_SPEC #Not really :(
					#
					material.setSpecularSwizzle( NoeMat44([[1, 1, 1, 0], [0, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0]]) )
				elif textureType == "NormalRoughnessMap" and not bFoundNM:
					bFoundNM = True
					material.setNormalTexture(textureFilePath2)
					materialFlags |= noesis.NMATFLAG_PBR_ROUGHNESS_NRMALPHA
				elif textureType == "AlphaTranslucentOcclusionSSSMap" and not bFoundSSSM:
					bFoundSSSM = True
					material.setOpacityTexture(textureFilePath2)
					material.setOcclTexture(textureFilePath2)
				elif textureType == "Heat_Mask" and not bFoundHM:
					bFoundHM = True
				elif textureType == "BloodTexture" and not bFoundBT:
					bFoundBT = True
				
				if bFoundSpecColour:
					material.setSpecularColor(texSpecColour[i][0])
				if bFoundAmbiColour:
					material.setAmbientColor(texAmbiColour[i][0])
				if bFoundMetallicColour:
					material.setMetal(texMetallicColour[i][0], 0.0)
				if bFoundRoughColour:
					material.setRoughness(texRoughColour[i][0], 0.0)
				if bFoundFresnelColour:
					material.setEnvColor(NoeVec4((1.0, 1.0, 1.0, texFresnelColour[i][0])))
					
				if bDebug:
					print("Type: " + textureType + " Name: " + textureName)
			material.setFlags(materialFlags)
			self.matList.append(material)
		
	def loadMeshFile(self, mdlList):
		bs = self.inFile

		rapi.parseInstanceOptions("-fbxnewexport")
		
		magic = bs.readUInt()
		unk00 = bs.readUShort()
		unk01 = bs.readUShort()
		fileSize = bs.readUInt()
		unk02 = bs.readUInt()
		
		unk03 = bs.readUShort()
		numModels = bs.readUShort()
		unk04 = bs.readUInt()
		
		self.rootDir = GetRootGameDir()
		self.createMaterials();
		
		headerOffsets = [bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64(),bs.readUInt64()]
		
		if bDebug:
			print("Header Offsets:")
			print(headerOffsets)
		
		bs.seek(headerOffsets[0], NOESEEK_ABS)
		countArray = bs.read("16B")
		
		if bDebug:
			print("Count Array")
			print(countArray)
		
		#AABB Min/Max
		bs.seek(0x30, NOESEEK_REL)
		
		offsetUnk00 = bs.readUInt64()
		bs.seek(offsetUnk00)
		
		if numModels == 0:
			print("Unsupported model type")
			return
		
		offsetInfo = []
		for i in range(countArray[0]):
			offsetInfo.append(bs.readUInt64())
			
		if bDebug:
			print("Vertex Info Offsets")
			print(offsetInfo)
		
		nameOffsets = []
		names = []
		nameRemapTable = []
		
		bs.seek(headerOffsets[9], NOESEEK_ABS)
		for i in range(numModels):
			nameRemapTable.append(bs.readUShort())
			
		bs.seek(headerOffsets[12], NOESEEK_ABS)
		for i in range(numModels):
			nameOffsets.append(bs.readUInt64())
			
		for i in range(numModels):
			bs.seek(nameOffsets[i], NOESEEK_ABS)
			names.append(bs.readString())
			
		if bDebug:
			print("Names:")
			print(names)
			
		#Skeleton
		bs.seek(headerOffsets[3], NOESEEK_ABS)
		
		if headerOffsets[3] > 0:
			boneInfo = [bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt64(), bs.readUInt64(), bs.readUInt64(), bs.readUInt64()]
			
			boneRemapTable = []
			for i in range(boneInfo[1]):
				boneRemapTable.append(bs.readShort())
				
			if bDebug:
				print(boneRemapTable)

			boneParentInfo = []
			bs.seek(boneInfo[4], NOESEEK_ABS)
			for i in range(boneInfo[0]):
				boneParentInfo.append([bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort()])
			
			bs.seek(boneInfo[5], NOESEEK_ABS)
			for i in range(boneInfo[0]):
				mat = NoeMat44.fromBytes(bs.readBytes(0x40)).toMat43()
				self.boneList.append(NoeBone(boneParentInfo[i][0], names[countArray[1] + i], mat, None, boneParentInfo[i][1]))
			self.boneList = rapi.multiplyBones(self.boneList)
		
		meshInfo = []
		bs.seek(headerOffsets[7], NOESEEK_ABS)
		meshInfo.append([bs.readUInt64(), bs.readUInt64(), bs.readUInt64(), bs.readUInt(), bs.readUInt(), bs.readUShort(), bs.readUShort(), bs.readUInt(), bs.readUInt(), bs.readUInt()])
		
		if bDebug:
			print("Mesh Info:")
			print(meshInfo)
		
		meshVertDeclInfo = []
		positionIndex = -1
		normalIndex = -1
		uvIndex = -1
		uv2Index = -1
		weightIndex = -1

		for i in range (meshInfo[0][6]):
			meshVertDeclInfo.append([bs.readUShort(), bs.readUShort(), bs.readUInt()])
			
			if meshVertDeclInfo[i][0] == 0 and positionIndex == -1:
				positionIndex = i
			elif meshVertDeclInfo[i][0] == 1 and normalIndex == -1:
				normalIndex = i
			elif meshVertDeclInfo[i][0] == 2 and uvIndex == -1:
				uvIndex = i
			elif meshVertDeclInfo[i][0] == 3 and uv2Index == -1:
				uv2Index = i
			elif meshVertDeclInfo[i][0] == 4 and weightIndex == -1:
				weightIndex = i
		
		if bDebug:
			print("Vert Decl info:")
			print(meshVertDeclInfo)
			
		bs.seek(meshInfo[0][1], NOESEEK_ABS)		
		vertexBuffer = bs.readBytes(meshInfo[0][3])
		
		for i in range(countArray[0]):
			meshVertexInfo = []
			ctx = rapi.rpgCreateContext()
			bs.seek(offsetInfo[i], NOESEEK_ABS)
			
			numOffsets = bs.readUInt()
			hash = bs.readUInt()
			offsetSubOffsets = bs.readUInt64()
			bs.seek(offsetSubOffsets, NOESEEK_ABS)
			
			offsetInfo2 = []
			for j in range(numOffsets):
				offsetInfo2.append(bs.readUInt64())
			
			if bDebug:
				print("Offset info 2")
				print(offsetInfo2)
			
			for j in range(numOffsets):
				bs.seek(offsetInfo2[j], NOESEEK_ABS)
				meshVertexInfo.append([bs.readUByte(), bs.readUByte(), bs.readUShort(), bs.readUInt(), bs.readUInt(), bs.readUInt()])

				if bDebug:
					print("Mesh vertex info:")
					print(meshVertexInfo)
				
				if bDebug:
					print(meshVertexInfo[j])
					
				indexBufferSplitData = []
				for k in range(meshVertexInfo[j][1]):
					indexBufferSplitData.append([bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUInt(), bs.readUInt(), bs.readUInt()])#Index, faceCount, indexBufferStartIndex, vertexStartIndex
				
				for k in range(meshVertexInfo[j][1]):
					#Search for material
					for l in range(len(self.matNames)):
						if self.matNames[l] == names[nameRemapTable[indexBufferSplitData[k][0]]]:
							rapi.rpgSetMaterial(self.matNames[l])
							break
							
					rapi.rpgSetName("Model_" + str(i) + "_Mesh_" + str(j) + "_" + str(k))
					rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))

					if positionIndex != -1:
						rapi.rpgBindPositionBufferOfs(vertexBuffer, noesis.RPGEODATA_FLOAT, meshVertDeclInfo[positionIndex][1], (meshVertDeclInfo[positionIndex][1] * indexBufferSplitData[k][6]))
					
					if normalIndex != -1 and bNORMsEnabled:
						if bDebugNormals:
							rapi.rpgBindColorBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, meshVertDeclInfo[normalIndex][1], meshVertDeclInfo[normalIndex][2] + (meshVertDeclInfo[normalIndex][1] * indexBufferSplitData[k][6]), 4)
						else:
							rapi.rpgBindNormalBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, meshVertDeclInfo[normalIndex][1], meshVertDeclInfo[normalIndex][2] + (meshVertDeclInfo[normalIndex][1] * indexBufferSplitData[k][6]))
						
					if uvIndex != -1 and bUVsEnabled:
						rapi.rpgBindUV1BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, meshVertDeclInfo[uvIndex][1], meshVertDeclInfo[uvIndex][2] + (meshVertDeclInfo[uvIndex][1] * indexBufferSplitData[k][6]))
					if uv2Index != -1 and bUVsEnabled:
						rapi.rpgBindUV2BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, meshVertDeclInfo[uv2Index][1], meshVertDeclInfo[uv2Index][2] + (meshVertDeclInfo[uv2Index][1] * indexBufferSplitData[k][6]))
						
					if weightIndex != -1 and bSkinningEnabled:
						rapi.rpgSetBoneMap(boneRemapTable)
						rapi.rpgBindBoneIndexBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, meshVertDeclInfo[weightIndex][1], meshVertDeclInfo[weightIndex][2] + (meshVertDeclInfo[weightIndex][1] * indexBufferSplitData[k][6]), 8)
						rapi.rpgBindBoneWeightBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, meshVertDeclInfo[weightIndex][1], meshVertDeclInfo[weightIndex][2] + (meshVertDeclInfo[weightIndex][1] * indexBufferSplitData[k][6]) + 8, 8)
					
					if indexBufferSplitData[k][4] > 0:
						bs.seek(meshInfo[0][2] + (indexBufferSplitData[k][5] * 2), NOESEEK_ABS)
						if bDebug:
							print("Index Buffer Start: " + str(bs.tell()))
						indexBuffer = bs.readBytes(indexBufferSplitData[k][4] * 2)
						if bDebug:
							print("Index Buffer End: " + str(bs.tell()))
						
						if bRenderAsPoints:
							rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, (meshVertexInfo[j][4] - (indexBufferSplitData[k][6] - vertexStartIndex)), noesis.RPGEO_POINTS, 0x1)
						else:
							rapi.rpgSetStripEnder(0x10000)
							rapi.rpgCommitTriangles(indexBuffer, noesis.RPGEODATA_USHORT, indexBufferSplitData[k][4], noesis.RPGEO_TRIANGLE, 0x1)
							rapi.rpgClearBufferBinds()
			try:
				mdl = rapi.rpgConstructModelSlim()
			except:
				mdl = NoeModel()
			mdl.setBones(self.boneList)
			mdl.setModelMaterials(NoeModelMaterials(self.texList, self.matList))
			mdlList.append(mdl)
		return mdlList
				
def meshLoadModel(data, mdlList):
	mesh = meshFile(data)
	mdlList = mesh.loadMeshFile(mdlList)
	#mesh.buildSkeleton()
	return 1