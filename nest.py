#!/usr/bin/env python2.7

import argparse
import json
import requests
import urllib


def cel_to_fahr(celsius):
    return celsius * 1.8 + 32.0


def fahr_to_cel(fahrenheit):
    return (fahrenheit - 32.0) / 1.8


def login(session, username, password):
    payload = {'username': args.username, 'password': args.password}
    headers = {'user-agent': 'Nest/1.1.0.10 CFNetwork/548.0.4'}
    r = s.post('https://home.nest.com/user/login', data=payload, headers=headers)
    #print r.status_code
    #print r.headers

    data = r.json()
    #print data

    auth = dict()
    auth['url'] = data['urls']['transport_url']
    auth['token'] = data['access_token']
    auth['userid'] = data['userid']

    #print url
    #print token
    #print userid
    return auth


def get_status(session, auth):
    headers = {'user-agent':'Nest/1.1.0.10 CFNetwork/548.0.4',
               'Authorization':'Basic ' + auth['token'],
               'X-nl-user-id': auth['userid'],
               'X-nl-protocol-version': '1'}
    r = s.get(auth['url'] + '/v2/mobile/user.' + auth['userid'], headers=headers)
    #print r.status_code
    #print r.headers

    #print json.dumps(data, indent=2)
    return r.json()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description="Nest thermostat controller")
    argparser.add_argument('-u', '--username', required=True, help='Nest username')
    argparser.add_argument('-p', '--password', required=True, help='Nest password')
    argparser.add_argument('-s', '--serial', help='Nest serial number (Default: first nest found)')
    args = argparser.parse_args()

    s = requests.Session()

    auth = login(s, args.username, args.password)

    data = get_status(s, auth)

    if args.serial is None:
        for structure in data['structure']:
            serial = data['structure'][structure]['devices'][0].split('.')[1]
            pass
    else:
        serial = args.serial

    temp = cel_to_fahr(data['shared'][serial]['current_temperature'])
    humidity = data['device'][serial]['current_humidity']
    setpt = cel_to_fahr(data['shared'][serial]['target_temperature'])
    mode = data['shared'][serial]['target_temperature_type']

    print u'Temp: %.1f\N{DEGREE SIGN}F, Humidity: %d%%, Set: %.1f\N{DEGREE SIGN}F, Mode: %s' % (temp, humidity, setpt, mode)
