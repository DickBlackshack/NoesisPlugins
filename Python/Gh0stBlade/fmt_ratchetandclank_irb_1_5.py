#Ratchet and Clank: Into the Nexus [PS3] - ".irb" Loader
#By Gh0stblade
#v1.5
#Special thanks: Chrrox

from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("Ratchet and Clank: Into the Nexus [PS3]", ".irb")
	noesis.setHandlerTypeCheck(handle, irbCheckType)
	noesis.setHandlerLoadModel(handle, irbLoadModel)
	noesis.logPopup()
	return 1

def irbCheckType(data):
	bs = NoeBitStream(data)
	if bs.readUInt() != 0x57484749:
		print("Fatal Error: Unknown file magic: expected 0x57484749!")
		return 0
	return 1
		
class irbFile(object): 
	def __init__(self, data):
		self.inFile = NoeBitStream(data, NOE_BIGENDIAN)
		rapi.rpgSetOption(noesis.RPGOPT_BIGENDIAN, 1)
		self.texHashList = []
		self.meshCount = -1
		self.meshScaleX = -1
		self.meshScaleY = -1
		self.meshScaleZ = -1
		self.inputPath = -1
		self.boneList = []
		self.boneMapInfo = []
		self.meshInfo = []
		self.boneMap = []
		self.faceBuff = []
		self.vertBuff = []
		self.texPaths = []
		self.texPathStream = []
		self.meshType = -1
		self.meshInfo = []
		self.numMesh = -1
		
	def loadMainFile(self):
		bs = self.inFile
		bs.seek(0x0, NOESEEK_ABS)
		
		magic = bs.readUInt()
		minorVersion = bs.readUShort()
		majorVersion = bs.readUShort()
		numEntries = bs.readUInt()
		offsetEntryStart = bs.readUInt()
		
		offsetUnk00 = bs.readUInt()
		numUnk00 = bs.readUInt()
		
		for i in range(numEntries):
			bs.seek((i * 0x10) + 0x20, NOESEEK_ABS) 
			entryType = bs.readUInt()
			if entryType in irbEntryTypeList:
				irbEntryTypeList[entryType](self, bs, bs.readUInt(), bs.readUShort(), bs.readUShort(), bs.readUInt())
			else:
				print("Fatal Error: Unknown entry type:" + str(hex(entryType)))
				
	def loadMeshTexHash(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Mesh Texture Hashes....")
		bs.seek(entryOffset, NOESEEK_ABS)
		for i in range(entryCount):
			bs.seek(entryOffset + i * entrySize, NOESEEK_ABS)
			self.texHashList.append([str(hex(struct.unpack('>Q', bs.readBytes(entrySize))[0]) + ".dds")])
			print(self.texHashList[i][0])
		print("Finished loading texture hashes!")
	
	def loadMeshCount(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Mesh count Info....")
		bs.seek(entryOffset, NOESEEK_ABS)
		self.meshCount = bs.readUInt()
		print("Mesh Count: " + str(self.meshCount))
		print("Finished loading mesh count info!")
		
	def loadMeshScaleV1(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Mesh Scale Info....")
		bs.seek(entryOffset + 0x70, NOESEEK_ABS)
		self.meshScaleX = self.meshScaleY = self.meshScaleZ = struct.unpack('>f', (struct.pack('>I', bs.readInt() + 0x7800000)))[0]
		print("The Mesh's scale is: (" + str(self.meshScaleX) + ", " + str(self.meshScaleY) + ", " + str(self.meshScaleZ) + ")")
		print("Finished loading mesh scale!")

	def loadMeshScaleV2(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Mesh Scale Info....")
		bs.seek(entryOffset + 0x20, NOESEEK_ABS)
		self.meshScaleX = struct.unpack('>f', (struct.pack('>I', bs.readInt() + 0x7800000)))[0]
		self.meshScaleY = struct.unpack('>f', (struct.pack('>I', bs.readInt() + 0x7800000)))[0]
		self.meshScaleZ = struct.unpack('>f', (struct.pack('>I', bs.readInt() + 0x7800000)))[0]
		print("The Mesh's scale is: (" + str(self.meshScaleX) + ", " + str(self.meshScaleY) + ", " + str(self.meshScaleZ) + ")")
		print("Finished loading mesh scale!")

	def loadMeshInputPath(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Input Path....")
		bs.seek(entryOffset, NOESEEK_ABS)
		self.InputPath = bs.readString()
		print("The input file is: " + str(self.InputPath))
		print("Finished Input Path!")
		
	def loadMeshBones(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Bones....")
		
		bs.seek(entryOffset, NOESEEK_ABS)
		numBones = bs.readShort()
		boneRoot = bs.readShort()
		boneOffsetParentInfo = bs.readInt()
		boneOffsetMtx1 = bs.readInt()
		boneOffsetMtx2 = bs.readInt()
		boneUnk00 = bs.readShort()
		boneUnk01 = bs.readShort()
		offsetBoneUnk02 = bs.readInt()
		
		for i in range(numBones):
			bs.seek(boneOffsetParentInfo + i * 0x8, NOESEEK_ABS)
			boneID = bs.readShort()
			bonePID = bs.readShort()
			boneUnk00 = bs.readShort()
			boneUnk01 = bs.readShort()
			bs.seek(boneOffsetMtx1 + i * 64, NOESEEK_ABS)
			boneMtx = NoeMat44.fromBytes(bs.readBytes(64), NOE_BIGENDIAN).toMat43()
			bone = NoeBone(i, "bone%03i"%i, boneMtx, None, bonePID)
			self.boneList.append(bone)
		print("Finished loading:" + str(numBones) + " bones!")
		
	def loadMeshBoneMap(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Bone Map info....")
		for i in range(entryCount):
			bs.seek(entryOffset + i * 0x8, NOESEEK_ABS)
			offsetMeshInfo = bs.readInt()
			boneMapCount = bs.readInt()
			self.boneMapInfo.append([offsetMeshInfo, boneMapCount])
		print("Finished loading bone map info!")
		
	def loadMeshInfoV1(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Mesh Info....")
		self.numMesh = entryCount
		self.meshType = 0x0
		for i in range(entryCount):
			bs.seek(((entryOffset) + i * 0x40), NOESEEK_ABS)
			meshFaceStart = bs.readUInt()
			meshVertStart = bs.readUInt()
			meshMatID = bs.readUShort()
			meshVertCount = bs.readUShort()
			meshBoneIdxCount = bs.readUByte()
			meshType = bs.readUByte()
			meshBoneMapIdx = bs.readUByte()
			meshUnk00 = bs.readUByte()
			
			meshUnk01 = bs.readUShort()
			meshFaceCount = bs.readUShort()
			meshUnk02 = bs.readUInt()
			meshUnk03 = bs.readUInt()
			meshUnk04 = bs.readUInt()
			
			meshOffsetBoneMap = bs.readUInt()
			meshUnk05 = bs.readUInt()
			meshVertType = bs.readUByte()
			meshUnk06 = bs.readUByte()
			meshUnk07 = bs.readUShort()
			meshUnk08 = bs.readUInt()
			
			meshUnk09 = bs.readUShort()
			meshUnk10 = bs.readUShort()
			meshUnk11 = bs.readUShort()
			meshUnk12 = bs.readUShort()
			meshUnk13 = bs.readUShort()
			meshUnk14 = bs.readUShort()
			meshUnk15 = bs.readUShort()
			meshUnk16 = bs.readUShort()
									#0				   1			2			3			 4			5				6				  7			        8				9			10
			self.meshInfo.append([meshFaceStart, meshVertStart, meshMatID, meshVertCount, meshType, meshVertType, meshOffsetBoneMap, meshBoneMapIdx, meshFaceCount, meshBoneIdxCount, meshMatID])
			
			bidList = []
			bs.seek(meshOffsetBoneMap, NOESEEK_ABS)
			
			for j in range(meshBoneIdxCount):
				bidList.append(bs.readShort())
			self.boneMap.append([bidList])
		print("Finished Loading Mesh Info!")
		
	def loadMeshInfoV2(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Mesh Info....")
		self.numMesh = entryCount
		self.meshType = 0x1
		for i in range(entryCount):
			bs.seek(((entryOffset) + i * 0x40), NOESEEK_ABS)
			meshFaceStart = bs.readUInt()
			meshVertStart = bs.readUShort()
			meshVertStart2 = bs.readUShort()
			meshVertCount = bs.readUShort()
			meshUnk00 = bs.readUByte()
			meshUnk01 = bs.readUByte()
			meshType = bs.readUByte()
			meshType2 = bs.readUByte()
			meshUnk03 = bs.readUByte()
			meshUnk04 = bs.readUByte()
			
			meshUnk01 = bs.readUShort()
			meshFaceCount = bs.readUShort()
			meshUnk02 = bs.readUInt()
			meshUnk03 = bs.readUInt()
			
			meshOffsetBoneMap = bs.readUInt()
			meshUnk05 = bs.readUInt()
			meshVertType = bs.readUByte()
			meshUnk06 = bs.readUByte()
			meshUnk07 = bs.readUShort()
			meshUnk08 = bs.readUInt()
			
			meshUnk09 = bs.readUShort()
			meshUnk10 = bs.readUShort()
			meshUnk11 = bs.readUShort()
			meshUnk12 = bs.readUShort()
			meshUnk13 = bs.readUShort()
			meshUnk14 = bs.readUShort()
			meshUnk15 = bs.readUShort()
			meshUnk16 = bs.readUShort()
									#0				   1			2				3			 4				5				6			  7		        8			9			10
			self.meshInfo.append([meshFaceStart, meshVertStart, meshVertStart2, meshVertCount, meshType, meshVertType, meshOffsetBoneMap, meshUnk03, meshFaceCount, meshUnk00, meshVertStart2])
		print("Finished Loading Mesh Info!")
		
	def loadMeshFaceIndices(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Face Indices....")
		bs.seek(entryOffset, NOESEEK_ABS)
		self.faceBuff = bs.readBytes(entryCount * entrySize)
		print("Finished Loading Face Indices!")
		
	def loadMeshVertices(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Vertices....")
		bs.seek(entryOffset, NOESEEK_ABS)
		self.vertBuff = bs.readBytes(entryCount * entrySize)
		print("Finished Loading Vertices!")

	def loadMeshTexOffs(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading Texture path offsets....")
		for i in range(entryCount):
			bs.seek(entryOffset + i * entrySize, NOESEEK_ABS)
			texOffset = bs.readUInt()
			bs.seek(texOffset, NOESEEK_ABS)
			self.texPaths.append([bs.readString()])
			print(self.texPaths[i][0])
		print("Finished loading texture path offsets!")
		
	def loadMeshTexStrs(self, bs, entryOffset, entryFlags, entryCount, entrySize):
		print("Loading texture path stream....")
		bs.seek(entryOffset, NOESEEK_ABS)
		self.texPathStream = bs.readBytes(entryCount * entrySize)
		print("Finished loading path stream!")
		
		
	def buildMeshV1(self, meshInfo, index):
		bs = self.inFile
		rapi.rpgSetName("Mesh_" + str(index + 1))
		rapi.rpgSetMaterial("Material_" + str(meshInfo[2]))
		rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 0)
		rapi.rpgSetPosScaleBias((self.meshScaleX, self.meshScaleY, self.meshScaleZ), (0, 0, 0))
			
		if meshInfo[4] == 0:
			#Vertices
			vs = NoeBitStream(self.vertBuff, NOE_BIGENDIAN)
			vs.seek(meshInfo[1], NOESEEK_ABS)
			vertBuff = vs.readBytes(meshInfo[3] *  0x14)
			
			#Faces
			fs = NoeBitStream(self.faceBuff, NOE_BIGENDIAN)
			fs.seek(meshInfo[0] * 0x2, NOESEEK_ABS)
			faceBuff = fs.readBytes(meshInfo[8] * 0x2)

			#Bone Map
			if meshInfo[9] != 0:
				rapi.rpgSetBoneMap(self.boneMap[meshInfo[7]][0])
				fakeBoneBuffer = [0x00, 0xFF] * meshInfo[3]

			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_SHORT, 0x14, 0x0)
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 0x14, 0x8)
			#rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_SHORT, 0x14, 0x8)#FIXME
			if meshInfo[9] != 0:
				rapi.rpgBindBoneIndexBufferOfs(bytes(fakeBoneBuffer), noesis.RPGEODATA_UBYTE, 0x2, 0x0, 0x1)
				rapi.rpgBindBoneWeightBufferOfs(bytes(fakeBoneBuffer), noesis.RPGEODATA_UBYTE, 0x2, 0x1, 0x1)
			
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[8], noesis.RPGEO_TRIANGLE, 1)
			
		elif meshInfo[4] == 1:
			#Vertices
			vs = NoeBitStream(self.vertBuff, NOE_BIGENDIAN)
			vs.seek(meshInfo[1], NOESEEK_ABS)
			vertBuff = vs.readBytes(meshInfo[3] *  0x1C)
			
			#Faces
			fs = NoeBitStream(self.faceBuff, NOE_BIGENDIAN)
			fs.seek(meshInfo[0] * 0x2, NOESEEK_ABS)
			faceBuff = fs.readBytes(meshInfo[8] * 0x2)	
			
			#Bone Map
			if meshInfo[9] != 0:
				rapi.rpgSetBoneMap(self.boneMap[meshInfo[7]][0])
			
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_SHORT, 0x1C, 0x0)
			rapi.rpgBindBoneIndexBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, 0x1C, 0x8, 4)
			rapi.rpgBindBoneWeightBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, 0x1C, 0x0C, 0x4)
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 0x1C, 0x10)
			#rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_SHORT, 0x1C, 0x10)#FIXME
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[8], noesis.RPGEO_TRIANGLE, 1)
		rapi.rpgClearBufferBinds()
			
	def buildMeshV2(self, meshInfo, index):
		bs = self.inFile
		rapi.rpgSetName("Mesh_" + str(index + 1))
		rapi.rpgSetPosScaleBias((self.meshScaleX, self.meshScaleY, self.meshScaleZ), (0, 0, 0))
		
		meshInfo[4] = 0x0 #TEMP, not tested for any other vert types! plus [i][4] won't match!
		
		if meshInfo[4] == 0:
			#Vertices
			vs = NoeBitStream(self.vertBuff, NOE_BIGENDIAN)
			vs.seek(meshInfo[1] * 0x14, NOESEEK_ABS)
			vertBuff = vs.readBytes(meshInfo[3] *  0x14)
			
			#Faces
			fs = NoeBitStream(self.faceBuff, NOE_BIGENDIAN)
			fs.seek(meshInfo[0] * 0x2, NOESEEK_ABS)
			faceBuff = fs.readBytes(meshInfo[8] * 0x2)
			
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_SHORT, 0x14, 0x0)
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 0x14, 0x8)
			rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_SHORT, 0x14, 0x8)#FIXME
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[8], noesis.RPGEO_TRIANGLE, 1)
		elif meshInfo[4] == 1:
			pass
			#Unimplmented
		rapi.rpgClearBufferBinds()
			
	def loadMeshes(self):
		for i in range(self.numMesh):
			print("Building mesh: " + str(i + 1) + " of: " + str(self.numMesh))
			if self.meshType == 0x0: 	#Normal meshes (Mobys)
				irbFile.buildMeshV1(self, self.meshInfo[i], i)
			else:						#Static meshes (Ties)
				irbFile.buildMeshV2(self, self.meshInfo[i], i)
			
