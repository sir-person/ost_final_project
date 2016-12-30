import os 
import webapp2
import jinja2
import logging
import urllib
from google.appengine.api import users
from google.appengine.ext import ndb
from data.reservations import Reservation, Resource 

from datetime import datetime,time,timedelta

jinja_environment = jinja2.Environment(autoescape=True,
 loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

hackey_gmt_offset= timedelta(hours=-5)
class LandingHandler(webapp2.RequestHandler):

	def get(self):
		logging.info(self.request.scheme)
		user = users.get_current_user() 
		owned_set = set() 
		if not user:
			webapp2.abort(403)
		
		owned_query = Resource.query(Resource.owner == user).order(-Resource.last_reserved_on)
		owned_resources = []
		for resource in owned_query.fetch():
			owned_resources.append( resource.to_html())

		all_query = Resource.query().order(-Resource.last_reserved_on)
		all_resources = []
		names = dict()
		for resource in all_query.fetch():
			names[resource.key.id()] = resource.name
			all_resources.append(resource.to_html())

		reservations = []
		res_query=Reservation.query(Reservation.reserver == user, Reservation.end_on>datetime.utcnow()+hackey_gmt_offset).order(Reservation.end_on,Reservation.start_on)
		for reservation in res_query.fetch():
			html=reservation.to_html()
			html['resource_name']= names[reservation.resource_key.id()]
			reservations.append(html)

		template_values = {
			'user' : user,
			'all_resources':all_resources,
			'owned_resources':owned_resources,
			'reservations':reservations,
		}   
		template = jinja_environment.get_template('landing_page.html')
		self.response.out.write(template.render(template_values))


class ResourceViewHandler(webapp2.RequestHandler):

	def get(self):
		resource_feedback = self.request.get('resource_feedback')
		reservation_feedback = self.request.get('reservation_feedback')

		user = users.get_current_user()        
		resource_id = self.request.get('resource_id')
		if not resource_id:
			webapp2.abort(400)

		key = ndb.Key(urlsafe=resource_id)
		resource = key.get()

		reservations = []
		res_query=Reservation.query(Reservation.resource_key == key).order(Reservation.start_on)
		for reservation in res_query.fetch():
			reservations.append(reservation.to_html())

		template_values = {
			'email' : user.nickname(),
			'resource': resource.to_html(),
			'reservations': reservations,
			'resource_feedback':resource_feedback,
			'reservation_feedback':reservation_feedback,
			'user':user,
		}   
		template = jinja_environment.get_template('resource.html')
		self.response.out.write(template.render(template_values))


	def post(self):
		user = users.get_current_user()        
		if not user:
			webapp2.abort(403)
		resource_id = self.request.get('resource_id')
		key = ndb.Key(urlsafe=resource_id)
		resource = key.get()
		resource_feedback = ''
		scheme=self.request.scheme
		host=self.request.host
		if not resource:
			webapp2.abort(404)

		if resource.owner!= user:
			resource_feedback = 'You do not own this resource'
			params = {'resource_id': resource_id,'resource_feedback': resouce_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
			return

		resource_name = self.request.get('resource_name')
		if not resource_name:
			resource_feedback = 'resource name is required'
			params = {'resource_id': resource_id,'resource_feedback': resouce_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
			return

		resource_start = self.request.get('resource_start')
		resource_stop = self.request.get('resource_stop')
		try:
			resource_start = datetime.strptime(resource_start, "%H:%M").time()
			resource_stop = datetime.strptime(resource_stop, "%H:%M").time()
		except Exception as e:
			resource_feedback = str(e)
			params = {'resource_id': resource_id,'resource_feedback': resouce_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
			return


		resource_tags = self.request.get('resource_tags').strip()
		if resource_tags:
			tokens = resource_tags.lower().split(",")
			resource_tags = [token.strip() for token in set(tokens)]
		else:
			resource_tags = []

		resource_description = self.request.get('resource_description')	
		resource.name = resource_name
		resource.tags = resource_tags
		resource.availability_start_on = resource_start
		resource.availability_end_on = resource_stop
		resource.description = resource_description
		
		resource.put()
		reservations=[]
		reservations_query = Reservation.query(Reservation.resource_key==key).order(Reservation.start_on)	
		
		for reservation in reservations_query.fetch():
			reservations.append(reservation.to_html())

		template_values = {
			'email' : user.nickname(),
			'reservations':reservations,
			'resource': resource.to_html(),
			'user': user
		}   
		template = jinja_environment.get_template('resource.html')
		self.response.out.write(template.render(template_values))


class ResourceHandler(webapp2.RequestHandler):

	def post(self):
		user = users.get_current_user()    
		scheme=self.request.scheme
		host=self.request.host    
		if not user:
			webapp2.abort(403)

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
		resource_description = self.request.get('resource_description')	
		resource = Resource(
			name = resource_name,
			tags = resource_tags,
			owner = user,
			availability_start_on = resource_start,
			availability_end_on = resource_stop,
			description = resource_description
		)
		k = resource.put()

		#Code form the home page load 
		owned_set = set() 
		owned_query = Resource.query(Resource.owner == user).order(-Resource.last_reserved_on)
		owned_resources = []
		for resource in owned_query.fetch():
			owned_resources.append( resource.to_html())

		all_query = Resource.query().order(-Resource.last_reserved_on)
		all_resources = []
		for resource in all_query.fetch():
			all_resources.append(resource.to_html())

		reservations_query = Reservation.query(Reservation.owner == user).order(Reservation.start_on)	
		template_values = {
			'email' : user.nickname(),
			'all_resources':all_resources,
			'owned_resources':owned_resources,
			'reservations':[],
		}   
		template = jinja_environment.get_template('landing_page.html')
		self.response.out.write(template.render(template_values))

	def get(self):
		user = users.get_current_user()        
		if not user:
			webapp2.abort(403)

		template = jinja_environment.get_template('new_resource.html')
		template_values = {
			'email' : user.nickname()
		}   
		self.response.out.write(template.render(template_values))


class ReservationCreateHandler(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user()        
		resource_id = self.request.get("resource_id")
		
		scheme=self.request.scheme
		host=self.request.host
		if not resource_id:
			self.redirect("%s://%s/"%(scheme,host),True)

		key = ndb.Key(urlsafe=resource_id)
		resource = key.get()
		reservation_date = self.request.get('reservation_date')
		reservation_duration = self.request.get('reservation_duration')
		end_date = None
		try:
			reservation_date = datetime.strptime(reservation_date, "%m/%d/%Y %H:%M")
			reservation_duration = datetime.strptime(reservation_duration, "%H:%M").time()
			end_date = reservation_date + timedelta(hours=reservation_duration.hour, minutes=reservation_duration.minute)
		except Exception as e:
			reservation_feedback = 'resource name is required'
			params = {'resource_id': resource_id,'reservation_feedback': reservation_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
		
		if reservation_date > end_date:
			reservation_feedback = 'reservation date %s is after end date %s'%(reservation_date,end_date)
			params = {'resource_id': resource_id,'reservation_feedback': reservation_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
			return

		if reservation_date.day != end_date.day:
			reservation_feedback='Your duration goes beyond the day boundary'
			params = {'resource_id': resource_id,'reservation_feedback': reservation_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
			return

		reserve_time=reservation_date.time()
		if resource.availability_start_on > reserve_time:
			reservation_feedback='Requested date %s is before avialibility hours %s'%(reserve_time,resource.availability_start_on) 
			params = {'resource_id': resource_id,'reservation_feedback': reservation_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
			return
		

		if resource.availability_end_on < end_date.time():
			reservation_feedback='Requested date %s is after avialibility hours %s'%(end_date.time(),resource.availability_end_on,) 
			params = {'resource_id': resource_id,'reservation_feedback': reservation_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
			return
		
		res_day_begin = reservation_date.replace(hour=0, minute=0, second=0, microsecond=0)
		res_day_end = res_day_begin + timedelta(days=1)

		res_before=Reservation.query(Reservation.resource_key == key, Reservation.start_on <= reservation_date, Reservation.start_on >= res_day_begin ).get()
		res_after=Reservation.query(Reservation.resource_key == key, Reservation.start_on >= reservation_date, Reservation.start_on <= res_day_end ).get()
		
		if res_before and res_before.end_on >= reservation_date:
			reservation_feedback = '%s conflicts with appointment at %s' %(reservation_date, res_before.start_on)
			params = {'resource_id': resource_id,'reservation_feedback': reservation_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
			return

		if res_after and res_after.start_on <= end_date:
			reservation_feedback = '%s conflicts with appointment at %s' %(reservation_date, res_after.start_on)
			params = {'resource_id': resource_id,'reservation_feedback': reservation_feedback}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
			return


		reservation = Reservation(
			reserver=user,
			owner=resource.owner,
			resource_key=key,
			start_on=reservation_date,
			end_on= end_date
		)
		reservation.put()
		resource.last_reserved_on = datetime.utcnow()
		resource.put()
		params = {'resource_id': resource_id}
		self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)

	#cancel reservation
	def get(self):
		user = users.get_current_user()        
		reservation_id = self.request.get("reservation_id")
		resource_id = self.request.get("resource_id")
		scheme=self.request.scheme
		host=self.request.host
		if not reservation_id:
			params = {'resource_id': resource_id}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
		key = ndb.Key(urlsafe=reservation_id)
		reservation = key.get()
		if not reservation:
			params = {'resource_id': resource_id,'reservation_feedback':'That reservation has already been cancelled'}
			self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)
		key.delete()
		params = {'resource_id': resource_id}
		self.redirect("%s://%s/resource/view?%s"%(scheme,host,urllib.urlencode(params)),True)

app = webapp2.WSGIApplication([
	('/', LandingHandler),
	('/resource/new', ResourceHandler),
	('/resource/view', ResourceViewHandler),
	('/reservation/new', ReservationCreateHandler),
])