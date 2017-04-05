import bcrypt
from flask import Flask, request, jsonify, json
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson import ObjectId

import TwilioRestClient
from twilio.rest import TwilioRestClient

# DB setup
client = MongoClient()
db = client.database

hives = db.hives
drones = db.drones

# initiate app
app = Flask(__name__)

# constants
hive_name_key = 'hive_name'
date_created_key = 'date_created'

## signal keys
command_key = 'command'
options_key = 'options'
expires_key = 'expires'
text_key = 'text'
numbers_key = 'numbers'

## utility keys
auth_key = 'auth'
id_key = '_id'

# errors
def param_error(missing_params):
    param_string = ','.join(missing_params)
    error_message = ['error':'You are missing the following parameters: %s' ] % param_string
    return jsonify(error_message)

auth_error = jsonify({'error': 'Authentication failed'})


# functions

#TODO Finish working on authenticating; can we make this a decorator?
'''
Action:
    Validates authorization by checking request headers

Params:

    headers -- The Request headers

Returns:

    BOOL based on whether or not authentication succeeded

'''

def validate(headers):
    try:
        token = headers[auth_key]
        check_token = hives.find_one({id_key: ObjectId(token)})
        if check_token return True else return False

    except KeyError:
        return False

'''
Params:

    options_data -- JSON array of options (options are strings)

Returns:

    options concatenated into a string each joined by a return space

'''

def parse_options(options_data):
    option_string = '\n'.join(options_data)
    return option_string

'''
Params:

numbers -- JSON array of phone numbers to message

Returns:

    a string array of the numbers

'''
def parse_numbers(numbers_data):
    #Drone = [Number:Hive]
    drone = [:]
    for num in number_data:


'''
Sends given message to all numbers via twilio

Params:

    numbers -- an array of phone numbers
    message -- a string message to send to each number


'''

# TODO Ensure all numbers beging with '+'
def send_messages(numbers, message):
    client = TwilioRestClient(account_sid, auth_token)

    # TODO: Does this function send the messages or just prep them?
    for num in numbers:
        message = client.message.create(
    	to = num,
    	from_= "+650825-9655",
    	body = message
        )

def create_drones(numbers):
    pass


@app.route('/')
def welcome():
    pass

def validate_params(param_keys, args):
    # find the missing keys
    missing_params = []
    for key in param_keys:
        if key not in args:
            missing_params.append(key)
    # equivalent:
    missing_params = [key for key in param_keys if key not in args]
    return missing_params

def make_error_response(missing_params):
    # format an error response
    param_string = ','.join(missing_params)
    error_message = {'error': 'You are missing the following parameters: %s' % param_string}
    return jsonify(error_message)

# Get a token from the user
# TODO: Check that the source is an iOS app
# TODO: Set these tokens to expire after a period of time.

@app.route('/hives')
def get_token_for_hive:

    missing = validate_params([hive_name_key, date_created_key], request.args)
    if missing:
        return make_error_response(missing)
    # try:

    hive_name = request.args.get(hive_name_key)
    date_created = request.args.get(date_created_key)
    hive_name_dict = {hive_name_key: hive_name, date_created_key: date_created}
    hive_id = hives.insert_one(hive_name_dict).id

    return hive_id

    # except KeyError:
    #
    #     return param_error([KeyError.message])

'''
Signal Structure:
    * Command: Str
        * options: [Str] -- list of numbered responses
        * expiry: Str -- should be a date string

Assume:
    The following should be handled by the iOS app

    * len(command) -- Less than 140 characters, including all options
    * len(options) -- 0 to 3 max
'''

@app.route('/signals')
def send_signal():
    if not validate(request.headers):
        return auth_error

    try:
        body = request.form
        command = body[command_key]
        options_data = body[options_key]
        options = parse_options(options_data)

        #TODO: Check that the string format of these numbers is okay
        numbers = body[numbers_key]

        message = command + options
        send_messages(numbers, message)


    except KeyError:
        return param_error([param_error_name])

# Relay the messages that come from Twilio here
@app.route('relay')
def relay_response():
    pass


if __name__ == "__main__":
    app.run()
