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
import setup
import internal

config = {}
config['webapp2_extras.jinja2'] = {
  'template_path':'',
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

class getShoes(authHandler):
	def get(self):
		template_values = {}
		self.render_response('getDemo.html', **template_values)
		
	def post(self):
		from random import randrange
	
		#config
		defaultRequests = 2
		defaultFetch = 500
		status = {}

		data = self.request.body

		#Time to parse the data we got, see if it's legit.
		try:
			data = json.loads(data)
			uuid = data['uuid']
			getUser = userData.get_by_id(self.convert_md5(uuid))
			sex = data['sex']
			cat = data['cat']
			product = ""
			product = data['type'] #irrelevant for now and ignored in the code, but futureproofing stuff
			minPrice = None
			maxPrice = None
			sex = [True,False][sex=="f"]
			try:
				version = data['version']
			except KeyError:
				version = None

			try:
				color = data['color'].lower()
			except KeyError:
				color = None

			#minPrice = data['minPrice']
			#maxPrice = data['maxPrice']
			
			try:
				responseReq = int(data['num'])
			except:
				responseReq = defaultRequests
			#Create a new user if he/she doesn't exist yet
			uuidKeyName = self.convert_md5(data['uuid'])	
			userExists = userData.get_by_id(uuidKeyName)
			if userExists:
				pass
			else:
				newUser = userData(id=uuidKeyName)
				newUser.uuId = data['uuid']
				newUser.put()
			
			#load cursor and cursor name--TODO: OPTIMIZE AND MAKE IT A NEW MODULE
			cursorName = '-'.join([str(sex),str(cat),str(product),str(color),str(minPrice),str(maxPrice),'sortByRating']) 
			queryCursor = None
			try:
				cursorList = getUser.cursors
				cursorList = json.loads(cursorList)
				queryCursor = cursorList[cursorName]
				queryCursor = ndb.Cursor.from_websafe_string(queryCursor)
			except KeyError:
				queryCursor = None
			except:
				cursorList = {}

			#START QUERY
			getShoes = shoes2.query()
			getShoes = getShoes.filter(shoes2.sex==sex)
			getShoes = [getShoes.filter(shoes2.color==color),getShoes][color==None or color=="all"]
			getShoes = [getShoes.filter(shoes2.sCat==cat),getShoes][cat=="all"]
			getShoes = getShoes.order(-shoes2.rating)

			if queryCursor:
				results = getShoes.iter(produce_cursors=True,limit=defaultFetch,start_cursor=queryCursor)
			else:	
				results = getShoes.iter(produce_cursors=True, limit=defaultFetch)
			
			#Makes sure that if the results are less than what we expected to fetch
			#the random number doesn't ask for too many and cause an index error
			#if len(results)<defaultFetch:
			#	defaultFetch=len(results)
		
			i = 0
			obj = []
			selected = []

			while i<responseReq:
				try:
					result = results.next()
					pUrl = result.url
					pName = result.name
					pImg = result.img
					pKey = str(result.key.urlsafe())
					pPrice = result.price
					pPrevPrice = result.prevPrice
					pDiscount = int(((pPrevPrice-pPrice)/pPrevPrice)*100)
					pSource = str(result.source)
					pColor = str(result.color)
					pCat = str(result.sCat)
					newCursor = results.cursor_after().to_websafe_string()
					keyName = self.convert_md5(uuid+pKey)

					showDiscount = [False,True][pDiscount>=50]
					
					if responses.get_by_id(keyName): #if duplicate, skip adding it and don't increase I by one
						continue

					taskqueue.add(queue_name="actions", url="/queue/action", params={'uuid':uuid, 'pKey':pKey, 'act':'sent'})
					obj.append({'url':pUrl,'name':pName,'img':pImg, 'key':pKey, 'price':str(pPrice),'source':pSource,'color':pColor,'category':pCat,'discount':str(pDiscount),'showDiscount':str(showDiscount)})
				except StopIteration:
					#obj = {'status':'failed','error':'ran out of products to show'}
					obj = []
					if queryCursor:
						newCursor = queryCursor.to_websafe_string()
					break
				i = i+1

			
			#logging.info("hello"+str(responseReq)+str(i))
			#update Cursor TODO: make this its own module!!
			try:
				cursorList[cursorName] = newCursor
				try:
					getUser.cursors = json.dumps(cursorList)
					getUser.put()
				except AttributeError:
					newUser.cursors = json.dumps(cursorList)
					newUser.put()
			except:
				pass #this fails when its the first time searching for a color and nothing is found. As a result no cursors should be saved. Basically no responses from the db.

		except:
			status = {'status':'Failed','reason':'unable to parse json'}
			raise
			
		self.response.headers['Content-Type'] = 'application/json'
		if version:
			newStyle = {}
			newStyle['status']="ok"
			newStyle['products'] = obj
			self.response.out.write(json.dumps(newStyle))
		else:
			self.response.write(json.dumps(obj))

class getCat(authHandler):
	def get(self):
		catList = ["Sandals","Heels","Flats","Boots"]
		colorList = {'Red':'#FB0C14','Black':'#000000','Brown':'#9F3C17','Green':'#51CA46','Grey':'#999999','Orange':'#F2732B','Purple':'#9053B4','Yellow':'#FFD236','Blue':'#2657EE','Pink':'#FF75F3','White':'#FFFFFF'}
		priceList = ['Any Price','Under £20','£21-100','£101-200','£201-500','£501+']
		categories = {'categories':catList,'colors':colorList,'prices':priceList}
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(categories))

