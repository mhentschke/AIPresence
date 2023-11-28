from marshmallow import Schema, fields, validate, post_load, pre_dump, pre_load
from classes import Sensor, Binary_Sensor, Smartphone_Tracker, Model, Device
import pandas as pd
import pickle
import config
import os

class Model_Stats_Schema(Schema):
    accuracy = fields.Float()
    model_type = fields.Str()
    classification_report = fields.Dict()

class Model_Schema(Schema):
    trained_model_stats = fields.Nested(Model_Stats_Schema)
    data_path = fields.Str()
    trained_columns = fields.List(fields.Str())

    @post_load
    def make_model(self, data, **kwargs):
        data_path = os.path.join(config.DATA_PATH, data['data_path'])
        data_filepath = Model.get_data_filepath(data_path)
        model_filepath = Model.get_model_filepath(data_path)
        scaler_filepath = Model.get_scaler_filepath(data_path)
        return Model(data['data_path'], 
                     data = pd.read_csv(data_filepath), 
                     trained_model = pickle.load(open(model_filepath, 'rb')),
                     trained_model_stats=data['trained_model_stats'], scaler = pickle.load(open(scaler_filepath, 'rb')),
                     trained_columns = data['trained_columns']
                     )
    
    @pre_dump
    def dump_model(self, model, **kwargs):
        # if folder model.data_path does not exist, create it
        print("Predumping model")
        data_path = os.path.join(config.DATA_PATH, model.data_path)
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        data_filepath = Model.get_data_filepath(data_path)
        model_filepath = Model.get_model_filepath(data_path)
        scaler_filepath = Model.get_scaler_filepath(data_path)
        model.data.to_csv(data_filepath, index=False)
        pickle.dump(model.trained_model, open(model_filepath, 'wb'))
        pickle.dump(model.scaler, open(scaler_filepath, 'wb'))
        #data = {'data_path': model.data_path, 'trained_model_stats': model.trained_model_stats}
        return model
    

class Device_Schema(Schema):
    entity_id = fields.Str(required=False)
    beacon_id = fields.Str(required=False)
    name = fields.Str()
    model = fields.Nested(Model_Schema, allow_none=True)

    @pre_dump
    def dump_device(self, device, **kwargs):
        print("Predumping device:", device)
        return device
    

    #@pre_load
    #def load_device(self, data, **kwargs):
    #    data['model'] = Model_Schema.load(data['model'])

    @post_load
    def make_device(self, data, **kwargs):
        return Device(**data)

class Sensor_Schema(Schema):
    entity_id = fields.Str(required=False)
    mobile = fields.Bool()

    #@post_load
    #def make_sensor(self, data, **kwargs):
    #    return Sensor(**data)

class Binary_Sensor_Schema(Sensor_Schema):

    @post_load
    def make_binary_sensor(self, data, **kwargs):
        return Binary_Sensor(**data)
    
class Smartphone_Tracker_Schema(Sensor_Schema):
    
    @post_load
    def make_smartphone_tracker(self, data, **kwargs):
        return Smartphone_Tracker(**data)

class Room_Schema(Schema):
    id = fields.Str()
    name = fields.Str()
    color = fields.Str()
    
class Trackers_Schema(Schema):
    trackers = fields.Dict(keys = fields.Str(), values = fields.Nested(Smartphone_Tracker_Schema))
    
    @pre_dump
    def dump_trackers(self, trackers, **kwargs):
        return {'trackers': trackers}
    
    @post_load
    def make_trackers(self, data, **kwargs):
        return data['trackers']


class Devices_Schema(Schema):
    devices = fields.Dict(keys = fields.Str(), values = fields.Nested(Device_Schema))

    @pre_dump
    def dump_devices(self, devices, **kwargs):
        return {'devices': devices}
    
    @post_load
    def make_devices(self, data, **kwargs):
        return data['devices']

class Rooms_Schema(Schema):
    rooms = fields.Dict(keys = fields.Str(), values = fields.Nested(Room_Schema))

    @pre_dump
    def dump_rooms(self, rooms, **kwargs):
        return {'rooms': rooms}
    
    @post_load
    def make_rooms(self, data, **kwargs):
        return data['rooms']

class Sensors_Schema(Schema):
    sensors = fields.Dict(keys = fields.Str(), values = fields.Nested(Binary_Sensor_Schema))

    @pre_dump
    def dump_sensors(self, sensors, **kwargs):
        return {'sensors': sensors}
    
    @post_load
    def make_sensors(self, data, **kwargs):
        return data['sensors']

def save_object(obj, filename, schema):
    with open(os.path.join(config.DATA_PATH, filename), 'w') as f:
        to_file = schema.dumps(obj)
        f.write(to_file)

def load_object(filename, schema):
    with open(os.path.join(config.DATA_PATH, filename), 'r') as f:
        result = schema.loads(f.read())
        print("Loading Object from {}, with schema {} resulted in: {}".format(filename, type(schema), result))
        return result
