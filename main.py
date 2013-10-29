#!/usr/bin/python
#hello

import os
import webapp2
import jinja2
import urllib2, StringIO, csv
from model import *
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
import logging
import json
import datetime

config = {}
config['webapp2_extras.jinja2'] = {
  'template_path':'/',
  'environment_args': {
    'autoescape': True,
    'extensions': [
        'jinja2.ext.autoescape']}
}


#This could be used to make urllib2 work with urlfetch with timeout limits in the future
#old_fetch = urlfetch.fetch
#def new_fetch(url, payload=None, method="GET", headers={},allow_truncated=False, follow_redirects=True,deadline=60.0, *args, **kwargs):
#	return old_fetch(url, payload, method, headers, allow_truncated,follow_redirects, deadline, *args, **kwargs)
#urlfetch.fetch = new_fetch

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class authHandler(webapp2.RequestHandler):
	def render_response(self, template_path, **template_values):
		template = jinja_environment.get_template(template_path)
		self.response.write(template.render(**template_values))

	def convert_md5(self, longStr):
		import md5
		m = md5.new()
		m.update(longStr)
		return m.hexdigest()

class getShoeScribe(authHandler):
	def post(self):
#		url = "http://pf.tradedoubler.com/export/export?myFeed=13814257482332345&myFormat=13814257482332345"
#		url = "http://pf.tradedoubler.com/export/export?myFeed=13814286512332345&myFormat=13814286512332345";
		#url = "http://pf.tradedoubler.com/export/export?myFeed=13816649672332345&myFormat=13814286512332345"
	  	#result = urllib2.urlopen(url).read()
		#output = StringIO.StringIO(result)


		i=0
		k=0
		tableRows = []
	
		shoeData = open('data/dataTest.csv','rb')
		shoeData = shoeData.read()
		shoeData = StringIO.StringIO(shoeData)

		cr = csv.reader(shoeData)

		for row in cr:
			rowStr = ' '.join(row)

			colArray = rowStr.split("|")
			
			if i>0:
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

				print colArray[30]
				
				try:
					addNewShoe.prevPrice = float(colArray[13])
				except:
					addNewShoe.prevPrice = addNewShoe.price

				shoeSizes = colArray[20].split(" ")
				addNewShoe.sizes = [v.replace('.0','') for v in shoeSizes]

				addNewShoe.inStock = True #this becomes an if/else statement

				#add field data here		
				fieldData = colArray[34].replace('"','').split(";")

				for field in fieldData:
					field = field.split(":")
					if field[0]=="color":
						addNewShoe.color = field[1]
					if field[0]=="largeimage":
						addNewShoe.img = "http:"+field[2]
					if field[0]=="sex":
						if field[1]=="MEN":
							addNewShoe.sex = True
						else:
							addNewShoe.sex = False

				addNewShoe.put()
			i=i+1
		
#		template_values = {}
#		template_values['tableRows']=tableRows
#		self.render_response('index.html', **template_values)

class setTask(authHandler):
	def get(self):
		self.response.write('<form method="post" action="/admin/new/task"><input type="submit"></form>')
	def post(self):
		taskqueue.add(url='/admin/new/feed/shoeScribe')

class getShoes(authHandler):
	def get(self,sex,product,category):
		from random import randrange

		color = self.request.get('color')
		num = self.request.get('num')
		try:
			responseReq = int(num)
		except:
			responseReq = 10
		

		getShoes = shoes2.query()
		if sex=="m":
			getShoes.filter(shoes2.sex == True)
		if sex=="f":
			getShoes.filter(shoes2.sex == False)
		
		results = getShoes.fetch(100)

		i = 0
		obj = []
		while i<responseReq:
			rand = randrange(50)
			url = results[rand].url
			name = results[rand].name
			img = results[rand].img
			key = str(results[rand].key.urlsafe())
			price = str(results[rand].price)
			source = str(results[rand].source)
			color = str(results[rand].color)

			obj.append({'url':url,'name':name,'img':img, 'key':key, 'price':price,'source':source,'color':color})
			i=i+1
		
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(obj))

