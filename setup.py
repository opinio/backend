import webapp2
import json
import urllib2, StringIO, csv
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
import logging
from model import *
from xml.dom.minidom import parseString
#from httplib3
import socket
import xml.etree.cElementTree as etree

import os
import cloudstorage as gcs
import sys, traceback

# Retry can help overcome transient urlfetch or GCS issues, such as timeouts.
my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
# All requests to GCS using the GCS client within current GAE request and
# current thread will use this retry params as default. If a default is not
# set via this mechanism, the library's built-in default will be used.
# Any GCS client function can also be given a more specific retry params
# that overrides the default.
# Note: the built-in default is good enough for most cases. We override
# retry_params here only for demo purposes.
gcs.set_default_retry_params(my_default_retry_params)

BUCKET = '/dafiti'


class addDafiti(webapp2.RequestHandler):
	def get(self):
		catMapping = {
		'alpargatas':'Flats',
		'anabela':'Heels',
		'ankle boot':'Boots',
		'botas':'Boots',
		'peep toe':'Heels',
		'rasteiras':'Sandals',
		'sandalias':'Sandals',
		'sapatilhas':'Flats',
		'scarpins':'Heels'
		}

		colorMapping = {
		'Amarela':'yellow',
		'Amarelo':'yellow',
		'Azul':'blue',
		'Bege':'brown',
		'Branca':'white',
		'Branco':'white',
		'Bronze':'brown',
		'Canela':'brown',
		'Caramelo':'brown',
		'Cinza':'grey',
		'Dourada':'yellow',
		'Dourado':'yellow',
		'Laranja':'yellow',
		'Marrom':'brown',
		'Off-White':'grey',
		'Prata':'grey',
		'Preta':'black',
		'Preto':'black',
		'Rosa':'pink',
		'Roxa':'purple',
		'Roxo':'purple',
		'Verde':'green',
		'Vermelha':'red',
		'Vermelho':'red',
		'White':'white'
		}

		#Real Backend:
		filename = '/dafiti/dafiti.xml'
		#Staging:
		#filename = '/dafiti1/dafiti.xml'

		i=0

		with gcs.open(filename) as xml_file:
			tree = etree.parse(xml_file)
			root = tree.getroot()
			for product in root:
				category = product[8].text
				categories = category.split(' / ')
				if 'calcados' in categories and 'feminino' in categories and 'baby' not in categories and 'kids' not in categories and 'teens' not in categories and 'tenis' not in categories:
					description = product[0].text
					details = product[1].text
					prevPrice = product[2].text
					price = product[3].text
					pId = product[4].text
					brand = product[5].text
					url = product[6].text.replace('<![CDATA[','').replace(']]>','')
					img = product[7].text
					category = categories[1]
					payments = product[8].text
					color = description.split(' ')[-1]
				
					if category in catMapping and color in colorMapping:
						dataLoad = {
							'details':details,
							'prevPrice':prevPrice.replace(",","."),
							'price':price.replace(",","."),
							'brand':brand,
							'pId':pId,
							'url':url,
							'img':img,
							'sCat':catMapping[category],
							'color':colorMapping[color],
							'mcatName':category,
							'mColor':color
						}
						taskqueue.add(queue_name="addShoes", url="/admin/addDafiti", params=dataLoad,target=taskqueue.DEFAULT_APP_VERSION)
						i = i+1

			if i>0:
				self.response.write(i)

			xml_file.close()
		
	def post(self):
		getShoes = shoes2.query()
		getShoes = getShoes.filter(shoes2.source=="Dafiti")
		getShoes = getShoes.filter(shoes2.pId==self.request.get('pId'))
		results = getShoes.iter(limit=1,keys_only=True)
		if not results.has_next():
			addNewShoe = shoes2()
			addNewShoe.source = "Dafiti"
			addNewShoe.name = unicode(self.request.get('brand'))
			addNewShoe.url = self.request.get('url')
			addNewShoe.img = self.request.get('img')
			addNewShoe.description = self.request.get('details')
			addNewShoe.price = float(self.request.get('price'))
			addNewShoe.currency = "BRL"
			addNewShoe.sCat = [self.request.get('sCat')]
			addNewShoe.mcatName = self.request.get('mcatName')
			addNewShoe.color = self.request.get('color') 
			addNewShoe.sex = False
			addNewShoe.srank = 0
			addNewShoe.rating = 0
			addNewShoe.pId = self.request.get('pId')
			addNewShoe.prevPrice = float(self.request.get('prevPrice'))
			addNewShoe.likes = 0
			addNewShoe.dislikes = 0
			addNewShoe.catId = 0
			addNewShoe.sku = ""
			addNewShoe.inStock = True
			addNewShoe.sizes = [""]
			addNewShoe.mColor = self.request.get('mColor')
			addNewShoe.country = "Brazil"
			addNewShoe.catName = "Women shoes"
		
			if addNewShoe.price<=100:
				addNewShoe.priceCat = 1
			elif addNewShoe.price<=200:
				addNewShoe.priceCat = 2
			else:
				addNewShoe.priceCat = 3

			addNewShoe.put()
		else: #this is where the price update code goes!
			pass
				
		#except Exception,e:
		#	logging.error(str(e))

