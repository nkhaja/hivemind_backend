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
    
