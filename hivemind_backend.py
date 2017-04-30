from flask import Flask, request, jsonify, json
# from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson import ObjectId
from bson import json_util
from twilio.rest import Client
import re

#TODO: Change documentation to official python documentation

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

## auth keys
auth_key = 'auth'
id_key = '_id'


# setup for jsonEncoding
import json
from bson import ObjectId

#TODO: Add to another file
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


### functions

'''
Params:

    options_data -- JSON array of options (options are strings)

Returns:

    options concatenated into a string each joined by a return space

'''

def parse_options(options_data):
    # enumerate the options
    for i in range(len(options_data)):
        options_data[i] = str(i + 1)+'.'+ options_data[i]

    option_string = '\n'.join(options_data)
    return option_string


'''
Sends given message to all numbers via twilio

Params:

    numbers -- an array of phone numbers
    message -- a string message to send to each number

'''
# TODO Ensure all numbers beging with '+'
# TODO Put the phone number into constant
def send_messages(hive_id, message):
    all_drones = list(drones.find({hive_token_key: hive_id}))

    print('going to check the drones')
    print(all_drones)
    numbers_messaged = []
    for drone in all_drones:
        client.api.account.messages.create(
    	to = drone[number_key],
    	from_= '+14156609449',
    	body = message
        )
        print('a message has been sent')
'''
Stores a drone document into the hive corresponding to given id.

Params:
    numbers - an array of phone numbers
    hive_id - The string id of the hive we want to assign these numbers to

Returns:
    An array of drones (each represented as a dicts)

'''
def create_drones(numbers, hive_id):

    #TODO: Update the regex to cut off +1
    drones_created = []
    regex = re.compile('-| |\\(|\\)')
    print('all_numbers')
    print(numbers)
    for num in numbers:
        num = regex.sub('', num).replace(u'\xa0', u' ').replace(' ', '')
        print(num)

        if drones.find_one({hive_token_key: hive_id, number_key: num }) is None:
            drone = {}

            # assign properties
            drone[number_key] = num
            drone[last_request_key] = 'empty'
            drone[last_response_key] = 0
            drone[hive_token_key] = hive_id

            # insert the drone and get its id
            drone_id = drones.insert_one(drone).inserted_id
            # drone_to_store = {id_key:drone_id}

            # json returned shouldn't contain and objectId
            drone[id_key] = str(drone_id)

            # get relevant hive and update it's drones property
            hives.update_one({id_key: ObjectId(hive_id)}, { '$addToSet': {drones_key: drone_id} })
            drones_created.append(drone)
            print('added the following drone')

    return drones_created


'''
Changes the last_request of each drone to most recent message

Params:
    hive_id - The message will be sent to all drones in hive with this id
    message - a string representing the message to be sent to all drones in hive
'''

def update_drones(hive_id, message):
    drones.update_many({hive_token_key: hive_id}, {'$set': {last_request_key: message}})


'''
Determines if specified params are missing, and returns of list of missing params

Params:
    param_keys - a list of every parameter that needs to be present
    args - a dictionary that we are checking for the desired param_keys

Returns:
    an array of any parameters that are missing
'''

def validate_params(param_keys, args):
    # find the missing keys
    missing_params = [key for key in param_keys if key not in args]
    return missing_params

'''
Takes an array of params and returns an error message requesting them

Params:
    missing_params: a string list representing missing params

Returns:
    a jsonified error message specifying the parameters that are missing
'''

def make_error_response(missing_params):
    # format an error response
    param_string = ','.join(missing_params)
    error_message = {'error': 'You are missing the following parameters: %s' % param_string}
    error_message = jsonify(error_message)
    error_message.status_code = 400
    return error_message


def delete_hive(hive_id):
    drones.remove({hive_token_key: hive_id})
    hives.remove({hive_token_key: hive_id})

def delete_drones_by_number(hive_id, numbers):
    hive_query = {hive_token_key: ObjectId(hive_id)}

    drones_deleted = []
    hive = hives.find_one({id_key:ObjectId(hive_id)})
    all_drones = list(hive[drones_key])
    for num in numbers:
        #check that this hive has the drone
        find_drone_query = {number_key: num, hive_token_key: hive_id}
        drone = drones.find_one(find_drone_query)

        #TODO: Fix this terrible replacement
        if drone is not None:
            for drone_id in all_drones:
                if str(drone_id) == str(drone[id_key]):
                    print('removing from all drones')
                    all_drones.remove(drone_id)
                    break

            '''The strategy below failed, more efficient see if can fix later'''
            #build query for this drone
            # drone_object_id = str(drone[id_key])

            # drone_query = { drones_key: {id_key: drone_object_id}}

            # pull the drone out of this hive
            # update_result = hives.update_one(hive_query, {'$pull': drone_query})

            ## end of old strategy

            drones.remove(find_drone_query)
            drones_deleted.append(drone)


    the_update = hives.update_one({id_key:ObjectId(hive_id)}, {'$set': {drones_key:all_drones}})
    return drones_deleted

# ROUTES

# TODO make a landing page for the app here
@app.route('/')
def welcome():
    return jsonify({'greeting': 'This is hivemind'})


# Get a token from the user
# TODO: Check that the source is an iOS app
# TODO: Set these tokens to expire after a period of time.