class fix(webapp2.RequestHandler):
	def get(self):
		cursor = self.request.get('cursor')
		skip = 2500
		if cursor == "":
			cursor = None
			i = 0
		else:
			cursor = ndb.Cursor.from_websafe_string(cursor)
			i = int(self.request.get('i'))

		getShoes = shoes2.query()
		
		if cursor:
			getShoes = getShoes.iter(produce_cursors=True,limit=skip,start_cursor=cursor)
		else:
			getShoes = getShoes.iter(limit=skip,produce_cursors=True)
		for shoe in getShoes:
			if not shoe.priceCat:
				taskqueue.add(queue_name="addShoes", url="/admin/fix", params={'key':str(shoe.key.urlsafe())},target=taskqueue.DEFAULT_APP_VERSION)
		cursor = getShoes.cursor_after().to_websafe_string()
		i = i+skip
		self.redirect('/admin/fix?cursor='+cursor+'&i='+str(i))
			#break

	def post(self):
		key = self.request.get('key')
		shoe = ndb.Key(urlsafe=key).get()
		if shoe.currency=="GBP":
			if shoe.price<=60:
				shoe.priceCat = 1
			elif shoe.price<=150:
				shoe.priceCat = 2
			else:
				shoe.priceCat = 3
		
		elif shoe.currency=="BRL":
			if shoe.price<=100:
				shoe.priceCat = 1
			elif shoe.price<=200:
				shoe.priceCat = 2
			else:
				shoe.priceCat = 3

		shoe.put()

	#	shoe.pId = str(shoe.pId)

		#if type(shoe.sCat).__name__ != "list":
		#	shoe.sCat = [str(shoe.sCat)]
		#	if shoe.mcatName == "FOOTWEAR_High-heeled sandals_D":
		#		shoe.sCat.append("Sandals")
	#
	#		#Process Title
	#		shoe.name = unicode(shoe.name.split(" - ")[0].title())
	#		shoe.name = unicode(shoe.name.replace(u" on shoescribe.com",u""))
	#		shoe.name = unicode(shoe.name.replace("Boots Boots",""))
	#		shoe.name = unicode(shoe.name.replace("Ankle Boots",""))
	#
	#		#Add Likes/Dislikes
	#		shoe.likes = 0
	#		shoe.dislikes = 0
	#		shoe.srank = 0
	#
	#		#Change shoe rating to float
	#		shoe.rating = float(shoe.rating)
	#
	#		#Save
	#		shoe.put()

