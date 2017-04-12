from flask import Flask, request, jsonify, json
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson import ObjectId
from bson import json_util
from twilio.rest import Client

# DB setup
client = MongoClient()
db = client.database

hives = db.hives
drones = db.drones

#security



# Twilio setup
client = Client(account_sid, auth_token)


# initiate app
app = Flask(__name__)

# twilio response constants
body_key = 'body'
account_sid_key = 'AccountSid'
from_key = 'From'

# hive keys
hive_name_key = 'hive_name'
hive_token_key = 'hive_token'
drones_key = 'drones'
date_created_key = 'date_created'

# drone keys
number_key = 'number'
last_request_key = 'last_request'
last_response_key = 'last_response'

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

auth_error = {'error': 'Authentication failed'}

def param_error(missing_params):
    param_string = ','.join(missing_params)
    error_message = {'error':'You are missing the following parameters: %s' } % param_string
    return jsonify(error_message)


import json
from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


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
        return check_token is not None

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

        message = client.api.account.messages.create(
    	to = num,
    	from_= '+14156609449',
    	body = message
        )

def create_drones(numbers, hive_id):
    drones.drop()
    print(len(numbers))
    for num in numbers:
        if drones.find_one({number_key:num}) is None:
            drone = {}
            drone[numbers_key] = num
            drone[last_request_key] = 'empty'
            drone[last_response_key] = 'empty'
            drone[hive_token_key] = hive_id

            print('checkpoint A')

            # insert the drone and get its id
            drone_id = drones.insert_one(drone).inserted_id

            print('checkpoint B')

            # get relevant hive and update its drones property
            hives.update_one({id_key: ObjectId(hive_id)}, { '$addToSet':{drones_key:drone_id} })

            print('checkpoint C')


# change the last_request of each drone to most recent message
def update_drones(numbers, message):
    for num in numbers:
        drones.update_one({number_key: num}, {'$set':{last_request_key: message}})


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

@app.route('/hives', methods = ['POST'])
def get_token_for_hive():

    if request.method == 'POST':
        missing = validate_params([hive_name_key, date_created_key], request.args)
        if missing:
            return make_error_response(missing)

        hive_name = request.args.get(hive_name_key)
        date_created = request.args.get(date_created_key)


        hive_name_dict = {hive_name_key: hive_name, date_created_key: date_created, drones_key: []}

        hive_id = hives.insert_one(hive_name_dict).inserted_id
        hive_name_dict[id_key] = str(hive_id)

        # add the token to the dict if accepted

        return jsonify(hive_name_dict)
    else:
        return jsonify({'error': 'This method is not supported'})

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
@app.route('/signals', methods = ['POST'])
def send_signal():

    print(request.json)
    print(request.data)
    # check for missing values
    missing_body = validate_params([command_key, options_key], request.json)
    missing_params = validate_params([hive_token_key], request.args)
    if missing_body or missing_params:
        return make_error_response(missing_body + missing_params)

    #assign desired values to vars
    body = request.json
    command = body[command_key]
    options_data = list(body[options_key])
    options = parse_options(options_data)
    hive_id = request.args.get(hive_token_key)

    #TODO: Check that the string format of these numbers is okay

    numbers = list(body[numbers_key])
    message = command + options

    # create new drones if new have appeared, update existing drones
    create_drones(numbers, hive_id)
    update_drones(numbers, message)
    send_messages(numbers, message)
    return jsonify({'ya':'hoo!'})




# Relay the messages that come from Twilio here
@app.route('/relay')
def relay_response():
    # if not authenticate(request.headers):
    #     return auth_error

    # get the desired params from the twilio response
    missing = validate_params([from_key, body_key, account_sid_key], request.args)
    if missing:
        return make_error_response(missing)

    # get the desired params out of message
    from_num = request.args.get(from_key)
    body = request.args.get(body_key)
    account_sid_from_twilio = request.args.get(account_sid_key)

    if not account_sid_from_twilio == account_sid:
        return jsonify({'error': 'this accountSid does not match'})

    #TODO: check that the drones exists before you update it.
        # however this should exist if its hitting this endpoint
    drones.update_one({'number_key': from_num}, { '$set':{last_response_key:body}})


@app.route('/hives/<hive_id>')
def pull_request(hive_id=None):

    # hive_id not provided
    if not hive_id:
        return jsonify({'error': 'this route requires a valid hive_id'})

    hive = hives.find_one({id_key:ObjectId(hive_id)})
    # hive with id not found
    if not hive:
        return jsonify({'error': 'not a valid hive id'})

    # return the desired hive info
    return jsonify(hive)



if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host = '0.0.0.0', port=port)
