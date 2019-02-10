#ICO HD [PS3] .cmdl Mesh Loader
#By Gh0stblade
#Special shoutout: Chrrox (ofc)
#v0.8b

from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("ICO HD [PS3]", ".cmdl")
	noesis.setHandlerTypeCheck(handle, cmdlCheckType)
	noesis.setHandlerLoadModel(handle, cmdlLoadModel)
	return 1

def cmdlCheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readInt()
	if magic != 0x4C444F4D: 												#"MODL"
		print("Fatal Error: Unknown filetype!")
		return 0     
	return 1
	

class cmdlFile(object): 

	def __init__(self, data):     
          
		self.inFile = NoeBitStream(data, NOE_BIGENDIAN)
		rapi.rpgSetOption(noesis.RPGOPT_BIGENDIAN, 1)
		rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
		self.meshInfo = []
		self.boneMap = []
		self.boneList = []
		self.numEntries = -1
		self.numVerts = -1
		self.numFaces = -1
		self.numNorms = -1
		self.numColors = -1
		self.numBones = -1
		self.numMeshes = -1
		
	def loadHeader(self):
		bs = self.inFile
		bs.seek(0xC, NOESEEK_ABS)												#Skip to entry cout
		self.numEntries = bs.readUInt()											#Number of entries
		print("Number of entries: " + str(self.numEntries))
		
	def loadMainFile(self):
		bs = self.inFile
		bs.seek(0x0, NOESEEK_ABS)
		
		for i in range(0, self.numEntries + 1):
			self.entryName = bs.readUInt()										#Name of the entry
			entryUnk00 = bs.readUShort()										#???
			entryUnk01 = bs.readUShort()										#???
			self.entryOffset = bs.readUInt()									#???
			self.entrySize = bs.readInt()										#???
			
			tempOffset = bs.getOffset()											#Save temp offset
			
			if self.entryName in cmdlObjectLoaderDict:
				cmdlObjectLoaderDict[self.entryName](self, bs)
				bs.seek(tempOffset, NOESEEK_ABS)								#Go back to old offset
			else:
				print("Fatal Error: Unknown entry type:", str(hex(self.entryName)), "at offset:", str(hex(self.entryOffset)))
		
		
	def loadVertices(self, bs):
		print("Loading Vertices....")
		bs.seek(self.entryOffset + 0xC, NOESEEK_ABS)							#Skip to entry offset
		self.vertBuffer = bs.readBytes(self.entrySize)							#Read the vertices
		self.numVerts = int(self.entrySize / 0x10)								#Get the vert count
		print("Finished loading vertices!")
		
	def loadFaces(self, bs):
		print("Loading mesh info!")
		bs.seek(self.entryOffset + 0xC, NOESEEK_ABS)							#Skip to entry offset
		self.numFaces = bs.readUInt()											#Read face count
		faceStart = bs.getOffset()												#Save face position
		bs.seek(self.numFaces * 0x4, NOESEEK_REL)								#Skip the faces
		print(bs.tell())
		
		self.unk00 = bs.readInt()
		self.numMeshes = bs.readInt()											#Number of bone maps
		for i in range(0, self.numMeshes):
			meshUnk00 = bs.readInt()
			meshUnk01 = bs.readInt()
			meshUnk02 = bs.readInt()
			meshUnk03 = bs.readInt()
			
			meshUnk04 = bs.readInt()
			meshUnk05 = bs.readInt()
			bs.seek(0x3, NOESEEK_REL)
			meshUnk06 = bs.readInt()
			
			meshVertCount = bs.readInt()
			meshUnk07 = bs.readInt()
			meshFaceCount = bs.readInt()
			
			numBoneIndices = bs.readInt()
			
			bidList = []														#Declare new boneID list array[]
			
			for j in range(0, numBoneIndices):
				bidList.append(bs.readInt())
			self.boneMap.append(bidList)
			bs.seek(0x8, NOESEEK_REL)
			
			temp = bs.getOffset()												#Save temp position
			
			#get the face data
			bs.seek(faceStart, NOESEEK_ABS)										#Skip to face start
			faceStartIdx = bs.readInt()											#Get the start face Idx
			bs.seek(faceStart, NOESEEK_ABS)										#Skip to face start
			
			faceData = []
			for j in range(0, meshFaceCount):
				face = bs.readUInt() - faceStartIdx
				faceData.append(face)
			faceStart = bs.getOffset()											#Save new face start offset
			#						0				1				2		3			4
			self.meshInfo.append([meshVertCount, meshFaceCount, faceData])
			
			bs.seek(temp, NOESEEK_ABS)										#Skip to temp position
		print("Finished loading mesh info!")
		
		
	def loadNormals(self, bs):
		print("Loading Normals....")
		bs.seek(self.entryOffset + 0xC, NOESEEK_ABS)							#Skip to entry offset
		self.normBuffer = bs.readBytes(self.entrySize)							#Read the normals
		self.numNorms = int(self.entrySize / 0x4)								#Get normal count
		print("Finished loading normals!")
		
	def loadColors(self, bs):
		print("Loading Colors....")
		bs.seek(self.entryOffset + 0xC, NOESEEK_ABS)							#Skip to entry offset
		self.colorBuffer = bs.readBytes(self.entrySize)							#Read the colors
		self.numColors = int(self.entrySize / 0x4)								#Get color count
		print("Finished loading colors!")
		
	def loadUVs(self, bs):
		print("Loading UVs....")
		bs.seek(self.entryOffset + 0xC, NOESEEK_ABS)							#Skip to entry offset
		self.uvBuffer = bs.readBytes(self.entrySize)							#Read the colors
		self.numUVs = int(self.entrySize / 0x4)									#Get uv count
		print("Finished loading UVs!")
		
	def loadBoneIndices(self, bs):
		print("Loading Bone Indices....")
		bs.seek(self.entryOffset + 0xC, NOESEEK_ABS)							#Skip to entry offset
		boneIDList = []
		self.boneIdxBuffer = bs.readBytes(self.entrySize)							#Read the indices
		
		#Load the skeleton
		skelFileName = rapi.getDirForFilePath(rapi.getInputName()) + "skelton.skb"	#Set skeleton filename "skelton.skb"
		if (rapi.checkFileExists(skelFileName)):									#If it exists
			print("Skeleton file detected!")										#Print detected message
			skelData = rapi.loadIntoByteArray(skelFileName)							#Load into byte array "skelData"
			self.numBones = int(len(skelData) / 0x40)								#self.numBones is the length divided by 0x40
			skelData = NoeBitStream(skelData, NOE_LITTLEENDIAN)						#The bone data is endian little
			for i in range(0, self.numBones):										#For each bone
				
				boneID = skelData.readInt()											#Read bone ID
				boneUnk00 = skelData.readFloat()
				boneUnk01 = skelData.readFloat()
				boneUnk02 = skelData.readFloat()
				
				boneX = skelData.readFloat()
				boneY = skelData.readFloat()
				boneZ = skelData.readFloat()
				scale = skelData.readFloat()
				
				quatX = skelData.readFloat()
				quatY = skelData.readFloat()
				quatZ = skelData.readFloat()
				quatW = skelData.readFloat()
				
				boneUnk03 = skelData.readFloat()
				boneUnk04 = skelData.readFloat()
				bonePID = skelData.readInt()
				boneUnk06 = skelData.readFloat()
				
				quat = NoeQuat([quatX, quatY, quatZ, quatW])
				mat = quat.toMat43()
				mat[3] = [boneX, boneY, boneZ]
				self.boneList.append(NoeBone(i, "bone%03i"%i, mat, None, bonePID))
			self.boneList = rapi.multiplyBones(self.boneList)
		print("Finished loading bone indices!")
		
	def loadBoneWeights(self, bs):
		print("Loading Bone Weights....")
		bs.seek(self.entryOffset + 0xC, NOESEEK_ABS)							#Skip to entry offset
		self.weightBuffer = bs.readBytes(self.entrySize)						#Read the weights
		print("Finished loading bone weights!")
		
		
	def build_mesh(self):
		bs = self.inFile
		print("Building Mesh....")
		vertStart = 0
		for i in range(0, self.numMeshes):
			print(self.boneMap[i])
		for i in range(0, self.numMeshes):
			rapi.rpgSetBoneMap(self.boneMap[i])
			rapi.rpgSetName("mesh_" + str(i + 1))
			rapi.rpgSetMaterial("mesh_" + str(i + 1) + ".dds")
			faceBuff = struct.pack(">" + 'I'*len(self.meshInfo[i][2]), *self.meshInfo[i][2])
			rapi.rpgBindPositionBufferOfs(self.vertBuffer, noesis.RPGEODATA_FLOAT, 0x10, vertStart)
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_UINT, self.meshInfo[i][1], noesis.RPGEO_TRIANGLE, 1)
			
			#rapi.rpgBindNormalBufferOfs(self.normBuffer, noesis.RPGEODATA_BYTE, 0x4, 0)
			# if not emptyrapi.rpgBindColorBufferOfs(self.colorBuffer, noesis.RPGEODATA_BYTE, 0x4, 0, 4)
			#rapi.rpgBindUV1BufferOfs(self.uvBuffer, noesis.RPGEODATA_UBYTE, 0x4, 0x0)
			
			rapi.rpgBindBoneIndexBufferOfs(self.boneIdxBuffer, noesis.RPGEODATA_UBYTE, 0x2, 0, 0x1)
			rapi.rpgBindBoneWeightBufferOfs(self.weightBuffer, noesis.RPGEODATA_HALFFLOAT, 0x8, 0, 0x4)
			#rapi.rpgBindBoneWeightBuffer(self.weightBuffer, noesis.RPGEODATA_BYTE, 0x8, 0)
			vertStart += self.meshInfo[i][0] * 0x10
		rapi.rpgClearBufferBinds()
			

cmdlObjectLoaderDict = {
0x4D4F444C : cmdlFile.loadFaces,							#"MODL" 
0x504F5330 : cmdlFile.loadVertices,							#"POS0"
0x4E524D30 : cmdlFile.loadNormals,							#"NORM0"
0x434F4C30 : cmdlFile.loadColors,							#"COL0"
0x54455830 : cmdlFile.loadUVs,								#"TEX0"
0x424F4E49 : cmdlFile.loadBoneIndices,						#"BONI"
0x424F4E57 : cmdlFile.loadBoneWeights,						#"BONW"
}

def cmdlLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	parser = cmdlFile(data)
	parser.loadHeader()
	parser.loadMainFile()
	parser.build_mesh()
	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()
	mdl.setBones(parser.boneList)
	mdlList.append(mdl);
	return 1
	