# POST a hive name, responds with a hive object containing a token
# token must be used to access hive functions on all other routes
@app.route('/hives', methods = ['POST'])
def get_token_for_hive():

    if request.method == 'POST':
        missing = validate_params([hive_name_key, date_created_key], request.json)
        if missing:
            return make_error_response(missing)

        hive_name = request.json.get(hive_name_key)
        date_created = request.json.get(date_created_key)

        print(hive_name)
        print(request.json[hive_name_key])

        # Create a new hive object dictionary, store it
        hive_name_dict = {
            hive_name_key: hive_name,
            date_created_key: date_created,
            drones_key: []
        }

        hive_id = hives.insert_one(hive_name_dict).inserted_id

        # convert the ObjectID mongo object to a string
        hive_name_dict[id_key] = str(hive_id)

        return jsonify(hive_name_dict)


# receives a list of numbers and adds them as drones to the hive with hive_id
@app.route('/drones/<hive_id>', methods = ['POST', 'DELETE'])
def build_drones(hive_id=None):

    missing_body = validate_params([numbers_key], request.json)
    if missing_body or hive_id is None:
        return make_error_response(missing_body + hive_token_key)

    # hive with id not found
    hive = hives.find_one({id_key: ObjectId(hive_id)})
    if hive is None:
        missing_id = jsonify({'error': 'not a valid hive id'})
        missing_id.status_code = 400
        return missing_id

    numbers = list(request.json[numbers_key])
    if request.method == 'POST':
        # create a list of numbers from response body
        drones_created = create_drones(numbers, hive_id)

        return jsonify({'drones': drones_created})


    elif request.method == 'DELETE':
        drones_deleted = delete_drones_by_number(hive_id, numbers)
        return JSONEncoder().encode(drones_deleted)


'''
Signal Structure:
    * Command: Str
        * options: [Str] -- list of numbered responses
        * expiry: Str -- should be a date string

Assume:
    The following should be handled by the iOS app

    * len(command) -- Less than 140 characters, including all options
    * len(options) -- 1 to 3
'''

# A message sent to this endpoint is relayed to all drones in the hive with given id
@app.route('/signals/<hive_id>', methods = ['POST'])
def send_signal(hive_id=None):

    print('hitting the top')
    missing_body = validate_params([command_key, options_key], request.json)
    if missing_body or hive_id is None:
        return make_error_response(missing_body + hive_token_key)

    print('made sure nothing was missing')

    # hive with id not found
    hive = hives.find_one({id_key: ObjectId(hive_id)})
    if not hive:
        return jsonify({'error': 'not a valid hive id'})

    print('was able to find the hive')
    #assign desired values to vars
    body = request.json
    command = body[command_key]
    options_data = list(body[options_key])
    options = parse_options(options_data)

    #TODO: Check that the string format of these numbers is okay

    message = command +'\n'+ options

    # create new drones if new have appeared, update existing drones
    print('updating the drones')
    update_drones(hive_id, message)
    print('get ready to send the message!')
    send_messages(hive_id, message)

    print(message)
    return jsonify({'message_sent': message})




# Relay the messages that come from Twilio here
@app.route('/relay', methods = ['POST'])
def relay_response():

    json = request.form.to_dict()
    missing = validate_params([from_key, reply_key, account_sid_key], json)
    if missing:
        return make_error_response(missing)

    # get the desired params out of message
    from_num = json[from_key]
    from_num = from_num[-10:]
    reply = json[reply_key]
    account_sid_from_twilio = json[account_sid_key]

    # Account sid mismatch
    if not account_sid_from_twilio == account_sid:
        print('accountSID mismatch')
        resp = jsonify({'error': 'this accountSid does not match'})
        resp.status_code = 400
        return resp

    #TODO: check that the drones exists before you update it.
        # however drone should technically exist if its hitting this endpoint

    # Make sure desired drone exists
    drone = drones.find_one({number_key: from_num})
    if not drone:
        print('drone with number %s does not belong to any hives') % from_num
        resp = jsonify({'error': 'this drone does not belong to a hive'})
        resp.status_code = 400
        return resp

    #TODO error handle single digits greater than 3
    if len(reply) < 2 and reply.isdigit():
        print('good reply')

    else:
        print('bad reply')
        message = 'Please respond with a single digit corresponding to one of the options given'
        client.api.account.messages.create(
    	to = from_num,
    	from_= '+14156609449',
    	body = message
        )

        #update drone with appropriate message
        drones.update({number_key: from_num},
                      { '$set': {last_response_key: reply}},
                        multi = True)
    #update the last_response field of drones with response sent here
    return jsonify({'message': 'thanks twilio!'})

# GET a json of hive with hive_id, contains all drones and their responses
@app.route('/hives/<hive_id>', methods = ['GET', 'DELETE'])
def pull_request(hive_id=None):

    # hive_id not provided
    if not hive_id:
        resp = jsonify({'error': 'this route requires a valid hive_id'})
        resp.status_code = 400
        return resp

    hive = hives.find_one({id_key: ObjectId(hive_id)})

    # hive with id not found
    if not hive:
        return jsonify({'error': 'not a valid hive id: {}'.format(hive_id)})

    drones_for_hive = []
    for drone_id in hive[drones_key]:
        drone = drones.find_one({id_key: ObjectId(drone_id)})
        drones_for_hive.append(drone)

    if request.method == 'DELETE':
        delete_hive(hive_id)

    # put the drone into the hive
    hive[drones_key] = drones_for_hive

    # encode to remove any Mongo ObjectID's
    hive_string = JSONEncoder().encode(hive)

    return hive_string


if __name__ == "__main__":
    app.run(debug=True)
