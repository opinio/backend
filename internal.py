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
  'template_path':'/',
  'environment_args': {
    'autoescape': True,
    'extensions': [
        'jinja2.ext.autoescape']}
}


jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class authHandler(webapp2.RequestHandler):
	def render_response(self, template_path, **template_values):
		template = jinja_environment.get_template(template_path)
		self.response.write(template.render(**template_values))


class listShoes(authHandler):
	def get(self):
		pass	
