from google.appengine.ext import ndb
import datetime
class Resource(ndb.Model):

	name = ndb.StringProperty()
	tags = ndb.StringProperty(repeated = True)
	#using user property because appengine doesn't let you load by user_id
	owner = ndb.UserProperty()
	availability_start_on = ndb.TimeProperty()
	availability_end_on = ndb.TimeProperty()
	last_reserved_on = ndb.DateTimeProperty()
	description = ndb.TextProperty(indexed=False)
	created_on = ndb.DateTimeProperty(auto_now_add = True)
	update_on = ndb.DateTimeProperty(auto_now = True)

	
	def to_html(self):
		return {
			'urlsafe':self.key.urlsafe(),
			'name': self.name,
			'tags': ', '.join(self.tags),
			'owner': self.owner,
			'availability_start_on': self.availability_start_on.strftime('%H:%M'),
			'availability_end_on': self.availability_end_on.strftime('%H:%M'),
			'last_reserved_on': self.last_reserved_on,
			'description': self.description,
			'created_on': self.created_on,
			'update_on': self.update_on
		}


class Reservation(ndb.Model):

	#user of whoever made this reservation
	reserver = ndb.UserProperty()
	#user of resrouce creator
	owner = ndb.UserProperty() 
	resource_key = ndb.KeyProperty()
	start_on = ndb.DateTimeProperty()
	end_on = ndb.DateTimeProperty()
	created_on = ndb.DateTimeProperty(auto_now_add = True)
	update_on = ndb.DateTimeProperty(auto_now = True)

	def to_html(self):
		delta = self.end_on - self.start_on

		return {
			'urlsafe': self.key.urlsafe(),
			'reserver':self.reserver,
			'owner':self.owner,
			'resource_key':self.resource_key.urlsafe(),
			'start_on':self.start_on,
			'end_on':self.end_on,
			'created_on':self.created_on,
			'update_on':self.update_on,
			'duration': str(delta),
		}
		