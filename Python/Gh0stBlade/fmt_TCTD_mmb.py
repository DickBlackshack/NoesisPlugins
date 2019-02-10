#Tom Clancy's The Division [PC] - ".mmb" Loader
#By Gh0stblade
#v1.4
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
UVScale = 6.0						#UV Scale
#TCTD Only	
bExtractSpecificLod = True			#Load specific lod level only (True = on, False = off)
lodToExtract = 0					#Force load specific lod level (0 = High, 1 = Mid, 2 = Normal, 3 = Low)
#Gh0stBlade ONLY
bDebug = True						#Prints debug info (True = on, False = off)
bDebugNormals = False and bDebug		#Debug normals (True = on, False = off)
bForceLoadModel = bDebug			#Force Load Model regardless of errors (True = on, False = off)

from inc_noesis import *
import math
	
def registerNoesisTypes():
	handle = noesis.register("Tom Clancy's The Division [PC]", ".mmb")
	noesis.setHandlerTypeCheck(handle, mmbCheckType)
	noesis.setHandlerLoadModel(handle, mmbLoadModel)
	
	if bDebug:
		noesis.logPopup()
	return 1

def mmbCheckType(data):
	bs = NoeBitStream(data)
	
	fileIdentifier = bs.readBytes(3).decode("ASCII").rstrip("\0")
	fileType = bs.readUByte()
	if fileIdentifier == "MMB":
		if fileType == 9 or fileType == 10 or fileType == 11:
			return 1
		else:
			print("Fatal Error: Unsupported file type: " + str(hex(fileType) + " expected 9 (0x9), 10 (0xA) or 11(0xB)!"))
	else: 
		print("Fatal Error: Unknown file identifier: " + str(hex(fileIdentifier) + " expected 'MMB'!"))
		return 0
		
#Returns size of a specific data type
def getDataTypeSize(dataType):
	if dataType == 5:#?
		return 2
	elif dataType == 6:#FLOAT
		return 4
	elif dataType == 8:#?
		return 4
	elif dataType == 11:#SHORT
		return 2
	elif dataType == 14:#UBYTE
		return 1
	elif dataType == 15:#BYTE
		return 1
	elif dataType == 19:#USHORT
		return 2
	else:
		print("[getDataTypeSize] - Unknown data type: " + str(dataType))
		return 0
		
#Returns Noesis compatible data types
def getComponentType(dataType):
	if dataType == 5:#?
		return noesis.RPGEODATA_HALFFLOAT
	elif dataType == 6:#FLOAT
		return noesis.RPGEODATA_FLOAT
	elif dataType == 8:#?
		return noesis.RPGEODATA_FLOAT
	elif dataType == 11:#SHORT
		return noesis.RPGEODATA_SHORT
	elif dataType == 14:#UBYTE
		return noesis.RPGEODATA_UBYTE
	elif dataType == 15:#BYTE
		return noesis.RPGEODATA_BYTE
	elif dataType == 19:#USHORT
		return noesis.RPGEODATA_USHORT
	else:
		print("[getComponentType] - Unknown data type: " + str(dataType))
		return 0

#Returns Noesis compatible facebuff data type
def getFaceDataType(dataType):
	if dataType == 0:
		return noesis.RPGEODATA_USHORT
	elif dataType == 1:
		return noesis.RPGEODATA_UINT
	else:
		print("[getFaceDataType] - Unknown data type: " + str(dataType))
		
#Returns number of components for specific component types
def getComponentCount(componentType):
	if componentType == 0:#Position
		return 3
	elif componentType == 2:#Skin indices
		return 4
	elif componentType == 3:#Skin Weights
		return 4
	elif componentType == 4:#Normals
		return 4
	elif componentType == 5:#Tangents?
		return 4
	elif componentType == 7:#UVs
		return 2
	elif componentType == 8:#RGBA?
		return 4
	else:
		print("[getComponentCount] - Unknown component type: " + str(componentType))
		return 0

#Returns overall vertex component size
def getComponentSize(dataType, componentType):
	return (getDataTypeSize(dataType) * getComponentCount(componentType))
	
