from flask import Flask, request, jsonify, json
# from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson import ObjectId
from bson import json_util
from twilio.rest import Client

# DB setup
mongo_uri = 'mongodb://<>:<>@ds161890.mlab.com:61890/hivemind'
client = MongoClient(mongo_uri, connect=True)
db = client.get_default_database()

hives = db.hives
drones = db.drones

#security
account_sid = "SECRET"
auth_token = "SO_SECRET"

# Twilio setup
client = Client(account_sid, auth_token)

# initiate app
app = Flask(__name__)

# twilio response constants
reply_key = 'Body'
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
def send_messages(hive_id, message):
    all_drones = list(drones.find({hive_token_key:hive_id}))
    drone = drones.find_one({hive_token_key:hive_id})
    print(hive_id)
    print(drone)
    print(all_drones)

    for drone in all_drones:
        print(drone)
        message = client.api.account.messages.create(
    	to = drone[number_key],
    	from_= '+14156609449',
    	body = message
        )

def create_drones(numbers, hive_id):

    drones_created = []
    for num in numbers:
        if drones.find_one({number_key:num}) is None:
            drone = {}
            drone[number_key] = num
            drone[last_request_key] = 'empty'
            drone[last_response_key] = 'empty'
            drone[hive_token_key] = hive_id

            # insert the drone and get its id
            drone_id = drones.insert_one(drone).inserted_id
            drone[id_key] = str(drone_id)

            # get relevant hive and update its drones property
            hives.update_one({id_key: ObjectId(hive_id)}, { '$addToSet':{drones_key:drone_id} })
            drones_created.append(drone)

        return drones_created


# change the last_request of each drone to most recent message
def update_drones(hive_id, message):
    drones.update_many({hive_token_key: hive_id}, {'$set':{last_request_key: message}})


@app.route('/')
def welcome():
    return jsonify({'greeting': 'This is hivemind'})

# Ensures that all paremeters are there
def validate_params(param_keys, args):
    # find the missing keys
    print('entering validate_params')
    missing_params = [key for key in param_keys if key not in args]
    print(missing_params)
    return missing_params

# Build an error response depending on the missing params
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


@app.route('/signals/<hive_id>', methods = ['POST'])
def send_signal(hive_id=None):
    # check for missing values
    print(request.json)
    missing_body = validate_params([command_key, options_key], request.json)

    if missing_body or hive_id is None:
        return make_error_response(missing_body + hive_token_key)
    print('passed missing check')

    # hive with id not found
    hive = hives.find_one({id_key:ObjectId(hive_id)})
    if not hive:
        return jsonify({'error': 'not a valid hive id'})

    print('checking params')
    #assign desired values to vars
    body = request.json
    command = body[command_key]
    options_data = list(body[soptions_key])
    options = parse_options(options_data)

    #TODO: Check that the string format of these numbers is okay


    message = command + options

    # create new drones if new have appeared, update existing drones
    update_drones(hive_id, message)
    send_messages(hive_id, message)
    print('about to return')
    return jsonify({'ya':'hoo!'})


@app.route('/drones/<hive_id>', methods = ['POST'])
def build_drones(hive_id=None):

    missing_body = validate_params([numbers_key], request.json)
    if missing_body or hive_id is None:
        return make_error_response(missing_body + hive_token_key)

    # hive with id not found
    hive = hives.find_one({id_key:ObjectId(hive_id)})
    if not hive:
        missing_params = jsonify({'error': 'not a valid hive id'})
        missing_params.status_code = 400
        return missing_params

    # create a list of numbers from response body
    numbers = list(request.json[numbers_key])
    drones_created = create_drones(numbers, hive_id)

    return jsonify({'drones':drones_created})




# Relay the messages that come from Twilio here
@app.route('/relay', methods = ['POST'])
def relay_response():

    json = request.form.to_dict()
    missing = validate_params([from_key, reply_key, account_sid_key], json)
    if missing:
        return make_error_response(missing)

    # get the desired params out of message
    from_num = json[from_key]
    reply = json[reply_key]
    account_sid_from_twilio = json[account_sid_key]

    if not account_sid_from_twilio == account_sid:
        print('accountSID mismatch')
        return jsonify({'error': 'this accountSid does not match'})

    #TODO: check that the drones exists before you update it.
        # however drone should technically exist if its hitting this endpoint

    print('looking for drone')
    drone = drones.find_one({number_key:from_num})

    if not drone:
        print('drone with number %s does not belong to any hives') % from_num
        resp = jsonify({'error': 'this drone does not belong to a hive'})
        resp.status_code = 400
        return resp


    drones.update_one({number_key: from_num}, { '$set':{last_response_key:reply}})
    print(from_num)
    return jsonify({'message': 'thanks twilio!'})


@app.route('/hives/<hive_id>', methods = ['GET'])
def pull_request(hive_id=None):

    # hive_id not provided
    print('checking the hive id')
    if not hive_id:
        resp = jsonify({'error': 'this route requires a valid hive_id'})
        resp.status_code = 400
        return resp


    print('finding the hive')
    hive = hives.find_one({id_key:ObjectId(hive_id)})
    # hive with id not found
    if not hive:
        return jsonify({'error': 'not a valid hive id'})

    print('about to encode hive')
    hive = JSONEncoder().encode(hive)
    print('assigning hive id')
    # return the desired hive info
    return jsonify(hive)


if __name__ == "__main__":
    # port = int(os.environ.get('PORT', 5000))
    # app.run(host = '0.0.0.0', port=port)
    app.run()
