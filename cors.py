import json
import urllib
import urlparse
import requests
import traceback
import pyramid
import logging
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='lti.log',level=logging.DEBUG
                    )
logger = logging.getLogger('')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger.addHandler(console)

server_scheme = 'https'
server_host = 'h.jonudell.info'
server_port = None

#server_host_internal = '10.0.0.9'  # for local testing
#server_port_internal = 8000

if server_port is None:
    server = '%s://%s' % (server_scheme, server_host)
else:
    server = '%s://%s:%s' % (server_scheme, server_host, server_port)

endpoint = 'https://hypothes.is/api/annotations' 

logger.info( 'server: %s' % server )

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response

def cors_response(request, response=None):
    if response is None:
        response = Response()
    request_headers = request.headers['Access-Control-Request-Headers'].lower()
    request_headers = re.findall('\w(?:[-\w]*\w)', request_headers)
    response_headers = ['access-control-allow-origin']
    for req_acoa_header in request_headers:
        if req_acoa_header not in response_headers:
            response_headers.append(req_acoa_header)
    response_headers = ','.join(response_headers)
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '%s' % response_headers,
        'Access-Control-Allow-Methods': "UPDATE, POST, GET"
        })
    response.status_int = 204
    print ( response.headers )
    return response

def proxy(request, endpoint, method):
    qs = urlparse.parse_qs(request.query_string)
    id = qs['id'][0] if 'id' in qs.keys() else None
    token = qs['token'][0]
    data = request.body
    print ( id, token, data )
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json;charset=utf-8' }
    r1 = None
    if   method == 'get':
        url = '%s/%s' % (endpoint, id)
        print url
        r1 = requests.get(url, headers=headers, data=data)
    elif method == 'put':
        url = '%s/%s' % (endpoint, id)
        print url
        r1 = requests.put(url, headers=headers, data=data)
    elif method == 'post':
        url = endpoint
        print url
        r1 = requests.post(url, headers=headers, data=data)
    else:
        print 'proxy did not expect method %s' % method
    print ( r1.status_code )
    print ( r1.text )
    r2 = Response(r1.text)
    r2.headers.update({
        'Access-Control-Allow-Origin': '*'
        })
    return r2

@view_config( route_name='update' )
def update(request):
    if  request.method == 'OPTIONS':
        print ( 'cors preflight' )
        return cors_response(request)
    else:
        print 'update'
        return proxy(request, endpoint, 'put')

@view_config( route_name='create' )
def create(request):
    if  request.method == 'OPTIONS':
        print ( 'cors preflight' )
        return cors_response(request)
    else:
        print ( 'create' )
        return proxy(request, endpoint, 'post')

@view_config( route_name='get' )
def get(request):
    if  request.method == 'OPTIONS':
        print ( 'cors preflight' )
        return cors_response(request)
    else:
        print ( 'get' )
        return proxy(request, endpoint, 'get')

config = Configurator()

config.scan()

config.add_route('update', '/update')
config.add_route('create', '/create')
config.add_route('get', '/get')

app = config.make_wsgi_app()

if __name__ == '__main__': # local testing

    server = make_server(server_host_internal, server_port_internal, app)
    server.serve_forever()
    