irbEntryTypeList = {
0x3000		:	irbFile.loadMeshVertices,
0x3200		:	irbFile.loadMeshFaceIndices,
0x3300		:	irbFile.loadMeshInfoV2,
0x3400		:	irbFile.loadMeshScaleV2,
0x3410		:	irbFile.loadMeshInputPath,
0x5600		:	irbFile.loadMeshTexHash,
0xD000		:	irbFile.loadMeshCount,
0xD100		:	irbFile.loadMeshScaleV1,
0xD200		:	irbFile.loadMeshInputPath,
0xD300		:	irbFile.loadMeshBones,
0xD700		:	irbFile.loadMeshBoneMap,
#0xD800 	:	irbFile.loadMeshUnk00, #??? Probably mesh positions?
0xDD00  	:	irbFile.loadMeshInfoV1,
0xE100		:	irbFile.loadMeshFaceIndices,
0xE200		:	irbFile.loadMeshVertices,
0x27000		:	irbFile.loadMeshTexOffs,
0x27100		:	irbFile.loadMeshTexStrs,  
}

def irbLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	parser = irbFile(data)
	fileLength = len(data)
	parser.loadMainFile()
	parser.loadMeshes()
	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()
	mdl.setBones(parser.boneList)
	#mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
	mdlList.append(mdl);
	return 1
