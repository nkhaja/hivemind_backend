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

# Twilio setup
client = TwilioRestClient(account_sid, auth_token)

#security
account_sid = "secret"

# initiate app
app = Flask(__name__)

# twilio response constants
body_key = 'body'
account_sid_key = 'AccountSid'
from_key = 'From'

# hive keys
hive_name_key = 'hive_name'
hive_token_key = 'hive_token'
date_created_key = 'date_created'

# drone keys
number_key = 'number'

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

def authenticate(headers):
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
# def parse_numbers(numbers_data):
#     #Drone = [Number:Hive]
#     drone = [:]
#     for num in number_data:


'''
Sends given message to all numbers via twilio

Params:

    numbers -- an array of phone numbers
    message -- a string message to send to each number


'''

# TODO Ensure all numbers beging with '+'
def send_messages(numbers, message):

    # TODO: Does this function send the messages or just prep them?
    for num in numbers:
        message = client.message.create(
    	to = num,
    	from_= "+650825-9655",
    	body = message
        )

def create_drones(numbers, hive_id):
    drones = []
    for num in numbers:
        drone = {:}
        drone[numbers_key] = num
        drone[last_request_key] = 'empty'
        drone[hive_token_key] = hive_id

        # insert the drone and get its id
        drone_id = drones.insert_one(drone)

        #get relevant hive and update its drones property
        hives.find_one({id_key: ObjectId(hive_id)})

        

        allTasks.update_one({selfId:ObjectId(someTaskId)}, {'$set':newTask})



@app.route('/')
def welcome():
    pass

def validate_params(param_keys, args):
    # find the missing keys
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

    hive_name = request.args.get(hive_name_key)
    date_created = request.args.get(date_created_key)
    hive_name_dict = {hive_name_key: hive_name, date_created_key: date_created}
    hive_id = hives.insert_one(hive_name_dict).id

    # add the token to the dict if accepted
    hive_name_dict[hive_token_key] = hive_id

    return jsonify(hive_name_dict)

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

#TODO: Authentication on this route
@app.route('/signals')
def send_signal():

    missing = validate_params([hive_name_key, date_created_key], request.args)
    if missing:
        return make_error_response(missing)


    body = request.form
    command = body[command_key]
    options_data = body[options_key]
    options = parse_options(options_data)

    #TODO: Check that the string format of these numbers is okay
    numbers = body[numbers_key]

    message = command + options
    update_drones(numbers, message)
    send_messages(numbers, message)




# Relay the messages that come from Twilio here
@app.route('relay')
def relay_response():
    if not authenticate(request.headers):
        return auth_error

    # get the desired params from the twilio response
    missing = validate_params([body_key, date_created_key], request.args)
    body = request.args.get(body_key)
    account_sid = request.args.get(account_sid_key)




if __name__ == "__main__":
    app.run()