class getCat(authHandler):
	def get(self):
		categories = ['Sandals','Heels','Flats','Boots','Sneakers']
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(categories))

class pushAction(authHandler):
	def get(self):

		template_values = {}
		self.render_response('actDemo.html', **template_values)

	def post(self):
		data = self.request.body
		status = {}
		try:
			data = json.loads(data)
			status = {'status':'OK'}
			uuid = data['uuid']
		except:
			status= {'status':'Failed to load data in JSON--check formatting','dataReceived':data}

		for action in data["actions"]:
			actionType = action['type']
			test = taskqueue.add(queue_name="actions", url="/queue/action", params={'uuid':uuid, 'pId':action['pKey'], 'act':actionType})
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(status))

class queueAction(authHandler):
	def post(self):
		uuid = self.request.get('uuid')
		pId = self.request.get('pId')
		actionType = self.request.get('act')
		keyName = uuid+pId

		if(actionType=='delete'):
			updateAct = responses.get_by_id(keyName)
			if updateAct:
				updateAct.act = "delete"
				updateAct.put()
		elif actionType=='like' or actionType=='dislike':
			if responses.get_by_id(keyName): #check if duplicate before storing
				pass
			else:
				newResponse = responses(id=keyName)
				newResponse.uuId = ndb.Key('userData',uuid)
				newResponse.pId = ndb.Key('shoes2',pId)
				newResponse.act = actionType
				newResponse.put()


class newUser(authHandler):
	def post(self):
		data = self.request.body
		status = {}
		
		try:
			data = json.loads(data)
			keyName = self.convert_md5(data['uuid'])

			duplicate = userData.get_by_id(keyName)
			if duplicate:
				try:
					gender = data['gender']
					if gender=="m":
						duplicate.gender = True
					else:
						duplicate.gender = False

					duplicate.fId = int(data['fId'])
					duplicate.name = data['name']
					duplicate.email = data['email']
					duplicate.age = data['age']
					status = {'status':'OK','warning':'UUID already existed, only updated FB Information'}
					duplicate.put()
				except:
					status = {'status':'Failed','reason':'It was a duplicate UUID, but then failed in trying to update duplicate FB stuff'}
					raise
			else:
				newUser = userData(id=keyName)
				newUser.uuId = data['uuid']
				try:
					gender = data['gender']
					if gender=="m":
						newUser.gender = True
					else:
						newUser.gender = False

					newUser.fId = int(data['fId'])
					newUser.name = data['name']
					newUser.email = data['email']
					newUser.age = data['age']
					status = {'status':'OK'}
				except:
					status = {'status':'OK','warning':'No Facebook Information'}
			
				newUser.put()
		except:
			status = {'status':'Failed','Reason':'Had trouble parsing the JSON'}
			raise

		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(status))


	def get(self):
		template_values = {}
		self.render_response('userDemo.html', **template_values)

		#import uuid
		#uID = self.request.get('uuid')
		#status = {}

		#if(uID!=""):
		#	#uID = uuid.UUID(uID).int
		#	newUser = userData(id=uID)
		#	newUser.uuId = uID
		#	newUser.lastUpdate = datetime.datetime.now()

			#check if newUser already exists
		#	q = userData.query(userData.uuId==uID)
		#	results = q.fetch(1)
		#	if len(results)>0:
		#		status = {'status':'Failed','Reason':'UUID already Exists'}
		#	else:
		#		try:
		#			newUser.put()
		#			status = {'status':'OK'}
		#		except:
		#			status = {'status':'Failed','Reason':'Unknown'}
	#	else:
	#		status = {'status':'Failed','reason':'No uuid provided'}
#
#		self.response.headers['Content-Type'] = 'application/json'
#		self.response.out.write(json.dumps(status))


application = webapp2.WSGIApplication([
	('/admin/new/feed/shoeScribe', getShoeScribe),
	('/admin/new/task',setTask),
	('/get/(.*)/(.*)/(.*)',getShoes),
	('/get/catList',getCat),
	('/push/action',pushAction),
	('/queue/action',queueAction),
	('/users/new',newUser)],
	debug=True)

def main():
    application.run()

if __name__ == "__main__":
    main()
