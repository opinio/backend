from google.appengine.ext import ndb
import logging

class shoes2(ndb.Model):
#class shoes2(ndb.Expando):
	source = ndb.StringProperty()
	name = ndb.StringProperty()
	price = ndb.FloatProperty()
	priceCat = ndb.IntegerProperty()
	currency = ndb.StringProperty()
	color = ndb.StringProperty()
	sex = ndb.BooleanProperty() #men = 1, women = 0
	srank = ndb.IntegerProperty()
	prevPrice = ndb.FloatProperty()



	#toChange
	#pId = ndb.IntegerProperty() #will help us get uniqueness across yoox dataset
	#sCat = ndb.StringProperty()
	#rating = ndb.IntegerProperty()
	#url = ndb.TextProperty()
	#img = ndb.StringProperty()
	#description = ndb.TextProperty()

	#Changed Versions
	pId = ndb.StringProperty()
	sCat = ndb.StringProperty(repeated=True)
	rating = ndb.FloatProperty()
	url = ndb.TextProperty(indexed=False)
	img = ndb.StringProperty(indexed=False)
	description = ndb.TextProperty(indexed=False)
	country = ndb.StringProperty()


	#newProperties
	likes = ndb.IntegerProperty()
	dislikes = ndb.IntegerProperty()

	#yoox quirky stuff saved just to be safe
	catId = ndb.IntegerProperty() 
	catName = ndb.StringProperty()
	mcatName = ndb.StringProperty()
	sku = ndb.StringProperty()
	inStock = ndb.BooleanProperty()
	sizes = ndb.StringProperty(repeated=True)
	mColor = ndb.StringProperty()
	

class userData(ndb.Model): #no Keyname
	uuId = ndb.StringProperty()
	fId = ndb.IntegerProperty()
	fUsr = ndb.StringProperty() #facebook alias
	fTkn = ndb.StringProperty()
	fLoc = ndb.StringProperty()
	name = ndb.StringProperty()
	email = ndb.StringProperty()
	gender = ndb.BooleanProperty()
	age = ndb.StringProperty()
	created = ndb.DateTimeProperty(auto_now_add=True)
	lastUpdate = ndb.DateTimeProperty()
	nid = ndb.StringProperty()
	cursors = ndb.TextProperty()

class responses(ndb.Model):
	pId = ndb.KeyProperty(kind=shoes2)
	uuId = ndb.KeyProperty(kind=userData)
	act = ndb.StringProperty()
	date = ndb.DateTimeProperty(auto_now_add=True)
	
	#Rummble Labs Integration
	def _post_put_hook(self, future):
		from google.appengine.api import urlfetch
		try:
			if self.act=="like" or self.act=="dislike":
				uKey = str(self.uuId.urlsafe())
				pKey = str(self.pId.urlsafe())
				type = [1,2][self.act=="dislike"]

				lUrl = "http://api.rummblelabs.com/js/action/new?consumer_key=kux4aesu4aip6coo4UiZ&type=1&user="+uKey+"&item="+pKey+"&jsonpCallback="
				dUrl = "http://api.rummblelabs.com/js/action/new?consumer_key=kux4aesu4aip6coo4UiZ&type=2&user="+uKey+"&item="+pKey+"&jsonpCallback="	
				url = [lUrl,dUrl][self.act=="dislike"]
				response = urlfetch.fetch(url)
		except:
			logging.warning("Was not able to send to rummble labs!")
