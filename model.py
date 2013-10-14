from google.appengine.ext import db

class shoes2(db.Model):
	source = db.StringProperty()
	name = db.StringProperty()
	url = db.StringProperty()
	img = db.StringProperty()
	description = db.TextProperty()
	price = db.FloatProperty()
	currency = db.StringProperty()
	pId = db.IntegerProperty()
	catId = db.IntegerProperty() #is it smart to lock this in as an integer?
	catName = db.StringProperty()
	mcatName = db.StringProperty()
	sku = db.StringProperty()
	prevPrice = db.FloatProperty()
	inStock = db.BooleanProperty()
	sizes = db.ListProperty(str)

	color = db.StringProperty()
	sex = db.BooleanProperty() #men = 1, women = 0
	

class userData(db.Model):
	created = db.DateTimeProperty(auto_now_add=True)
	lastUpdate = db.DateTimeProperty()
	perm = db.BooleanProperty()
	userId = db.IntegerProperty() #smart to lock in as an integer?
	likes = db.ListProperty(int)


class organization(db.Model):
	prefix = db.StringProperty()
	update = db.StringProperty()
	helpCount = db.IntegerProperty(default=0)
	orgName = db.ReferenceProperty()
	isResolved = db.BooleanProperty(default=False)
	resolvedBy = db.UserProperty()
	location = db.StringProperty()


class UserProfile(db.Model):
    User = db.UserProperty()
    FirstSession = db.DateTimeProperty(auto_now_add=True)
    organization = db.ReferenceProperty()

class answerListing(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    status = db.ReferenceProperty()
    user = db.UserProperty()
    private = db.BooleanProperty(default=False)
    answer = db.StringProperty()