class pushAction(authHandler): #Manages updates of likes/dislikes
	def get(self):
		template_values = {}
		self.render_response('actDemo.html', **template_values)

	def post(self):
		data = self.request.body
		status = {}
		try:
			data = json.loads(data)
			uuid = data['uuid']
			try:
				dev = data['dev']
				status = {'status':'OK','devMode':'enabled'}
			except:
				dev = False
				status = {'status':'OK'}

			userExists = userData.get_by_id(self.convert_md5(uuid))
			if userExists:
				for action in data["actions"]:
					productExists = ndb.Key(urlsafe=action['pKey']).get()
					if productExists:
						actionType = action['type']
						test = taskqueue.add(queue_name="actions", url="/queue/action", params={'uuid':uuid, 'pKey':action['pKey'], 'act':actionType,'devMode':dev})

					else:
						status = {'status':'failed','reason':'Product does not exist'}
			else:
				status = {'status':'failed','reason':'User does not exist'}
		except:
			status= {'status':'Failed to load data in JSON--check formatting','dataReceived':data}
			raise
		
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(status))

class queueAction(authHandler):
	def post(self):
		devMode = self.request.get('devMode')
		if devMode=="False":
			devMode = False
		else:
			devMode = True
		uuid = self.request.get('uuid')
		pKey = self.request.get('pKey')
		actionType = self.request.get('act')
		keyName = self.convert_md5(uuid+pKey) #the keyName is the md5'ed concatenation of uuid and PKEY at all times!

		if(actionType=='delete'):
			#if the user has asked to delete the like, mark it as a delete.
			updateAct = responses.get_by_id(keyName)
			if updateAct:
				updateAct.act = "delete"
				updateAct.put()
		elif(actionType=="sent"):
			#if we just sent the product to the user, we'll mark it as sent.
			if responses.get_by_id(keyName): #check if duplicate before storing
				pass
			else:
				sentProduct= responses(id=keyName)
				sentProduct.uuId = ndb.Key('userData',self.convert_md5(uuid))
				sentProduct.pId = ndb.Key(urlsafe=pKey)
				sentProduct.act = actionType
				sentProduct.put()
		elif actionType=='like' or actionType=='dislike':
			#if they responded back, we need to load the sent product and then update it to a like or a dislike
			updateAct = responses.get_by_id(keyName) #check if duplicate before storing
			if updateAct:
				updateAct.act = actionType
				updateAct.put()
			else:
				notsentProduct = responses(id=keyName)
				notsentProduct= responses(id=keyName)
				notsentProduct.uuId = ndb.Key('userData',self.convert_md5(uuid))
				notsentProduct.pId = ndb.Key(urlsafe=pKey)
				notsentProduct.act = actionType
				notsentProduct.put()
			
			updatePrd = ndb.Key(urlsafe=pKey).get()

			if updatePrd and not devMode:
				delta = 0
				if actionType=="like":
					delta = 1
				elif actionType=="dislike":
					delta = -1

				if not updatePrd.rating:
					updatePrd.rating = 0

				updatePrd.rating = updatePrd.rating+delta
				updatePrd.put()
			else:
				pass


