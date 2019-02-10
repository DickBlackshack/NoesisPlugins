#Resident Evil/Biohazard: The Mercenaries 3D/Revelations [3DS] - ".mod" Loader
#By Gh0stblade
#v1.2
#Special thanks: Chrrox

from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("Resident Evil/Biohazard: The Mercenaries 3D/Revelations [3DS]", ".3dsmod")
	noesis.setHandlerTypeCheck(handle, modCheckType)
	noesis.setHandlerLoadModel(handle, modLoadModel)
	noesis.logPopup()
	return 1

def modCheckType(data):
	bs = NoeBitStream(data)
	if bs.readUInt() == 0x00444F4D:
		return 1
	else: 
		return 0
		
class modFile(object): 
	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.boneList = []
		self.boneMap = []
		
	def loadModFile(self):
		bs = self.inFile
		modHdr = bs.read("1I4H13I")
		modFile.loadSkeleton(self, modHdr)
		modFile.loadMeshes(self, modHdr)
		
	def loadMeshes(self, modHdr):
		bs = self.inFile
		for i in range(modHdr[3]):
			bs.seek(modHdr[15] + (i * 0x30), NOESEEK_ABS)
			print("MeshInfoStart: " + str(bs.tell()))
			modFile.buildMesh(self, modHdr, bs.read("2H8B5I"), i)
			
	
	def buildMesh(self, modHdr, meshInfo, index):
		bs = self.inFile
		
		#if meshInfo[3] != 0x0: this is the lod group, needs indexing then drawing and constructing then appending to mdllist to split out meshes
		#	return
		rapi.rpgSetName("Mesh_" + str(index + 1))
		#print(self.boneMap)
		#rapi.rpgSetBoneMap(self.boneMap)
		#rapi.rpgSetTransform(NoeMat43((NoeVec3((-1, 0, 0)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, -1)), NoeVec3((0, 0, 0)))))
		print("Mesh_" + str(index + 1))
		scale = 40.0
		rapi.rpgSetPosScaleBias((scale, scale, scale), (0, 0, 0))
		#@FIXME what if stride not same? this is causing glitch? maybe it should be last one?
		bs.seek((modHdr[16] + (meshInfo[8] * meshInfo[10])), NOESEEK_ABS)
		print("VS: " + str(bs.tell()))
		vertBuff = bs.readBytes(meshInfo[8] * meshInfo[1])
		print("VE: " + str(bs.tell()))
		
		bs.seek((modHdr[17] + (meshInfo[13] * 0x2)), NOESEEK_ABS)
			
		faceData = []
		for j in range(0, meshInfo[14]):
			face = bs.readUShort() - meshInfo[10]
			faceData.append(face)
		faceBuff = struct.pack("<" + 'H'*len(faceData), *faceData)
		
		print("Vert Stride: " + str(meshInfo[8]))
		if meshInfo[12] == 0x1b36016:
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 0)
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 16)
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_TRIANGLE_STRIP, 1)
		elif meshInfo[12] == 0x1289500d:
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 0)
			rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 12)
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 16)
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_TRIANGLE_STRIP, 1)
		elif meshInfo[12] == 0x43FB3015:
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 0)
			rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 12)
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 16)
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_TRIANGLE_STRIP, 1)
		elif meshInfo[12] == 0x59dc400b:
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 0)
			rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 12)
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 16)
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_TRIANGLE_STRIP, 1)
		elif meshInfo[12] == 0x638F1011:
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 0)
			rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 12)
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 16)
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_TRIANGLE_STRIP, 1)
		elif meshInfo[12] == 0x82917009:
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 0)
			rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 12)#???
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 16)
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_TRIANGLE_STRIP, 1)
		elif meshInfo[12] == 0x9a9d201d:
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 0)
			rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 12)#???
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 16)
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_TRIANGLE_STRIP, 1)
		elif meshInfo[12] == 0x9dfd7019:
			print("************************TEST: " + str(meshInfo[8]))
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 0)
			rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, meshInfo[8], noesis.RPGEO_POINTS, 1)
			#rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_TRIANGLE_STRIP, 1)
		elif meshInfo[12] == 0xF606F017:
			rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 0)
			rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 12)
			rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, meshInfo[8], 16)
			#rapi.rpgBindBoneWeightBufferOfs(vertBuff, noesis.RPGEODATA_BYTE, meshInfo[8], 28, 4)
			#rapi.rpgBindBoneIndexBufferOfs(vertBuff, noesis.RPGEODATA_USHORT, meshInfo[8], 32, 1)	
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, meshInfo[14], noesis.RPGEO_TRIANGLE_STRIP, 1)
		else:
			print("Fatal Error: Unknown FVF: " + str(hex(meshInfo[12])))
		rapi.rpgClearBufferBinds()
			
	def loadSkeleton(self, modHdr):
		bs = self.inFile
		
		for i in range(modHdr[2]):
			bs.seek((modHdr[12] + (i * 0x18)), NOESEEK_ABS)
			boneUnk00 = bs.readUByte()
			bonePID = bs.readUByte()
			bs.seek(((modHdr[12] + (modHdr[2] * 0x18)) + i * 0x40), NOESEEK_ABS)
			boneMtx1 = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()
			bs.seek((((modHdr[12] + (modHdr[2] * 0x18)) + modHdr[2] * 0x40) + i * 0x40), NOESEEK_ABS)
			boneMtx2 = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()
			bone = NoeBone(i, "bone%03i"%i, boneMtx2, None, bonePID)
			self.boneList.append(bone)
		boneMapTable = bs.readBytes(256)
		for i in range(bs.readUInt()):
			self.boneMap.append(bs.readByte())
			
def modLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	mesh = modFile(data)
	mesh.loadModFile()
	#mesh.loadMaterials()
	#mesh.buildMesh()
	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()
	mdl.setBones(mesh.boneList)
	#mdl.setModelMaterials(NoeModelMaterials(mesh.texList, mesh.matList))
	mdlList.append(mdl);
	return 1