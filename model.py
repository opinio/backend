from google.appengine.ext import ndb

class shoes2(ndb.Model):
	source = ndb.StringProperty()
	name = ndb.StringProperty()
	url = ndb.TextProperty()
	img = ndb.StringProperty()
	description = ndb.TextProperty()
	price = ndb.FloatProperty()
	currency = ndb.StringProperty()
	pId = ndb.IntegerProperty()
	catId = ndb.IntegerProperty() #is it smart to lock this in as an integer?
	catName = ndb.StringProperty()
	mcatName = ndb.StringProperty()
	sku = ndb.StringProperty()
	prevPrice = ndb.FloatProperty()
	inStock = ndb.BooleanProperty()
	sizes = ndb.StringProperty(repeated=True)

	color = ndb.StringProperty()
	sex = ndb.BooleanProperty() #men = 1, women = 0
	

class userData(ndb.Model):
	uuId = ndb.StringProperty()
	fId = ndb.IntegerProperty()
	created = ndb.DateTimeProperty(auto_now_add=True)
	lastUpdate = ndb.DateTimeProperty()

class responses(ndb.Model):
	pId = ndb.KeyProperty(kind=shoes2)
	uuId = ndb.KeyProperty(kind=userData)
	response = ndb.BooleanProperty()
