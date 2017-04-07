class Drone(object):

    def __init__(self, number, hive):
        """Initialize this drone with a number and hive"""
        self.hive = hive
        hased_number = hash(number)
        self.number = hashed_number

    def to_dict(self):
        drone_dict = [:]
        drone_dict['hive'] = self.hive
        drone_dict['number'] = self.number

        return drone_dict


class Hive(object):



'''

*Hive*

ID
QueenID
Name
LastRequest
DroneIds
Responses []

*Drone*
ID
PhoneNum
LastRequest
HiveID

*Relation*
hive_id
drone_id

'''


# great example of how to condense code:

def validate_params(param_keys, args):
    # find the missing keys
    missing_params = []
    for key in param_keys:
        if key not in args:
            missing_params.append(key)
    # equivalent:
    missing_params = [key for key in param_keys if key not in args]
    return missing_params