class pushEmail(authHandler):
	def post(self):
		data = self.request.body

		try:
			data = json.loads(data)
			try:
				uuidKeyName = self.convert_md5(data['uuid'])

				response = responses.query()
				response.filter(responses.uuId==ndb.Key('userData',uuidKeyName))
				response.filter(responses.act=='like')
				results = response.fetch()

				if len(results)>0:
					status = {'status':'OK'}
				else:
					status = {'status':'Failed','reason':'User does not have any likes'}
			except:
				status = {'status':'Failed','reason':'Failed in process of querying datastore'}
		except:
			status = {'status':'Failed','reason':'Could not convert json'}
			raise

		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(status))
		

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
					status = {'status':'OK','warning':'UUID already existed, only updated FB Information','uuid':data['uuid']}
					duplicate.put()
				except:
					status = {'status':'Failed','reason':'It was a duplicate UUID, but then failed in trying to update duplicate FB stuff','uuid':data['uuid']}
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
					status = {'status':'OK','uuid':data['uuid']}
				except:
					status = {'status':'OK','warning':'No Facebook Information','uuid':data['uuid']}
			
				newUser.put()
		except:
			status = {'status':'Failed','Reason':'Had trouble parsing the JSON'}

		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(status))


	def get(self):
		template_values = {}
		self.render_response('userDemo.html', **template_values)

class getWishlist(authHandler):
	def get(self,fId):

		uuId = fId

		fId = int(fId)
		getUser = userData.query()
		getUser = getUser.filter(userData.fId==fId)
		getUser = getUser.iter(limit=1)
		
		try:
			user = getUser.next()
			uuId = user.key
			getLikes = responses.query()
			getLikes = getLikes.filter(responses.uuId==uuId)
			getLikes = getLikes.filter(responses.act=="like")
			results = getLikes.iter()
			pKeys = []
			pList = []
			if results.has_next():
				for result in results:
					pKeys.append(result.pId)
				products = ndb.get_multi(pKeys)
				for p in products:
					newP = {}
					newP['name'] = p.name
					newP['source'] = p.source
					newP['url'] = p.url
					newP['img'] = p.img
					newP['description'] = p.description
					newP['price'] = p.price
					newP['currency'] = p.currency
					newP['sex'] = p.sex
					newP['sCat'] = p.sCat
					newP['rating'] = p.rating
					pList.append(newP)

				template_values = {'pList':pList,'user':user}
				self.render_response('wishList.html',**template_values)
			else:
				self.response.write("Hello! The wishlist you're visiting is empty!")
		except StopIteration:
			self.response.write('No users found')

class getTopShoes(authHandler):
	def get(self,num):
		getShoes = shoes2.query()
		getShoes = getShoes.order(-shoes2.rating)

		products = getShoes.iter(limit=int(num))
		pList = []
		user = {'name':'Top '+num+' Shoes'}
		for p in products:
			newP = {}
			newP['name'] = p.name
			newP['source'] = p.source
			newP['url'] = p.url
			newP['img'] = p.img
			newP['description'] = p.description
			newP['price'] = p.price
			newP['currency'] = p.currency
			newP['sex'] = p.sex
			newP['sCat'] = p.sCat
			newP['rating'] = p.rating
			pList.append(newP)

		template_values = {'pList':pList,'user':user}
		self.render_response('wishList.html',**template_values)


class home(authHandler):
	def get(self):
		template_values = {}
		self.render_response('index.html', **template_values)

application = webapp2.WSGIApplication([
	('/get/products',getShoes),
	('/get/catList',getCat),
	('/push/action',pushAction),
	('/push/email',pushEmail),
	('/queue/action',queueAction),
	('/users/new',newUser),
	('/admin/addShoeTask', setup.addShoeTask),
	('/admin/new/task',setup.setTask),
	('/admin/addShoe', setup.addShoe),
	('/admin/update/cat',setup.updateCat),
	('/admin/update/cat/task',setup.updateCatTask),
	('/admin/update/topShoes',setup.updatetopShoes),
	('/admin/update/deleteAll',setup.deleteAll),
	('/u/(.*)', getWishlist),
	('/blog/top/(.*)',getTopShoes),
	('/', home)],
	debug=True)

def main():
    application.run()

if __name__ == "__main__":
    main()