class addDafiti2(webapp2.RequestHandler):
	def get(self):
		#url = "http://www.integracaoafiliados.com.br/xml/dafiti/?tipo=geral&id_afiliado=stylect"
		#h = httplib3.Http()
		#resp, content = h.request(url, "GET")
		#self.response.write(resp)
		
		#url = ""
		#result = urlfetch.fetch(url,deadline=999).content
		#response = parseString(result)
		#self.response.write(result)

		#shoeData = open('data/dafiti_test.xml','rb')
		#shoeData = shoeData.read()
		#self.response.write(shoeData)
		#output = StringIO.StringIO(shoeData)

		#response = parseString(shoeData)

		#print response.documentElement

		#shoeData = StringIO.StringIO(shoeData)

		with open('data/dafiti.xml','rb') as xml_file:
			tree = etree.parse(xml_file)
			root = tree.getroot()
			i = 0
			k = 0
			
			for product in root:
				i = i+1
				category = product[8].text
				categories = category.split(' / ')
				if 'calcados' in categories and 'feminino' in categories and 'baby' not in categories and 'kids' not in categories and 'teens' not in categories and 'tenis' not in categories:
					k = k+1
					description = product[0].text
					details = product[1].text
					prevPrice = product[2].text
					price = product[3].text
					pId = product[4].text
					brand = product[5].text
					url = product[6].text.replace('<![CDATA[','').replace(']]>','')
					img = product[7].text
					category = categories[1]
					payments = product[8].text
					color = description.split(' ')[-1]

					if category in catMapping:
						addNewShoe = shoes2()
						addNewShoe.source = "Dafiti"
						addNewShoe.name = description
						addNewShoe.url = url
						addNewShoe.img = img
						addNewShoe.description = details
						addNewShoe.price = float(price)
						addNewShoe.currency = "BRL"
						addNewShoe.sCat = catMapping[category]
						#addNewShoe.color = 
						addNewShoe.sex = 0
						addNewShoe.srank = 0
						addNewShoe.rating = 0
						addNewShoe.brand = brand
						addNewShoe.pId = pId
						addNewShoe.prevPrice = float(prevPrice)

					self.response.write(color+'\n')
					#self.response.write("<br /><br />")
		self.response.write("total: "+str(i))
		self.response.write("<br />shoes: "+str(k))
			#for a in root.iter('categ'):
			#	print a.text
	def post(self):
		pass


class addShoeTask(webapp2.RequestHandler):
	def get(self):
		taskqueue.add(queue_name="addShoes", url="/admin/addShoeTask", target='addshoe')

	def post(self):
#		url = "http://pf.tradedoubler.com/export/export?myFeed=13814257482332345&myFormat=13814257482332345"
#		url = "http://pf.tradedoubler.com/export/export?myFeed=13814286512332345&myFormat=13814286512332345";
		#url = "http://pf.tradedoubler.com/export/export?myFeed=13816649672332345&myFormat=13814286512332345"
	  	#result = urllib2.urlopen(url).read()
		#output = StringIO.StringIO(result)
		

		k=0
	
		shoeData = open('data/dataTest.csv','rb')
		shoeData = shoeData.read()
		shoeData = StringIO.StringIO(shoeData)

		cr = csv.reader(shoeData)

		for row in cr:
			rowStr = ' '.join(row)
			taskqueue.add(queue_name="addShoes", url="/admin/addShoe", params={'line':rowStr},target=taskqueue.DEFAULT_APP_VERSION)


