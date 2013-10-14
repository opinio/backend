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

config = {}
config['webapp2_extras.jinja2'] = {
  'template_path':'/',
  'environment_args': {
    'autoescape': True,
    'extensions': [
        'jinja2.ext.autoescape']}
}

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

		i=0
		k=0

		tableRows = []
	
	  	#result = urllib2.urlopen(url).read()
		#output = StringIO.StringIO(result)


		#with open('data/data.csv','rb') as shoeData:
		#	cr = csv.reader(shoeData)
		#shoeData = open('data/data.csv','rb')
		shoeData = open('data/data.csv','rb')
		shoeData = shoeData.read()
		shoeData = StringIO.StringIO(shoeData)

		cr = csv.reader(shoeData)

		for row in cr:
			rowStr = ' '.join(row)
#			tableRows.append(rowStr.split("|")) #Only for the print view.

			colArray = rowStr.split("|")
		#add all the columns here
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
	#	self.render_response('index.html', **template_values)

class setTask(authHandler):
	def get(self):
		self.response.write('<form method="post" action="/admin/new/task"><input type="submit"></form>')
	def post(self):
		taskqueue.add(url='/admin/new/feed/shoeScribe')

class getShoes(authHandler):
	def get(self,sex,product,category):
		from random import randrange

		responseReq = 30
		
			
		getShoes = shoes2.all()
		if sex=="men":
			getShoes.filter('sex =',True)
		else:
			getShoes.filter('sex =',False)
		
		results = getShoes.fetch(100)
		
		i = 0
		obj = []
		while i<responseReq:
			rand = randrange(100)
			url = results[rand].source
			name = results[rand].name
			img = results[rand].img
			obj.append({'url':url,'name':name,'img':img})
			i=i+1
			
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(obj))

		#for test in result:
		#	print test.source


application = webapp2.WSGIApplication([
	('/admin/new/feed/shoeScribe', getShoeScribe),
	('/admin/new/task',setTask),
	('/get/(.*)/(.*)/(.*)',getShoes)],
	debug=True)

def main():
    application.run()

if __name__ == "__main__":
    main()
