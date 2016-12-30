import os 
import webapp2
import jinja2
import logging
from google.appengine.api import users
from google.appengine.ext import ndb
from data.reservations import Reservation, Resource 

from datetime import datetime,time

jinja_environment = jinja2.Environment(autoescape=True,
 loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class LandingHandler(webapp2.RequestHandler):
	def post(self):
		pass
        
		webapp2.abort(403)
	def get(self):
		pass


class ResourceHandler(webapp2.RequestHandler):

	def post(self):
		user = users.get_current_user()        
		if not user:
			webapp2.abort(403)
		user_id = user.user_id()
		resource_name = self.request.get('resource_name')
		if not resource_name:
			webapp2.abort(400)

		resource_start = self.request.get('resource_start')
		if not resource_start:
			webapp2.abort(400)
		resource_start = datetime.strptime(resource_start, "%H:%M").time()

		resource_stop = self.request.get('resource_stop')
		if not resource_stop:
			webapp2.abort(400)
		resource_stop = datetime.strptime(resource_stop, "%H:%M").time()

		resource_tags = self.request.get('resource_tags').strip()
		if resource_tags:
			tokens = resource_tags.lower().split(",")
			resource_tags = [token.strip() for token in set(tokens)]
		else:
			resource_tags = []
	# m = re.search('\d{2}:\d{2} (am|pm)', '02:33 pm')		
		resource = Resource(
			name = resource_name,
			tags = resource_tags,
			owner = user_id,
			availability_start_on = resource_start,
			availability_end_on = resource_stop
		)
		k = resource.put()

	def get(self):
		user = users.get_current_user()        
		if not user:
			webapp2.abort(403)
		user_id = user.user_id()
		template = jinja_environment.get_template('new_resource.html')
		template_values = {
			'email' : user.nickname()
		}   
		self.response.out.write(template.render(template_values))


class ReservationHandler(webapp2.RequestHandler):
	def post(self):
		webapp2.abort(403)
		pass
	def get(self):
		pass

app = webapp2.WSGIApplication([
	('/', LandingHandler),
	('/resource/new', ResourceHandler)
])