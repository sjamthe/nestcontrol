#!/usr/bin/env python2.7

# Nest thermostat controller
#
# https://github.com/scotte/nestcontrol
# Licensed under GNU GPL 3.0. See the LICENSE.

import argparse
import calendar
import json
import os
import re
import requests
import time


urls = {'login': 'https://home.nest.com/user/login',
        'status': '/v2/mobile/user',
        'set': '/v2/put/shared'}
modes = ['off', 'heat', 'cool', 'auto', 'range']
tokendir = '%s/.cache/nestcontrol' % os.environ['HOME']
tokenfile = 'token'
tokenpath = '%s/%s' % (tokendir, tokenfile)
tempre = re.compile('^[0-9\.]+$')
rangere = re.compile('^[0-9\.]+-[0-9\.]+$')
debug = 0


def cel_to_fahr(celsius):
    return celsius * 1.8 + 32.0


def fahr_to_cel(fahrenheit):
    return (fahrenheit - 32.0) / 1.8


def nest_post(session, url, data, headers=None):
    debug2('POST:', url)
    debug3('headers:', headers)
    r = session.post(url, headers=headers, data=data)
    debug2('http_status:', r.status_code)
    debug3('headers:', r.headers)
    if r.status_code != 200:
        log('Error, nest API returned HTTP status %d' % r.status_code)
        return None
    debug3('data:', r.text)
    return r


def nest_get(session, url, data, headers=None):
    debug2('POST:', url)
    debug3('headers:', headers)
    r = session.get(url, headers=headers, data=data)
    debug2('http_status:', r.status_code)
    debug3('headers:', r.headers)
    if r.status_code != 200:
        log('Error, nest API returned HTTP status %d' % r.status_code)
        return None
    debug3('data:', r.text)
    return r


def auth_url_userid(auth, url):
    return "%s%s.%s" % (auth['url'], url, auth['userid'])


def auth_url_serial(auth, url, serial):
    return "%s%s.%s" % (auth['url'], url, serial)


def auth_headers(auth):
    return {'Authorization': 'Basic %s' % auth['token'],
            'X-nl-user-id': auth['userid'],
            'X-nl-protocol-version': '1'}


def auth_nest_post_serial(session, auth, url, data, serial):
    headers = auth_headers(auth)
    jsondata = json.dumps(data)
    return nest_post(session, auth_url_serial(auth, url, serial), jsondata, headers)


def auth_nest_get_userid(session, auth, url, data=None):
    headers = auth_headers(auth)
    return nest_get(session, auth_url_userid(auth, url), data, headers)


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
    data = r.json()

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
    r = auth_nest_get_userid(session, auth, urls['status'])
    return r.json()


def do_temp(session, auth, fahrenheit, serial):
    celsius = fahr_to_cel(float(fahrenheit))
    debug1('Setting temp to %s (%0.1f)' % (fahrenheit, celsius))
    data = {'target_change_pending': True,
            'target_temperature': celsius}
    auth_nest_post_serial(session, auth, urls['set'], data, serial)


def do_range(session, auth, range, serial):
    (lowf, highf) = range.split('-')
    lowc = fahr_to_cel(float(lowf))
    highc = fahr_to_cel(float(highf))
    debug1('Setting temp to %s-%s (%0.1f-%0.1f)' % (lowf, highf, lowc, highc))
    data = {'target_change_pending': True,
            'target_temperature_low': lowc,
            'target_temperature_high': highc}
    auth_nest_post_serial(session, auth, urls['set'], data, serial)


def do_mode(session, auth, mode, serial):
    if mode == 'auto':
        mode = 'range'
    debug1('Setting mode to %s' % mode)
    data = {'target_change_pending': True,
            'target_temperature_type': mode}
    auth_nest_post_serial(session, auth, urls['set'], data, serial)


def do_command_temps(session, auth, command, serial):
    if tempre.match(command):
        debug1('Executing temp setpt command "%s"' % command)
        do_temp(session, auth, command, serial)
    elif rangere.match(command):
        debug1('Executing temp range command "%s"' % command)
        do_range(session, auth, command, serial)
    else:
        pass  # Ignore everything else for now


def do_command_modes(session, auth, command, serial):
    if tempre.match(command) or rangere.match(command):
        pass
    elif command in modes:
        debug1('Executing mode command "%s"' % command)
        do_mode(session, auth, command, serial)
    else:
        log('Ignoring unknown command "%s"' % command)


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
    argparser.add_argument('-u', '--username', required=True, help='Nest username.')
    argparser.add_argument('-p', '--password', required=True, help='Nest password.')
    argparser.add_argument('-s', '--serial', help='Nest serial number (Default: first nest found).')
    argparser.add_argument('-f', '--fulljson', action='store_true', default=False, help='Output entire status as json (Default: False).')
    argparser.add_argument('-j', '--json', action='store_true', default=False, help='Output basic info as json (Default: False).')
    argparser.add_argument('-d', '--debug', type=int, default=0, help='Debug level. Higher is more (Default: 0).')
    argparser.add_argument('command', nargs='*', help='commands - off, heat, cool, auto, or a set temperature in Fahrenheit. For example, to turn hvac off, use the command "off", or to turn on heat and set the temperature, "heat 72", or to just set the temperature "68". For auto, specify a temperature range (such as "68-72"). Commands are executed in the order provided, with set points first, and note: don\'t enter the quotes.')

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

    for command in args.command:
        do_command_temps(session, auth, command, serial)

    for command in args.command:
        do_command_modes(session, auth, command, serial)

    for command in args.command:
        do_command_temps(session, auth, command, serial)

    # If we executed a command, update the status
    if len(args.command) > 0:
        data = get_status(session, auth)

    temp = cel_to_fahr(data['shared'][serial]['current_temperature'])
    humidity = data['device'][serial]['current_humidity']
    mode = data['shared'][serial]['target_temperature_type']
    setpt = cel_to_fahr(data['shared'][serial]['target_temperature'])
    setptlow = cel_to_fahr(data['shared'][serial]['target_temperature_low'])
    setpthigh = cel_to_fahr(data['shared'][serial]['target_temperature_high'])

    if args.fulljson:
        print json.dumps(data, indent=2)
    elif args.json:
        result = dict()
        result['temp'] = float('%.1f' % temp)
        result['humidity'] = humidity
        result['setpt'] = float('%.1f' % setpt)
        result['setptlow'] = float('%.1f' % setptlow)
        result['setpthigh'] = float('%.1f' % setpthigh)
        result['mode'] = mode
        print json.dumps(result, indent=2)
    else:
        if mode != 'range':
            print u'Temp: %.1f\N{DEGREE SIGN}F, Humidity: %d%%, Set: %.1f\N{DEGREE SIGN}F, Mode: %s' % (temp, humidity, setpt, mode)
        else:
            print u'Temp: %.1f\N{DEGREE SIGN}F, Humidity: %d%%, Set: %.1f\N{DEGREE SIGN}F - %.1f\N{DEGREE SIGN}F, Mode: %s' % (temp, humidity, setptlow, setpthigh, mode)
