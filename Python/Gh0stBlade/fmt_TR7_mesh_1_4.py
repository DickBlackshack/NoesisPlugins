#Tomb Raider: Legend [PC] - ".tr7mesh" Loader
#By Gh0stblade
#v1.4
#Special thanks: Chrrox
#To do:

from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("Tomb Raider: Legend Next Generation 3D Mesh[PC]", ".tr7mesh")
	noesis.setHandlerTypeCheck(handle, meshCheckType)
	noesis.setHandlerLoadModel(handle, meshLoadModel)
	
	handle = noesis.register("Tomb Raider: Legend 2D Texture [PC]", ".pcd")
	noesis.setHandlerTypeCheck(handle, pcd9CheckType)
	noesis.setHandlerLoadRGBA(handle, pcd9LoadDDS)
	
	return 1
		
def meshCheckType(data):
	bs = NoeBitStream(data)
	bs.seek(0x10, NOESEEK_ABS)
	meshMagic = bs.readUInt()
	if meshMagic == 0x39444350:#PCD9
		print("PC Mesh File Detected!")
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(meshMagic) + " expected 0x39444350!"))
		return 0

def pcd9CheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	if magic == 0x39444350:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected 0x39444350!"))
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
	
class meshFile(object): 
	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.meshInfo = []
		self.numMesh = -1
		self.numMat = -1
		self.meshVertPos = -1
		self.meshUVPos = -1
		self.meshUV2Pos = -1
		self.meshNrmPos = -1
		self.meshBwPos = -1
		self.meshBiPos = -1
		self.meshColPos = -1
		self.offsetMeshGroupInfo = -1
		self.offsetMeshInfo = -1
		self.offsetBoneMap = -1
		self.offsetMatInfo = -1
		self.offsetFaceData = -1
		self.meshStart = 0
		self.boneList = []
		self.matList = []
		self.matNames = []
		self.texList = []
		
	def loadMainFile(self):#loads the mesh info
			bs = self.inFile
			bs.seek(0x10, NOESEEK_ABS)
			self.meshStart = bs.getOffset()
			
			meshMagic = bs.readUInt()
			meshVersion = bs.readUInt()
			meshFileSize = bs.readUInt()
			self.meshFaceCount = bs.readUInt()
			
			bs.seek(0x3C, NOESEEK_REL)#Collision box?
			
			self.offsetMeshGroupInfo = bs.readUInt()
			self.offsetMeshInfo = bs.readUInt()
			self.offsetBoneMap = bs.readUInt()
			self.offsetMatInfo = bs.readUInt()
			self.offsetFaceData = bs.readUInt()
			meshUnk00Offset = bs.readUInt()#???
			
			self.numMat = bs.readUShort()
			self.numMesh = bs.readUShort()
			self.BoneMapCount = bs.readUShort()
			numUnk00 = bs.readUShort()
			numUnk01 = bs.readUShort()
			numUnk02 = bs.readUShort()
			
			for i in range(0, self.numMesh):
				bs.seek(self.meshStart + self.offsetMeshInfo + i * 0xAC, NOESEEK_ABS)
				print("MesInfoOff ID: " + str(i) + " OFF: " + str(bs.tell()))
				meshFlags = bs.readUInt()
				meshGroupCount = bs.readUInt()
				meshBoneMapCount = bs.readUInt()
				meshBoneMapOffset = bs.readUInt()
				
				meshVertOffset = bs.readUInt()
				meshDummy = bs.readUInt()
				
				isDone = 0
				
				while isDone != 255:
					isDone = bs.readShort()
					meshBufferIndex = bs.readUShort()
					meshVertType = bs.readUShort()
					meshVertSubType = bs.readUShort()
					
					if meshVertType == 0x2 and meshVertSubType == 0x0:
						self.meshVertPos = meshBufferIndex
					elif meshVertType == 0x1 and meshVertSubType == 0x5:
						self.meshUVPos = meshBufferIndex
					elif meshVertType == 0x2 and meshVertSubType == 0x3:
						self.meshNrmPos = meshBufferIndex
					elif meshVertType == 0x6 and meshVertSubType == 0x2:
						self.meshBiPos = meshBufferIndex
					elif meshVertType == 0x4 and meshVertSubType == 0xA:
						self.meshBwPos = meshBufferIndex
					#elif meshVertType == 0x2 and meshVertSubType == 0x6:
						#self.meshColPos = meshBufferIndex
						
				bs.seek(self.meshStart + self.offsetMeshInfo + i * 0xAC + 0x98, NOESEEK_ABS)
				
				meshUnk00 = bs.readUInt()
				meshVertStride = bs.readUInt()
				meshVertCount = bs.readUInt()
				meshUnk01 = bs.readUInt()
				meshNumTris = bs.readUInt()
				
				self.meshInfo.append([meshFlags, meshGroupCount, meshBoneMapCount, meshBoneMapOffset, meshVertOffset, meshDummy, meshUnk00, meshVertStride, meshVertCount, meshUnk01, meshNumTris, self.meshVertPos, self.meshUVPos, self.meshNrmPos, self.meshBiPos, self.meshBwPos, self.meshColPos])
				
	def buildSkeleton(self):
		skelFileName = rapi.getDirForFilePath(rapi.getInputName()) + "skeleton.skl"
		if (rapi.checkFileExists(skelFileName)):
			print("Skeleton file detected!")
			print("Building Skeleton....")
			sd = rapi.loadIntoByteArray(skelFileName)
			sd = NoeBitStream(sd, NOE_LITTLEENDIAN)
			
			skelMagic = sd.readUInt()
			skelBoneCount = sd.readUInt()
			skelBoneCount2 = sd.readUInt()
			skelBoneStart = sd.readUInt()
			
			sd.seek(skelBoneStart, NOESEEK_ABS)
			for i in range(0, skelBoneCount):
				
				sd.seek(0x20, NOESEEK_REL)
				
				boneXPos = sd.readFloat()
				boneYPos = sd.readFloat()
				boneZPos = sd.readFloat()
				boneWPos = sd.readUInt()
				
				boneUnk00 = sd.readUInt()
				boneUnk01 = sd.readUInt()
				bonePID = sd.readInt()
				boneUnk02 = sd.readUInt()
				
				quat = NoeQuat([0, 0, 0, 1])
				mat = quat.toMat43()
				mat[3] = [boneXPos, boneZPos, -boneYPos]
				self.boneList.append(NoeBone(i, "bone%03i"%i, mat, None, bonePID))
			self.boneList = rapi.multiplyBones(self.boneList)
		else:
			print("Fatal, skeleton file non-existent!" + skelFileName)
		
	def buildMesh(self):
			bs = self.inFile
			print("Building Mesh....")
			self.meshGroupIdx = 0
			
			for i in range(0, self.numMesh):
			
				self.meshVertPos = self.meshInfo[i][11]
				self.meshUVPos = self.meshInfo[i][12]
				self.meshNrmPos = self.meshInfo[i][13]
				self.meshBwPos = self.meshInfo[i][14]
				self.meshBiPos = self.meshInfo[i][15]
				
				if self.meshInfo[i][2] != 0:
					bs.seek(self.meshStart + self.meshInfo[i][3], NOESEEK_ABS)
					boneMap = []
					for j in range(0, self.meshInfo[i][2]):
						boneMap.append(bs.readInt())
					rapi.rpgSetBoneMap(boneMap)
					
				for j in range(0, self.meshInfo[i][1]):
					bs.seek(self.meshStart + self.offsetMeshGroupInfo + self.meshGroupIdx * 0x14, NOESEEK_ABS)
					self.meshGroupIdx += 1
					
					meshFaceStart = bs.readUInt()
					meshFaceCount = bs.readUInt()
					meshVertCount = bs.readUInt()
					meshUnk00 = bs.readUInt()
					meshMatID = bs.readUInt()
					
					#matName = str(meshMatID) + ".pcd"
					#meshMat = NoeMaterial(matName, "")
					#meshMat.setTexture(matName)
					#meshMat.setFlags(noesis.NMATFLAG_TWOSIDED, 0)
					#self.matList.append(meshMat)
					#self.matNames.append(matName)
					#rapi.rpgSetMaterial(self.matNames[self.meshGroupIdx - 1])
			
					bs.seek(self.meshStart + self.offsetFaceData + meshFaceStart * 0x2, NOESEEK_ABS)
					faceBuff = bs.readBytes(meshFaceCount * 0x6)
					
					bs.seek(self.meshStart + self.meshInfo[i][4], NOESEEK_ABS)
					vertBuff = bs.readBytes(self.meshInfo[i][7] * self.meshInfo[i][8])
					
					rapi.rpgSetName("mesh_" + str(i) + "_group_" + str(j))	
					rapi.rpgSetTransform(NoeMat43((NoeVec3((1, 0, 0)), NoeVec3((0, 0, 1)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, 0)))))
					
					if self.meshVertPos != -1:
						rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, self.meshInfo[i][7], self.meshInfo[i][11])
					if self.meshUVPos != -1:
						rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, self.meshInfo[i][7], self.meshInfo[i][12])
					if self.meshNrmPos != -1:
						rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, self.meshInfo[i][7], self.meshInfo[i][13])
					if self.meshBiPos != -1:
						rapi.rpgBindBoneIndexBufferOfs(vertBuff, noesis.RPGEODATA_USHORT, self.meshInfo[i][7], self.meshInfo[i][14], 0x2)
					if self.meshBwPos != -1:
						rapi.rpgBindBoneWeightBufferOfs(vertBuff, noesis.RPGEODATA_UBYTE, self.meshInfo[i][7], self.meshInfo[i][15], 0x4)
					if self.meshColPos != -1:
						rapi.rpgBindColorBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, self.meshInfo[i][7], self.meshInfo[i][16], 3)
					rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshFaceCount * 3, noesis.RPGEO_TRIANGLE, 0x1)
					rapi.rpgClearBufferBinds()
					
				self.numMesh = -1
				self.meshVertPos = -1
				self.meshUVPos = -1
				self.meshUV2Pos = -1
				self.meshNrmPos = -1
				self.meshBwPos = -1
				self.meshBiPos = -1
				self.meshColPos = -1
			
def meshLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	parser = meshFile(data)
	parser.loadMainFile()
	parser.buildMesh()
	parser.buildSkeleton()
	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()
	mdl.setBones(parser.boneList)
	mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
	mdlList.append(mdl);
	return 1