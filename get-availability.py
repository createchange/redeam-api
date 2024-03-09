#! /usr/bin/env python3

'''
author: Jonathan Weaver
date: 2019-10-28
'''

import configparser
import requests
import json
import argparse
from argparse import SUPPRESS
from datetime import datetime, timedelta
from dateutil.parser import parse
import sys


'''
Import API keys and set headers for requests library
'''
config = configparser.ConfigParser()
config.read('config.ini')
api_key = config['redeam_api']['api_key']
api_secret = config['redeam_api']['api_secret']

headers =  headers = {
        'X-API-Key': api_key,
        'X-API-Secret': api_secret
}


def sanitizeDateEntry(sdate, edate):
    '''
    takes start and end dates from arguments (default or user inputted)
    returns time formatted properly for query
    '''
    try:
        delta = parse(edate) - parse(sdate)
        if delta.days > 30:
            confirm = input("Your search spans %s days. Are you sure you want to continue?\n(y/N)> " % str(delta.days))
            if confirm.lower() == "y":
                start = parse(sdate).isoformat() + "Z"
                end = parse(edate).isoformat() + "Z"
                return start, end
            else:
                print("Please correct date parameters and try again.")
                exit()
        else: 
            start = parse(sdate).isoformat() + "Z"
            end = parse(edate).isoformat() + "Z"
            return start, end

    except ValueError:
        print("Incorrect data format, should be YYYY-MM-DD")
        exit()


def getAvailabilities(headers, supplier_id, product_id, start_date, end_date):
    '''
    Call to listAvailabilities Redeam endpoint to obtain availabilities as per: supplied_id, product_id, start_date, end_date
    Docs: https://docs.booking.sandbox.redeam.io/booking-api-reference-v1.2/#operation/listAvailabilities
    '''
    r = requests.get(
            "https://booking.sandbox.redeam.io/v1.2/suppliers/%s/products/%s/availabilities" % (supplier_id, product_id),
            params = [('start', start_date), ('end', end_date)],
            headers=headers,
    )
    
    return r


def getSupplierName(headers, supplier_id):
    '''
    called by getAvailabilities function, returns Supplier name for use in output of availabilities
    Docs: https://docs.booking.sandbox.redeam.io/booking-api-reference-v1.2/#operation/getSupplier
    '''
    r = requests.get(
            "https://booking.sandbox.redeam.io/v1.2/suppliers/%s" % supplier_id,
            headers=headers,
    )

    data = json.loads(r.text)
    return data['supplier']['mainLocation']['name']


def getProductName(headers, supplier_id, product_id):
    '''
    called by getAvailabilities function, returns Product name for use in output of availabilities
    Docs: https://docs.booking.sandbox.redeam.io/booking-api-reference-v1.2/#operation/getProduct
    '''
    r = requests.get(
            "https://booking.sandbox.redeam.io/v1.2/suppliers/%s/products/%s" % (supplier_id, product_id),
            headers=headers,
    )

    data = json.loads(r.text)
    return data['product']['title']

def getRate(headers, supplier_id, product_id, rate_id):
    '''
    called by getAvailabilities function, returns Rate for use in output of availabilities
    Docs: https://docs.booking.sandbox.redeam.io/booking-api-reference-v1.2/#operation/getRate
    '''
    r = requests.get(
            "https://booking.sandbox.redeam.io/v1.2/suppliers/%s/products/%s/rates/%s" % (supplier_id, product_id, rate_id),
            headers=headers,
    )

    data = json.loads(r.text)
    name = data['rate']['name']
    prices = {}
    for i in range(len(data['rate']['prices'])):
        prices[data['rate']['prices'][i]['name']] = data['rate']['prices'][i]['retail']['amount']
    return name, prices

