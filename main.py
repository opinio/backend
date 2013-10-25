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
			obj.append({'url':url,'name':name,'img':img})
			i=i+1
		
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(obj))

class getCat(authHandler):
	def get(self):
		categories = ['Sandals','Heels','Flats','Boots','Sneakers']
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(categories))

class pushAction(authHandler):
	def get(self,act):
		tuser = self.request.get('tuser')
		fuser = self.request.get('fuser')
		test = '{"action": {"uuid": "hadi","type": "like","pId": "productId"}}'
		status = {'status':'OK'}
		self.response.out.write(json.dumps(status))

class newUser(authHandler):
	def get(self):
		uuid = self.request.get('uuid')
		status = {}

		if(uuid!=""):
			newUser = userData()
			newUser.uuId = uuid
			newUser.lastUpdate = datetime.datetime.now()

			#check if newUser already exists
			q = userData.query(userData.uuId==uuid)
			results = q.fetch(1)
			if len(results)>0:
				status = {'status':'Failed','Reason':'UUID already Exists'}
			else:
				try:
					newUser.put()
					status = {'status':'OK'}
				except:
					status = {'status':'Failed','Reason':'Unknown'}
		else:
			status = {'status':'Failed','reason':'No uuid provided'}

		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(status))


application = webapp2.WSGIApplication([
	('/admin/new/feed/shoeScribe', getShoeScribe),
	('/admin/new/task',setTask),
	('/get/(.*)/(.*)/(.*)',getShoes),
	('/get/catList',getCat),
	('/push/(.*)/',pushAction),
	('/users/new',newUser)],
	debug=True)

def main():
    application.run()

if __name__ == "__main__":
    main()
