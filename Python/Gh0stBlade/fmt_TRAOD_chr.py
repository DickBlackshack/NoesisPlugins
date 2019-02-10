#Tomb Raider: The Angel of Darkness [PC] - ".chr" Loader
#By Gh0stblade
#v1.0
#Special thanks: Chrrox
#Options: These are bools that enable/disable certain features! They are global and affect ALL platforms!
#Var								Effect
#Misc
#Mesh Global
bOptimizeMesh = False				#Enable optimization (remove duplicate vertices, optimize lists for drawing) (True = on, False = off)
bMaterialsEnabled = True			#Materials (True = on, False = off)
#Render
bRenderAsPoints = False				#Render mesh as points without triangles drawn (True = on, False = off)
#Vertex Components
bNORMsEnabled = True				#Normals (True = on, False = off)
bUVsEnabled = True					#UVs (True = on, False = off)
bCOLsEnabled = True					#Vertex colours (True = on, False = off)
bSkinningEnabled = True				#Enable skin weights (True = on, False = off)
#Gh0stBlade ONLY
bDebug = True						#Prints debug info (True = on, False = off)
bDebugNormals = False and bDebug	#Debug normals (True = on, False = off)
bForceLoadModel = bDebug			#Force Load Model regardless of errors (True = on, False = off)

from inc_noesis import *
import math
	
def registerNoesisTypes():
	handle = noesis.register("Tomb Raider: The Angel of Darkness [PC]", ".chr")
	noesis.setHandlerTypeCheck(handle, chrCheckType)
	noesis.setHandlerLoadModel(handle, chrLoadModel)
	
	if bDebug:
		noesis.logPopup()
	return 1

def chrCheckType(data):
	bs = NoeBitStream(data)
	
	fileIdentifier = bs.readUInt()
	if fileIdentifier == 0x0:
		return 1
	else: 
		print("Fatal Error: Unknown file identifier: " + str(hex(fileIdentifier) + " expected '0x0'!"))
		return 0

class chrFile(object): 
	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.boneList = []
		self.meshInfo = []
		self.numMesh = 0
		self.texList = []
		self.matList = []
		
	def loadchrFile(self):
		bs = self.inFile
		
		fileIdentifier = bs.readUInt()
		matOffset = bs.readUInt()
		boneOffset = bs.readUInt()
		boneOffset2 = bs.readUInt()
		meshOffset = bs.readUInt()
		numBones = bs.readUInt()
		numBones2 = bs.readUInt()
		numMeshes = bs.readUInt()
		unk00 = bs.readUInt()
		unk01 = bs.readUInt()
		unk02 = bs.readUInt()
		unk03 = bs.readUInt()
		
		bs.seek(boneOffset, NOESEEK_ABS)
		for i in range(numBones):
			boneFlags = bs.readUInt()
			boneName = bs.readBytes(64)
			boneHashedName = bs.readUInt()
			boneUnk00 = bs.readUInt()
			boneUnk01 = bs.readUInt()
			boneMtx1 = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()
			boneMtx2 = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()
			bs.seek(80, NOESEEK_REL)
			boneMtx3 = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()
			bs.seek(96, NOESEEK_REL)#Hash of parent name at 0x4?
			#self.boneList.append(NoeBone(i, "bone%03i"%i, boneMtx2, None, i-1))
			print("BoneEnd: " + str(bs.getOffset()))
			if bDebug:
				print("Bone Name: " + str(boneName) + " Flags: " + str(boneFlags))
				
		bs.seek(boneOffset2, NOESEEK_ABS)
		for i in range(numBones2):
			boneFlags = bs.readUInt()
			boneName = bs.readBytes(64)
			boneHashedName = bs.readUInt()
			boneUnk00 = bs.readUInt()
			boneUnk01 = bs.readUInt()
			boneMtx1 = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()
			boneMtx2 = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()
			bs.seek(80, NOESEEK_REL)
			boneMtx3 = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()
			bs.seek(96, NOESEEK_REL)#Hash of parent name at 0x4?
			self.boneList.append(NoeBone(i, "bone%03i"%i, boneMtx1, None, i+1))
			#if bDebug:
			#	print("Bone Name: " + str(boneName) + " Flags: " + str(boneFlags))
				
		bs.seek(meshOffset, NOESEEK_ABS)
		
		for i in range(numMeshes):
			meshLength = bs.readUInt()
			meshUnk00 = bs.readUInt()
			meshHash = bs.readUInt()
			meshNumVerts = bs.readUInt()
			vertBuff = bs.readBytes(meshNumVerts*0x26)
			meshNumFaces = bs.readUInt()
			faceStartOffset = bs.getOffset()
			bs.seek(meshNumFaces*0x2, NOESEEK_REL)
			meshNumFaceGroups = bs.readUInt()
			for j in range(meshNumFaceGroups):
				numFaces = bs.readUShort()
				numFaces2 = bs.readUShort()
				faceStart = bs.readUShort()
				matID = bs.readUShort()
				unk00 = bs.readUShort()
				unk01 = bs.readUShort()
				faceGroupEnd = bs.getOffset()
				rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_SHORT, 0x26, 0)
				rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_SHORT, 0x26, 12)
				rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_SHORT, 0x26, 34)
				bs.seek(faceStartOffset+(faceStart*0x2), NOESEEK_ABS)
				faceBuff = bs.readBytes(numFaces*0x2)
				
				rapi.rpgSetName("Mesh_" + str(i) + "Group_" + str(j))
				if bRenderAsPoints:
					rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, meshNumVerts, noesis.RPGEO_POINTS, 0x1)
				else:
					rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, numFaces, noesis.RPGEO_TRIANGLE_STRIP, 0x1)
				if bOptimizeMesh:
					rapi.rpgOptimize()
				rapi.rpgClearBufferBinds()
			
	def buildMesh(self):
		bs = self.inFile
		
		return 1
		
def chrLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	mesh = chrFile(data)
	mesh.loadchrFile()
	#mesh.buildMesh()
	try:
		mdl = rapi.rpgConstructModelSlim()
	except:
		mdl = NoeModel()
	mdl.setBones(mesh.boneList)
	#mdl.setModelMaterials(NoeModelMaterials(mesh.texList, mesh.matList))
	mdlList.append(mdl);
	return 1