#Returns lod name from ID
def getLodName(level):
	lodNames = ['HIGH', 'MID', 'NORMAL', 'LOW']
	return lodNames[level]

class mmbFile(object): 
	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.boneList = []
		self.meshInfo = []
		self.numMesh = 0
		self.texList = []
		self.matList = []
		
	def loadmmbFile(self):
		bs = self.inFile
		
		fileIdentifier = bs.readBytes(3).decode("ASCII").rstrip("\0")
		fileType = bs.readUByte()
		fileSize = bs.readUInt()
		numBones = bs.readUInt()
		
		if bDebug:
			print("[MMB Info] - Type: " + str(fileType) + " Size: " + str(fileSize) + " Bones: " + str(numBones))
		
		if numBones > 0:
			for i in range(numBones):
				boneName = bs.readBytes(bs.readUShort()).decode("ASCII").rstrip("\0")
				boneMat = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()
				boneParentID = bs.readShort()
				if bDebug:
					print("Bone Name: " + str(boneName) + " ID: " + str(i) + " Parent: " + str(boneParentID))
				self.boneList.append(NoeBone(i, boneName, boneMat, None, boneParentID))
			self.boneList = rapi.multiplyBones(self.boneList)
		
		if bDebug:
			print("Offset Bone End: " + str(bs.getOffset()))
			
		self.numMesh = bs.readUInt()
		for i in range(self.numMesh):
			meshGroupInfo = []
			meshFVFInfo = []
			
			if bDebug:
				print("Mesh Start: " + str(bs.getOffset()))
			
			meshName = bs.readBytes(bs.readUShort()).decode("ASCII").rstrip("\0")
			bs.seek(0x30, NOESEEK_REL)
			
			if fileType == 9:
				meshUnk00 = bs.readUByte()
			elif fileType == 10 or fileType == 11:
				meshUnk00 = bs.readUShort()
				
			meshVertComponentCount = bs.readUShort()
			
			#vertex buffer layout
			for j in range(meshVertComponentCount):
				meshFVFInfo.append([bs.readUShort(), bs.readUByte(), bs.readUByte()])
			
			meshNumUnk00 = bs.readUShort()
			bs.seek(meshNumUnk00 * 66, NOESEEK_REL)
			
			meshNumGroups = bs.readUByte()
			
			if bDebug:
				print("FGroup info offset: " + str(bs.getOffset()))
			
			for j in range(meshNumGroups):
				if fileType == 9 or fileType == 10:
					meshGroupInfo.append(bs.read("9I"))
				elif fileType == 11:
					meshGroupInfo.append(bs.read("10I"))
					
			bs.seek(12, NOESEEK_REL)
			
			meshNumUnk02 = bs.readUByte()
			bs.seek(meshNumUnk02 * 4, NOESEEK_REL)
			
			self.meshInfo.append([meshNumGroups, meshGroupInfo, [bs.readUShort(), bs.readUShort(), bs.readUShort(), bs.readUShort(), bs.readUInt(), bs.readUInt(), bs.readInt()], meshName, meshFVFInfo])
			
	def buildMesh(self):
		bs = self.inFile
		
		global lodToExtract
		if lodToExtract > 3 or lodToExtract < 0:
			lodToExtract = 0
			print("Warning: lod level out of range! Using: 0 (high) instead!")
		
		for i in range(self.numMesh):
			meshInfo = self.meshInfo[i]
			meshGroupInfo = meshInfo[1]
			meshVertInfo = meshInfo[2]
			meshFVFInfo = meshInfo[4]
			
			if bDebug:
				print(meshVertInfo)
			for j in range(meshInfo[0]):
				#If we want to extract specific lods
				if bExtractSpecificLod:
					#If pre-defined lod level is not the current lod level we skip it
					if lodToExtract != j:
						continue
				
				#Set mesh name
				rapi.rpgSetName(meshInfo[3] + "_LOD_" + getLodName(j))
				
				#Create material
				material = NoeMaterial("MAT_" + meshInfo[3], "")
				material.setTexture(meshInfo[3] + "_d.dds")
				self.matList.append(material)
				
				if bMaterialsEnabled != False:
					rapi.rpgSetMaterial("MAT_" + meshInfo[3])
				
				if bDebug:
					print(meshInfo[3] + "_LOD_" + getLodName(j))
					print(meshGroupInfo[j])
					print("Mesh: " + str(i) + " Lod: " + str(j) + " VStride: " + str(meshVertInfo[0]) + " NStride: " + str(meshVertInfo[1]) + " VertCount: " + str(meshGroupInfo[j][1]) + " FCount" + str(meshGroupInfo[j][3]))
				
				bs.seek(meshGroupInfo[j][8], NOESEEK_ABS)
				if bDebug:
					print("VSOffset: " + str(bs.getOffset()))
				vertBuff = bs.readBytes(meshGroupInfo[j][1] * meshVertInfo[0])
				if bDebug:
					print("VEOffset: " + str(bs.getOffset()))
				
				bs.seek(meshGroupInfo[j][8] + (meshGroupInfo[j][6] - meshGroupInfo[j][5]), NOESEEK_ABS)
				if bDebug:
					print("NSOffset: " + str(bs.getOffset()))
				vertBuff2 = bs.readBytes(meshGroupInfo[j][1] * meshVertInfo[1])
				if bDebug:
					print("NEOffset: " + str(bs.getOffset()))
				
				bs.seek(meshGroupInfo[j][8] + (meshGroupInfo[j][7] - meshGroupInfo[j][5]), NOESEEK_ABS)
				if bDebug:
					print("FSOffset: " + str(bs.getOffset()))
				
				if meshVertInfo[2] == 1:
					faceBuff = bs.readBytes(meshGroupInfo[j][3] * 0x4)
				else:
					faceBuff = bs.readBytes(meshGroupInfo[j][3] * 0x2)
				
				if bDebug:
					print("FEOffset: " + str(bs.getOffset()))
				
				if bDebug:
					print("FVF: " + str(meshFVFInfo))
				
				#Process vertex component info
				currentBufferPos1 = 0
				currentBufferPos2 = 0
				
				#HACK
				uvData = []
				for fvf in meshFVFInfo:
					#If first buffer
					if not fvf[2] & 0x80:#0x80 is flag for second buffer,0xF is channel idx
						if fvf[1] == 0:#Position
							if bDebug:
								print("XYZW pos: " + str(currentBufferPos1))
							if not fvf[2] & 0xF:
								rapi.rpgBindPositionBufferOfs(vertBuff, getComponentType(fvf[0]), meshVertInfo[0], currentBufferPos1)
								
							currentBufferPos1 += getComponentSize(fvf[0], fvf[1])
							
							#Only shorts are scaled
							if getComponentType(fvf[0]) == noesis.RPGEODATA_SHORT:
								meshScale = float(vertBuff[currentBufferPos1])
								currentBufferPos1 += 2 #+2 = scale
								if bDebug:
									print("Mesh Scale: " + str(meshScale))
								#BUFFER 1
								#Yes... the scale value is stored within the first vertBuffer
								if vertBuff[currentBufferPos1] != 0.0 and meshVertInfo[0] > 6:
									rapi.rpgSetPosScaleBias((meshScale, meshScale, meshScale), (0, 0, 0))
								
						elif fvf[1] == 2:#Bone Weight
							if bDebug:
								print("BW pos: " + str(currentBufferPos1))
							if bSkinningEnabled:
								if not fvf[2] & 0xF:
									rapi.rpgBindBoneWeightBufferOfs(vertBuff, getComponentType(fvf[0]), meshVertInfo[0], currentBufferPos1, 4)
							currentBufferPos1 += getComponentSize(fvf[0], fvf[1])
						elif fvf[1] == 3:#Bone Index
							if bDebug:
								print("BI pos: " + str(currentBufferPos1))
							if bSkinningEnabled:
								if not fvf[2] & 0xF:
									rapi.rpgBindBoneIndexBufferOfs(vertBuff, getComponentType(fvf[0]), meshVertInfo[0], currentBufferPos1, 4)
							currentBufferPos1 += getComponentSize(fvf[0], fvf[1])
						elif fvf[1] == 8:#UNKNOWN!
							if bDebug:
								print("Warning: Unknown component type 8 at: " + str(currentBufferPos1))
							currentBufferPos1 += getComponentSize(fvf[0], fvf[1])
						else:
							print("Unknown vertex component: " + str(fvf[1]) + " pos: " + str(currentBufferPos1))
					#Second buffer
					else:
						if fvf[1] == 4:#Normals
							if bDebug:
								print("Normal pos: " + str(currentBufferPos2))
							
							if bDebugNormals:
								if bCOLsEnabled:
									if not fvf[2] & 0xF:
										rapi.rpgBindColorBufferOfs(vertBuff2, getComponentType(fvf[0]), meshVertInfo[1], currentBufferPos2, 4)
							elif not bDebugNormals:
								if bNORMsEnabled:
									if not fvf[2] & 0xF:
										rapi.rpgBindNormalBufferOfs(vertBuff2, getComponentType(fvf[0]), meshVertInfo[1], currentBufferPos2)
							currentBufferPos2 += getComponentSize(fvf[0], fvf[1])
						elif fvf[1] == 5:#Tangent?
							if bDebug:
								print("Warning: Unknown component type 5 at: " + str(currentBufferPos2))
							currentBufferPos2 += getComponentSize(fvf[0], fvf[1])
							
						elif fvf[1] == 7:#UVs
							if bDebug:
								print("UV pos: " + str(currentBufferPos2))
							if bUVsEnabled:
								if not fvf[2] & 0xF:
									rapi.rpgBindUV1BufferOfs(vertBuff2, getComponentType(fvf[0]), meshVertInfo[1], currentBufferPos2)
									rapi.rpgSetUVScaleBias(NoeVec3 ((UVScale, UVScale, UVScale)), NoeVec3 ((UVScale, UVScale, UVScale)))
								elif fvf[2] & 0xF:#Offset
									placeholer = 1
							currentBufferPos2 += getComponentSize(fvf[0], fvf[1])
						elif fvf[1] == 8:#RGBA?
							if bDebug:
								print("Warning: Unknown component type 8 at: " + str(currentBufferPos2))
							currentBufferPos2 += getComponentSize(fvf[0], fvf[1])
						else:
							print("Fatal Error: vertex component 2: " + str(fvf[1]) + " pos: " + str(currentBufferPos2))
				
				if bDebug and currentBufferPos1 != meshVertInfo[0]:
					print("Warning: Vertex Buffer [1] stride mis-match! Expected: " + str(meshVertInfo[0]) + " got: " + str(currentBufferPos1))
					
				if bDebug and currentBufferPos2 != meshVertInfo[1]:
					print("Warning: Vertex Buffer [2] stride mis-match! Expected: " + str(meshVertInfo[1]) + " got: " + str(currentBufferPos2))
				
				if bRenderAsPoints:
					rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, meshGroupInfo[j][1], noesis.RPGEO_POINTS, 0x1)
				else:
					if bForceLoadModel:
						try:
							rapi.rpgCommitTriangles(faceBuff, getFaceDataType(meshVertInfo[2]), meshGroupInfo[j][3], noesis.RPGEO_TRIANGLE, 0x1)
						except:
							print("Warning: There was an error loading this mesh! Please report this!")
					else:
						rapi.rpgCommitTriangles(faceBuff, getFaceDataType(meshVertInfo[2]), meshGroupInfo[j][3], noesis.RPGEO_TRIANGLE, 0x1)
						
				if bOptimizeMesh:
					rapi.rpgOptimize()
					
				rapi.rpgClearBufferBinds()
		return 0
		
def mmbLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	mesh = mmbFile(data)
	mesh.loadmmbFile()
	mesh.buildMesh()
	try:
		mdl = rapi.rpgConstructModelSlim()
	except:
		mdl = NoeModel()
	mdl.setBones(mesh.boneList)
	mdl.setModelMaterials(NoeModelMaterials(mesh.texList, mesh.matList))
	mdlList.append(mdl);
	return 1