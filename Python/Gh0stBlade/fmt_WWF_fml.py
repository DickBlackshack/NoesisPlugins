#WWF - ".rax" Loader
#By Gh0stblade
#v1.0
#Special thanks: Chrrox
#Options: These are bools that enable/disable certain features! They are global and affect ALL platforms!
#Var							Effect
#Misc
bRenderAsPoints = 0				#Render mesh as points without triangles drawn (1 = on, 0 = off)
#Gh0stBlade ONLY
debug = 0 						#Prints debug info (1 = on, 0 = off)

from inc_noesis import *
import math

def registerNoesisTypes():
	handle = noesis.register("WWF []", ".fml")
	noesis.setHandlerTypeCheck(handle, fmlCheckType)
	noesis.setHandlerLoadModel(handle, fmlLoadModel)
	
	noesis.logPopup()
	return 1

def fmlCheckType(data):
	bs = NoeBitStream(data)
	fileMagic = bs.readUInt()
	if fileMagic == 0xF001FFFF:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(fileMagic) + " expected '0xF001FFFF'!"))
		return 0
		
class fmlFile(object): 
	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.meshNames = []
		self.matNames = []
		self.texNames = []
		self.boneList = []
		self.numBones = -1
		self.boneLevel = 0
		
	def loadfmlFile(self):
		bs = self.inFile
		
		unk00 = bs.readUShort()
		unk01 = bs.readUShort()
		unk02 = bs.readUShort()
		unk03 = bs.readUShort()
		
		unk04 = bs.readUShort()
		numMaterials = bs.readUShort()
		numTextures = bs.readUShort()
		numBones = bs.readUShort()
		
		unk08 = bs.readUShort()
		numMeshNames = bs.readUShort()
		
		#Load Mesh Names
		for i in range (numMeshNames):
			self.meshNames.append(self.getString())
			if debug:
				print("Mesh Name: " + str(self.meshNames[i]))
			
		#Load Material Names
		for i in range (numMaterials):
			matStart = bs.getOffset()
			self.matNames.append(self.getString())
			bs.seek(matStart+0x10, NOESEEK_ABS)
			matType = bs.readUByte()

			if matType&0x40:
				bs.seek(0x2F, NOESEEK_REL)
			else:
				bs.seek(0x2D, NOESEEK_REL)
				
			if debug:
				print("Mat Name: " + str(self.matNames[i]))
		
		#Load Texture Names
		for i in range (numTextures):
			self.texNames.append(self.getString())
			if debug:
				print("Tex Name: " + str(self.texNames[i]))
			
		#Load Bones
		self.loadBones(self.boneLevel, self.numBones) #Default level = 0 Default root = -1
		self.boneList = rapi.multiplyBones(self.boneList)
		
		currentMesh = 0#TEMP
		for i in range(2):
			currentMesh += 1
			meshCount = bs.readUShort()#Unconfirmed
			
			meshFVF = bs.readUByte()
			
			for j in range(meshFVF):
				meshFVFUnk00 = bs.readUShort()#Most likely material mesh uses?
				
			meshVertCount = bs.readUShort()
				
			if meshFVF == 0:
				vertStride = 0x31
			elif meshFVF == 1:
				vertStride = 0x2B
			elif meshFVF == 2:
				vertStride = 0x31
			elif meshFVF == 3:
				vertStride = 0x37
			#else:
			#	print("Fatal Error: Unknown FVF: " + str(meshFVF) + "!")
			vertBuff = bs.readBytes(meshVertCount * vertStride)
			meshFaceCount = bs.readUShort()
			
			faceBuff = bs.readBytes(meshFaceCount * 0x2)
			meshUnk04 = bs.readUShort()#FIXME
			meshUnk04 = bs.readUShort()#FIXME
			
			if meshVertCount > 0 and meshFaceCount > 0:
				rapi.rpgSetName(self.meshNames[i])
				rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x0)
				rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0xC)
				rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, vertStride, 0x1C)
				
				if bRenderAsPoints:
					rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, meshVertCount, noesis.RPGEO_POINTS, 0x1)
				else:
					rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, int(meshFaceCount), noesis.RPGEO_TRIANGLE_STRIP, 0x1)
				rapi.rpgClearBufferBinds()
		
	def getString(self):
		bs = self.inFile
		startOffset = bs.getOffset()
		string = bs.readString()
		bs.seek(startOffset + 0x10, NOESEEK_ABS)
		return string
		
	def loadBones(self, depth, parentID):
		bs = self.inFile
		self.numBones += 1
		boneName = self.getString()
		boneMat = NoeMat43.fromBytes(bs.readBytes(48)).transpose()
		boneUnk00 = bs.readUShort()#Only used on last bone?
		numChildren = bs.readShort()#If root bone this is max depth
		
		self.boneList.append(NoeBone(self.numBones, boneName, boneMat, None, parentID))
		
		if debug:
			print("BN: " + str(boneName) + " BID: " + str(self.numBones) + " PID: " + str(parentID) + " D: " + str(depth) + " NC: " + str(numChildren))
		
		tempParent = self.numBones
		
		if parentID == -1:#Root
			self.loadBones(depth + 1, tempParent)
		else:
			for i in range (numChildren):
				self.loadBones(depth + 1, tempParent)
		
		#HACK Load last bone
		if depth == 0:
			boneName = self.getString()
			boneMat = NoeMat43.fromBytes(bs.readBytes(48)).transpose()
			boneUnk00 = bs.readUShort()#Only used on last bone?
			numChildren = bs.readShort()#If root bone this is max depth
		
		return 1
		
def fmlLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	mesh = fmlFile(data)
	mesh.loadfmlFile()
	try:
		mdl = rapi.rpgConstructModelSlim()
	except:
		mdl = NoeModel()
	mdl.setBones(mesh.boneList)
	mdlList.append(mdl);
	return 1