class addShoe(webapp2.RequestHandler):
	def post(self):
		catMapping = {
			'Boots_Ankle boots_D':'Boots',
			'Boots_Boots_D':'Boots',
			'Espadrilles_Espadrilles_D':'NA',
			'Extras_Shoecare_D':'NA',
			'FOOTWEAR_Ankle boots_D':'Boots',
			'FOOTWEAR_Ankle boots_U':'Boots',
			'FOOTWEAR_Ballet flats_D':'Flats',
			'FOOTWEAR_Boots_D':'Boots',
			'FOOTWEAR_Boots_U':'NA',
			'FOOTWEAR_Clog sandals_D':'NA',
			'FOOTWEAR_Closed-toe slip-ons _D':'Heels',
			'FOOTWEAR_Combat boots_D':'NA',
			'FOOTWEAR_Combat boots_U':'Boots',
			'FOOTWEAR_Flip flops_D':'NA',
			'FOOTWEAR_Flip flops_U':'NA',
			'FOOTWEAR_High-heeled boots_D':'Boots',
			'FOOTWEAR_High-heeled sandals_D':'Heels',
			'FOOTWEAR_High-top dress shoes_U':'NA',
			'FOOTWEAR_Moccasins with heel_D':'Heels',
			'FOOTWEAR_Mules_D':'Boots',
			'FOOTWEAR_Peep-toe ballet flats_D':'NA',
			'FOOTWEAR_Platform sandals_D':'Heels',
			'FOOTWEAR_Sandals_D':'Sandals',
			'FOOTWEAR_Sandals_U':'NA',
			'FOOTWEAR_Shoe boots_D':'Boots',
			'FOOTWEAR_Slingbacks_D':'Heels',
			'FOOTWEAR_Slippers_D':'NA',
			'FOOTWEAR_Slippers_U':'NA',
			'FOOTWEAR_Wedges_D':'Heels'
		}

		colorMapping = {
			'red':'red',
			'black':'black',
			'brown':'brown',
			'green':'green',
			'grey':'grey',
			'orange':'orange',
			'purple':'purple',
			'yellow':'yellow',
			'blue':'blue',
			'pink':'pink',
			'white':'white',
			'azure':'blue',
			'beige':'brown',
			'bronze':'brown',
			'camel':'brown',
			'cocoa':'brown',
			'copper':'brown',
			'fuchsia':'purple',
			'garnet':'red',
			'gold':'yellow',
			'ivory':'white',
			'jade':'green',
			'khaki':'brown',
			'lead':'grey',
			'lilac':'purple',
			'maroon':'red',
			'mauve':'purple',
			'ochre':'brown',
			'platinum':'grey',
			'rust':'rust',
			'sand':'brown',
			'silver':'grey',
			'skin':'brown',
			'tan':'brown',
			'turquoise':'blue'
		}

		rowStr = self.request.get('line')
		colArray = rowStr.split("|")
		colArray = [v.replace('"','') for v in colArray]
		
		addNewShoe = shoes2()
		if colArray[30]=="YOOX_direct UK":
			addNewShoe.source="YOOX"
		else:
			addNewShoe.source = "ShoeScribe"

		addNewShoe.name = colArray[0]
		addNewShoe.url = colArray[1]
		addNewShoe.description = colArray[3]
		addNewShoe.price = float(colArray[4])
		addNewShoe.currency = colArray[5]
		addNewShoe.pId = int(colArray[6])
		addNewShoe.catId = int(colArray[7])
		addNewShoe.catName = colArray[8]
		addNewShoe.mcatName = colArray[9]
		addNewShoe.sku = colArray[10]
		addNewShoe.img = colArray[2].replace("_11_","_14_")
		addNewShoe.rating = 0
		addNewShoe.srank = 0

		if addNewShoe.mcatName in catMapping:
			addNewShoe.sCat = catMapping[addNewShoe.mcatName]
		else:
			pass

		try:
			addNewShoe.prevPrice = float(colArray[13])
		except:
			addNewShoe.prevPrice = addNewShoe.price

		shoeSizes = colArray[20].split(" ")
		addNewShoe.sizes = [v.replace('.0','') for v in shoeSizes]
		addNewShoe.inStock = True #this becomes an if/else statement
		
		fieldData = colArray[34].replace('"','').split(";")
		for field in fieldData:
			field = field.split(":")
			if field[0]=="color" or field[0]=="colori":
				addNewShoe.mColor = field[1]
				color = field[1].split(" ")
				for c in color:
					if c.lower() in colorMapping:
						addNewShoe.color = colorMapping[c.lower()]
						break
			if field[0]=="largeimage":
				addNewShoe.img = "http:"+field[2]
			if field[0]=="sex":
				if field[1]=="MEN":
					addNewShoe.sex = True
				else:
					addNewShoe.sex = False

		addNewShoe.put()

class setTask(webapp2.RequestHandler):
	def post(self):
		taskqueue.add(url='/admin/new/feed/shoeScribe')

class updateCat(webapp2.RequestHandler):
	def get(self):
		taskqueue.add(url="/admin/update/cat")
	def post(self):
		getShoes = shoes2.query()
		results = getShoes.fetch()
		i = 0
		for result in results:
			i = i+1
			key = result.key.urlsafe()
			taskqueue.add(url="/admin/update/cat/task", params={'counter':i,'key':key})

