#!/usr/bin/env python
import struct, random
from uuid import uuid4

try:
	import bson
	from bson.objectid import ObjectId
except :
	raise Exception('Install pymongo')

import json as _json

class JSONEncoder(_json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return 'ObjectId(' + str(o) + ')'
        return _json.JSONEncoder.default(self, o)

class Converter:
	def __init__(self, newObjectId=True):
		self.newObjectId = newObjectId
		self._xml = ''
		self._types = {'INIT':-1, 'DEFINITION':-2, 'END':-3, 'SIZE': -4,
		  'TITLE':-5, 'DOUBLE':0x01, 'STRING':0x02, 'DOCUMENT':0x03,
		  'ARRAY':0x04, 'OBJECTID':0x07, 'BOOLEAN':0x08, 'NULL':0x0A, 
		  'INT32':0x10}
	
	def _add(self, indent, datatype, data='', name=''):
		tab = '\t' * indent
		self._xml += tab
		
		if datatype is self._types['INIT']:
			blockName = 'name="' + name + '"' if name is not '' else ''
			self._xml += '<Block ' + blockName + '> <!-- ' + JSONEncoder().encode(data) + ' -->\n'
		elif datatype is self._types['DEFINITION']:
			self._xml += '<Blob valueType="hex" value="' + str('%.2x' % self._types[data]) + '" /> <!-- ' + data + ' -->\n'
		elif datatype is self._types['END']:
			self._xml += '<Blob valueType="hex" value="00" />\n' + tab[:-1] + '</Block>\n'
		elif datatype is self._types['SIZE']:
			self._xml += '<Number size="32">\n\t' + tab + '<Relation type="size" of="' + data + '" />\n' + tab + '</Number>\n'
		elif datatype is self._types['TITLE']:
			self._xml += '<String value="' + str(data) + '" nullTerminated="true" />\n'
		
		elif datatype is self._types['STRING'] and name is not '':
			self._xml += '<String name="' + name + '" value="' + data + '" nullTerminated="true" />\n'
		elif datatype is self._types['DOUBLE']:
			self._xml += '<Blob valueType="hex" value="' + ''.join('%.2x' % ord(c) for c in struct.pack('<d', data)) + '" />\n'
		elif datatype is self._types['OBJECTID']:
			if self.newObjectId:
				self._xml += ('<Number size="32" >\n\t' + tab + '<Fixup class="SequenceRandomFixup" />\n' + tab +
				 '</Number>\n' + tab + '<Blob valueType="hex" value="00000000" mutable="false"/>\n')
			else:
				self._xml += '<Blob valueType="hex" value="' + str(data) + '" />\n'
			
		elif datatype is self._types['INT32']:
			self._xml += '<Number size="32" value="' + str(data) + '" />\n'
	
	def _addDocument(self, jsonData, indent):
		for key, value in jsonData.iteritems() if type(jsonData) is dict else enumerate(jsonData):
			if type(value) is dict:
				dictName = str(key)+'_'+str(uuid4()).replace('-', '')[:5]
				self._add(indent+1, self._types['DEFINITION'], 'DOCUMENT')
				self._add(indent+1, self._types['TITLE'], key)
				self._add(indent+1, self._types['INIT'], value, dictName)
				self._add(indent+2, self._types['SIZE'], dictName)
				self._addDocument(value, indent+2)
				self._add(indent+2, self._types['END'])
			elif type(value) is list:
				arrayName = str(key)+'_'+str(uuid4()).replace('-', '')[:5]
				self._add(indent+1, self._types['DEFINITION'], 'ARRAY')
				self._add(indent+1, self._types['TITLE'], key)
				self._add(indent+1, self._types['INIT'], value, arrayName)
				self._add(indent+2, self._types['SIZE'], arrayName)
				self._addDocument(value, indent+2)
				self._add(indent+2, self._types['END'])
			elif type(value) is str:
				stringName = str(key)+'_'+str(uuid4()).replace('-', '')[:5]
				self._add(indent+1, self._types['DEFINITION'], 'STRING')
				self._add(indent+1, self._types['TITLE'], key)
				self._add(indent+1, self._types['SIZE'], stringName)
				self._add(indent+1, self._types['STRING'], value, stringName)
			elif type(value) is ObjectId:
				self._add(indent+1, self._types['DEFINITION'], 'OBJECTID')
				self._add(indent+1, self._types['TITLE'], key)
				self._add(indent+1, self._types['OBJECTID'], value)
			elif type(value) is int:
				self._add(indent+1, self._types['DEFINITION'], 'INT32')
				self._add(indent+1, self._types['TITLE'], key)
				self._add(indent+1, self._types['INT32'], abs(value))
			elif type(value) is float:
				self._add(indent+1, self._types['DEFINITION'], 'DOUBLE')
				self._add(indent+1, self._types['TITLE'], key)
				self._add(indent+1, self._types['DOUBLE'], value)
	
	def convert(self, jsonData, indent=0):
		self._add(indent, self._types['INIT'], jsonData)
		
		if type(jsonData) is dict:
			self._addDocument(jsonData, indent)
		else:
			raise Exception('Only dict is valid as an input')
		
		self._add(indent+1, self._types['END'])
		return self._xml

if __name__ == '__main__':
	#jsonData = {'_id': ObjectId('000000000000000000000000'), 'ns': 'test.adm', 'key': {'locs': '2d'}, 'name': 'locs_2d'}
	jsonData = {'_id': ObjectId('000000000000000000000000'), 'locs':[[55.5,42.3],[-74,44.74],{'lng':55.5,'lat':42.3}]}
	print Converter().convert(jsonData)
