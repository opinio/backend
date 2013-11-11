import webapp2
import json
import urllib2, StringIO, csv
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
import logging
from model import *

class addShoeTask(webapp2.RequestHandler):
	def post(self):
#		url = "http://pf.tradedoubler.com/export/export?myFeed=13814257482332345&myFormat=13814257482332345"
#		url = "http://pf.tradedoubler.com/export/export?myFeed=13814286512332345&myFormat=13814286512332345";
		#url = "http://pf.tradedoubler.com/export/export?myFeed=13816649672332345&myFormat=13814286512332345"
	  	#result = urllib2.urlopen(url).read()
		#output = StringIO.StringIO(result)

		k=0
	
		shoeData = open('data/data.csv','rb')
		shoeData = shoeData.read()
		shoeData = StringIO.StringIO(shoeData)

		cr = csv.reader(shoeData)

		for row in cr:
			rowStr = ' '.join(row)
			taskqueue.add(queue_name="addShoes", url="/admin/addShoe", params={'line':rowStr})


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
			if field[0]=="color":
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
		logging.info(counter)
		key = self.request.get('key')
		entity = ndb.Key(urlsafe=key).get()
		mapping = {
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
		#logging.info(entity.sCat)
		if(entity.sCat):
			pass
		else:
			if entity.mcatName in mapping:
				entity.sCat = mapping[entity.mcatName]
				entity.put()
			else:
				pass

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

		getResponses = responses.query()
		results = getResponses.fetch()
		for response in results:
			response.key.delete()

		getUsers = userData.query()
		results = getUsers.fetch()
		for user in results:
			user.key.delete()