class updateCatTask(webapp2.RequestHandler):
	def post(self):
		counter = self.request.get('counter')
		key = self.request.get('key')
		entity = ndb.Key(urlsafe=key).get()

		#DELETE IT!
		ndb.Key(urlsafe=key).delete()
		#mapping = {
		#	'Boots_Ankle boots_D':'Boots',
		#	'Boots_Boots_D':'Boots',
		#	'Espadrilles_Espadrilles_D':'NA',
		#	'Extras_Shoecare_D':'NA',
		#	'FOOTWEAR_Ankle boots_D':'Boots',
		#	'FOOTWEAR_Ankle boots_U':'Boots',
		#	'FOOTWEAR_Ballet flats_D':'Flats',
		#	'FOOTWEAR_Boots_D':'Boots',
		#	'FOOTWEAR_Boots_U':'NA',
		#	'FOOTWEAR_Clog sandals_D':'NA',
		#	'FOOTWEAR_Closed-toe slip-ons _D':'Heels',
		#	'FOOTWEAR_Combat boots_D':'NA',
		#	'FOOTWEAR_Combat boots_U':'Boots',
		#	'FOOTWEAR_Flip flops_D':'NA',
		#	'FOOTWEAR_Flip flops_U':'NA',
		#	'FOOTWEAR_High-heeled boots_D':'Boots',
		#	'FOOTWEAR_High-heeled sandals_D':'Heels',
		#	'FOOTWEAR_High-top dress shoes_U':'NA',
		#	'FOOTWEAR_Moccasins with heel_D':'Heels',
		#	'FOOTWEAR_Mules_D':'Boots',
		#	'FOOTWEAR_Peep-toe ballet flats_D':'NA',
		#	'FOOTWEAR_Platform sandals_D':'Heels',
		#	'FOOTWEAR_Sandals_D':'Sandals',
		#	'FOOTWEAR_Sandals_U':'NA',
		#	'FOOTWEAR_Shoe boots_D':'Boots',
		#	'FOOTWEAR_Slingbacks_D':'Heels',
		#	'FOOTWEAR_Slippers_D':'NA',
		#	'FOOTWEAR_Slippers_U':'NA',
		#	'FOOTWEAR_Wedges_D':'Heels'
		#}
		#logging.info(entity.sCat)
		#if(entity.sCat):
		#	pass
		#else:
		#	if entity.mcatName in mapping:
		#		entity.sCat = mapping[entity.mcatName]
				#entity.put()
		#	else:
		#		pass

class updatetopShoes(webapp2.RequestHandler):
	def get(self):
		keyShoes = open('data/keyShoes.csv','rU')
		keyShoes = keyShoes.read()
		keyShoes = StringIO.StringIO(keyShoes)

		cr = csv.reader(keyShoes, dialect=csv.excel_tab)

		heels = []
		boots = []
		flats = []
		sandals = []

		for row in cr:
			line = row[0].split(',')
			heels.append(line[0])
			boots.append(line[1])
			flats.append(line[2])
			sandals.append(line[3])

			taskqueue.add(queue_name="default", url="/admin/update/topShoes", params={'pId':line[0]})
			taskqueue.add(queue_name="default", url="/admin/update/topShoes", params={'pId':line[1]})
			taskqueue.add(queue_name="default", url="/admin/update/topShoes", params={'pId':line[2]})
			taskqueue.add(queue_name="default", url="/admin/update/topShoes", params={'pId':line[3]})
	def post(self):
		pId = self.request.get('pId')
		getShoe = shoes2.query()
		getShoe = getShoe.filter(shoes2.pId==pId)

		results = getShoe.iter(limit=1)
		if(results):
			result = results.next()
			logging.log('found!'+pId)
		else:
			logging.log('none found'+pId)

class deleteAll(webapp2.RequestHandler):
	def post(self):
		getShoes = shoes2.query()
		results = getShoes.fetch()
		for shoe in results:
			shoe.key.delete()

		getResponses = responses.query()
		results = getResponses.fetch()
		for response in results:
			response.key.delete()

		getUsers = userData.query()
		results = getUsers.fetch()
		for user in results:
			user.key.delete()