def apiCallErrorCheck(r):
    '''
    Takes API response from getAvailabilities function.
    Checks response code for api call.
    If 200, passes data back to be returned to user.
    Else, displays status code and accompanying error message and quits program.
    '''
    if r.status_code != 200:
        response = json.loads(r.text)
        print("Status code: %s\nError: %s\n\nPlease retry your query." % (r.status_code, response['error']['message']))
        exit()
    else:
        data = json.loads(r.text)
        return data


def returnResponseData(data):
    '''
    Takes data from valid response code and prints out availability info
    Could clean this up to assign each output field to a variable in order to shorten 'print' line of code.
    Should convert +00:00 timezone to localtime (and provide timezone info by name)
    '''
    # Check if data exists
    data_exists = False
    for key in data['availabilities']['byRate'].keys():
        if data['availabilities']['byRate'][key]:
            data_exists = True

    if data_exists == False:
        print("\nNo results. Please alter date parameters and try again.")
        exit()

    # Create dict of rate results
    rates = {}
    x = 1
    for key in data['availabilities']['byRate'].keys():
        name, prices = getRate(headers, args.supplierid, args.productid, key)
        supplier = getSupplierName(headers, args.supplierid)
        rates[x] = {'key':key, 'name':"%s (%s)" % (name, supplier), 'priceAdult': prices['Adult'], 'priceChild':prices['Child']}
        x += 1

    # Print out rates results for uses to select from
    for k,v in rates.items():
        print("\n%s. %s\n   Pricing:\n      Adult: %s\n      Child: %s" % (k,v['name'],v['priceAdult'],v['priceChild']))
        print("   Results: %s" % len(data['availabilities']['byRate'][v['key']]['availability']))

    while True:
        try:
            rate_selection = int(input("\nPlease input number for which event you'd like availability for:\n> "))
            key_selection = rates[rate_selection]

            for i in range(len(data['availabilities']['byRate'][key]['availability'])):
                # Return start/end datetime of each availability, as well as capacity
                availability_info = data['availabilities']['byRate'][key]['availability'][i]
                print("Start: %s\nEnd: %s\nCapacity: %s\n" % (parse(availability_info.get('start')).strftime("%A, %x @ %-I:%M%p %Z"), parse(availability_info.get('end')).strftime("%A, %x @ %-I:%M%p %Z"), availability_info.get('capacity')))
            break
            
        # Reject bad input and send back to try statement    
        except:
            print("Please make a valid selection.")


'''''''''''''''''
MAIN
'''''''''''''''''

'''
sets standard dates for search:
    cd = current date
    ed = 2 weeks from current date
'''
cd = datetime.utcnow()
ed = datetime.utcnow() + timedelta(days=14)


'''
Argument Parser
'''
# Initialize w/ description
desc = "Utilizes Redeam API to obtain availability for specified products.\n\nIf no date arguments are specified, search will default to two weeks out from today's date."
parser = argparse.ArgumentParser(description = desc, add_help=False)

# Set required arguments
required = parser.add_argument_group('required arguments')
required.add_argument("-pid", "--productid", help="for testing, use: 02f0c6cb-77ae-4fcc-8f4d-99bc0c3bee18", required=True)
required.add_argument("-sid", "--supplierid", help="for testing, use: fc49b925-6942-4df8-954b-ed7df10adf7e", required=True)

# Set optional arguments
optional = parser.add_argument_group('optional arguments')
optional.add_argument("-sdate", "--startdate", help="YYYY-MM-DD formatting. Defaults to today's date", nargs='?', default=str(cd))
optional.add_argument("-edate", "--enddate", help="YYYY-MM-DD formatting. Defaults to two weeks from today's date", nargs='?', default=str(ed))
optional.add_argument("-h", "--help", action='help', default=SUPPRESS, help="show this help message and exit")

# Parse arguments
args = parser.parse_args(None if sys.argv[1:] else ['-h'])


sdate, edate = sanitizeDateEntry(args.startdate, args.enddate)
r = getAvailabilities(headers, args.supplierid, args.productid, sdate, edate)
data = apiCallErrorCheck(r)
returnResponseData(data)
