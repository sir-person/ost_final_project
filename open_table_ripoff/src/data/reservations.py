from google.appengine.ext import ndb
import datetime
class Resource(ndb.Model):

	name = ndb.StringProperty()
	tags = ndb.StringProperty(repeated = True)
	#user_id of the creator of this resource
	owner = ndb.StringProperty()
	availability_start_on = ndb.TimeProperty()
	availability_end_on = ndb.TimeProperty()
	last_reserved_on = ndb.DateTimeProperty()
	created_on = ndb.DateTimeProperty(auto_now_add = True)
	update_on = ndb.DateTimeProperty(auto_now = True)

class Reservation(ndb.Model):

	#user_id of whoever made this reservation
	owner = ndb.StringProperty() 
	resource_key = ndb.KeyProperty()
	start_on = ndb.DateTimeProperty()
	end_on = ndb.DateTimeProperty()
	created_on = ndb.DateTimeProperty(auto_now_add = True)
	update_on = ndb.DateTimeProperty(auto_now = True)

		