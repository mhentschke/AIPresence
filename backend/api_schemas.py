from marshmallow import Schema, fields, validate, post_load
from classes import Sensor, Binary_Sensor, Smartphone_Tracker

class Model_Stats_Schema(Schema):
    accuracy = fields.Float()
    model_type = fields.Str()
    classification_report = fields.Dict()

class Model_Schema(Schema):
    trained_model_stats = fields.Nested(Model_Stats_Schema)

class Device_Schema(Schema):
    entity_id = fields.Str(required=False)
    beacon_id = fields.Str(required=False)
    name = fields.Str()
    model = fields.Nested(Model_Schema)

class Sensor_Schema(Schema):
    entity_id = fields.Str(required=False)
    mobile = fields.Bool()

    @post_load
    def make_sensor(self, data, **kwargs):
        return Sensor(**data)

class Binary_Sensor_Schema(Sensor_Schema):

    @post_load
    def make_binary_sensor(self, data, **kwargs):
        return Binary_Sensor(**data)
    
class Smartphone_Tracker_Schema(Sensor_Schema):
    whitelist = fields.Bool()
    blacklist = fields.Bool()
    
    @post_load
    def make_smartphone_tracker(self, data, **kwargs):
        return Smartphone_Tracker(**data)

class Room_Schema(Schema):
    id = fields.Str()
    name = fields.Str()
    color = fields.Str()

    