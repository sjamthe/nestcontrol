#!/usr/bin/env python2.7

import argparse
import calendar
import json
import os
import requests
import time


urls = {'login': 'https://home.nest.com/user/login',
        'status': '/v2/mobile/user'}
tokendir = '%s/.cache/nestcontrol' % os.environ['HOME']
tokenfile = 'token'
tokenpath = '%s/%s' % (tokendir, tokenfile)
debug = 0


def cel_to_fahr(celsius):
    return celsius * 1.8 + 32.0


def fahr_to_cel(fahrenheit):
    return (fahrenheit - 32.0) / 1.8


def nest_post(session, url, data, headers=None):
    return session.post(url, headers=headers, data=data)


def nest_get(session, url, data, headers=None):
    return session.get(url, headers=headers, data=data)


def auth_url(auth, url):
    return "%s%s.%s" % (auth['url'], url, auth['userid'])


def auth_headers(auth):
    return {'Authorization': 'Basic %s' % auth['token'],
            'X-nl-user-id': auth['userid'],
            'X-nl-protocol-version': '1'}


def auth_nest_post(session, auth, url, data):
    headers = auth_headers(auth)
    return nest_post(session, auth_url(auth, url), data, headers)


def auth_nest_get(session, auth, url, data=None):
    headers = auth_headers(auth)
    return nest_get(session, auth_url(auth, url), data, headers)


def login(session, username, password):
    if os.path.isfile(tokenpath):
        authfile = open(tokenpath, 'r')
        auth = json.load(authfile)
        ts = calendar.timegm(time.strptime(auth['expires'], '%a, %d-%b-%Y %H:%M:%S %Z'))
        if time.time() < ts:
            debug1('Using token from cache')
            return auth
        else:
            debug1('Cached token was expired, need a new one')

    debug1('Logging in')
    payload = {'username': args.username, 'password': args.password}
    r = nest_post(session, urls['login'], payload)
    debug2('http_status:', r.status_code)
    debug3('headers:', r.headers)

    data = r.json()
    debug3('json data:', data)

    auth = dict()
    auth['url'] = data['urls']['transport_url']
    auth['token'] = data['access_token']
    auth['userid'] = data['userid']
    auth['expires'] = data['expires_in']

    debug2('url:', auth['url'])
    debug2('token:', auth['token'])
    debug2('userid:', auth['userid'])
    debug2('expires:', auth['expires'])

    path = ''
    for dir in tokendir.split('/'):
        path += '%s/' % dir
        if not os.path.isdir(path):
            os.mkdir(path, 0700)

    authfile = open(tokenpath, 'w')
    json.dump(auth, authfile)

    return auth


def get_status(session, auth):
    debug1('Getting status')
    r = auth_nest_get(session, auth, urls['status'])
    debug2('http_status:', r.status_code)
    debug3('headers:', r.headers)
    debug3('json data:', r.json())
    return r.json()


def log(*args):
    print ' '.join(map(str, args))


def debug1(*args):
    if debug >= 1:
        log(*args)


def debug2(*args):
    if debug >= 2:
        log(*args)


def debug3(*args):
    if debug >= 3:
        log(*args)

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description="Nest thermostat controller")
    argparser.add_argument('-u', '--username', required=True, help='Nest username')
    argparser.add_argument('-p', '--password', required=True, help='Nest password')
    argparser.add_argument('-s', '--serial', help='Nest serial number (Default: first nest found)')
    argparser.add_argument('-d', '--debug', type=int, default=0, help='Debug level. Higher is more (Default: 0)')
    args = argparser.parse_args()

    debug = args.debug

    session = requests.Session()

    auth = login(session, args.username, args.password)

    data = get_status(session, auth)

    if args.serial is None:
        for structure in data['structure']:
            serial = data['structure'][structure]['devices'][0].split('.')[1]
            pass
    else:
        serial = args.serial

    temp = cel_to_fahr(data['shared'][serial]['current_temperature'])
    humidity = data['device'][serial]['current_humidity']
    mode = data['shared'][serial]['target_temperature_type']

    if mode != 'range':
        setpt = cel_to_fahr(data['shared'][serial]['target_temperature'])
        print u'Temp: %.1f\N{DEGREE SIGN}F, Humidity: %d%%, Set: %.1f\N{DEGREE SIGN}F, Mode: %s' % (temp, humidity, setpt, mode)
    else:
        setptlow = cel_to_fahr(data['shared'][serial]['target_temperature_low'])
        setpthigh = cel_to_fahr(data['shared'][serial]['target_temperature_high'])
        print u'Temp: %.1f\N{DEGREE SIGN}F, Humidity: %d%%, Set: %.1f\N{DEGREE SIGN}F - %.1f\N{DEGREE SIGN}F, Mode: %s' % (temp, humidity, setptlow, setpthigh, mode)
