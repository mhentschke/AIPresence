from homeassistant_api import Client
from homeassistant_api.errors import EndpointNotFoundError
from flask import Flask, request
import uuid
import os
import api_schemas
import storage
from classes import *
from marshmallow import ValidationError
import json
from dotenv import load_dotenv

load_dotenv()

HA_URL = os.environ["HA_URL"]
HA_TOKEN = os.environ["HA_TOKEN"]

app = Flask(__name__)

def get_data_from_trackers_and_sensors():
    data = {}

    for entity_id, tracker in (trackers | sensors).items():
        temp_data = tracker.get_data()
        # if data is a dictionary:
        if isinstance(temp_data, dict):
            temp_data = {entity_id + "-" + str(key): val for key, val in temp_data.items()}
        else:
            temp_data = { entity_id : temp_data }
        data.update(temp_data)
    return data

trackers = {}
devices = {}
rooms = {}
sensors = {}

def stringify_dict_items(dict, schema):
    list = []
    for key, value in dict.items():
        #dict[key] = schema.dump(value)
        item = schema.dump(value)
        item['id'] = key
        list.append(item)
    return list


with Client(
    HA_URL,
    HA_TOKEN,
    cache_session = False
) as client:
    
    @app.route('/trackers')
    def get_trackers():

        return (stringify_dict_items(trackers, api_schemas.Smartphone_Tracker_Schema()), 200)

    @app.route("/trackers/<entity_id>", methods=['POST', 'PUT'])
    def create_tracker(entity_id):
        mobile = request.json["mobile"] if "mobile" in request.json else False
        whitelist = request.json["whitelist"] if "whitelist" in request.json else False
        blacklist = request.json["blacklist"] if "blacklist" in request.json else False
        if request.method == 'POST':
            if entity_id in trackers:
                return ("Already exists. To overwrite, please use the PUT method", 409)
            mobile = request.json["mobile"] if "mobile" in request.json else False
        else:
            if entity_id not in trackers:
                return ("Entity not found", 404)    
        trackers[entity_id] = Smartphone_Tracker(entity_id, ha_client=client, mobile = mobile, whitelist = whitelist, blacklist = blacklist)
        storage.save_object(trackers, "trackers.json", storage.Trackers_Schema())
        return ("Success")

    @app.route("/trackers/<entity_id>", methods=['DELETE'])
    def delete_tracker(entity_id):
        if entity_id in trackers:
            del trackers[entity_id]
            storage.save_object(trackers, "trackers.json", storage.Trackers_Schema())
            return ("Success")
        else:
            return ("Entity not found", 404)
    
    @app.route("/sensors")
    def get_sensors():
        return (stringify_dict_items(sensors, api_schemas.Binary_Sensor_Schema()), 200)
    
    @app.route("/sensors/<entity_id>", methods=['POST', 'PUT'])
    def create_sensor(entity_id):
        if request.method == 'POST':
            if entity_id in sensors:
                return ("Already exists. To overwrite, please use the PUT method", 409)
        sensors[entity_id] = Binary_Sensor(entity_id, ha_client=client)
        storage.save_object(sensors, "sensors.json", storage.Sensors_Schema())
        return ("Success")
        
    @app.route("/devices", methods = ['GET'])
    def get_devices():
        return (stringify_dict_items(devices, api_schemas.Device_Schema()), 200)
    
    @app.route("/devices/<device_id>/location", methods = ['GET'])
    def get_device_location(device_id):
        if device_id in devices:
            loc = devices[device_id].get_location()
            if loc is None:
                return ("Device is not trained", 400)
            else:
                #print("loc", loc)
                return (loc, 200)
        else:
            return ("Device not found", 404)
        
    @app.route("/devices/location", methods = ['GET'])
    def get_devices_location():
        device_locations = {}
        for device_id, device in devices.items():
            response_dict = device.get_location()
            device_locations[device_id] = response_dict
        return (device_locations, 200)


    
    def create_or_update_device(device_id, request, model = None):
        if "entity_id" in request.json:
            devices[device_id] = Device(request.json["name"], entity_id=request.json["entity_id"], model = model, data_gatherer = get_data_from_trackers_and_sensors)
        elif "beacon_id" in request.json:
            devices[device_id] = Device(request.json["name"], beacon_id=request.json["beacon_id"], model = model, data_gatherer = get_data_from_trackers_and_sensors)
        else:
            raise ValueError("Exactly one of entity_id or beacon_id must be specified")
        storage.save_object(devices, "devices.json", storage.Devices_Schema())
        return ("Success")

    @app.route("/devices", methods=['POST'])
    def create_device():
        device_id = str(uuid.uuid4())
        try:
            create_or_update_device(device_id, request)
            return (device_id)
        except ValueError as e:
            return (str(e), 400)

    @app.route("/devices/<device_id>", methods=['PUT'])
    def create_device_id(device_id):
        model = None
        if device_id in devices:
            model = devices[device_id].model
        try:
            create_or_update_device(device_id, request, model)
            return ("Success")
        except ValueError as e:
            return (str(e), 400)
    
    @app.route("/devices/<device_id>", methods=["GET"])
    def get_device(device_id):
        if device_id in devices:
            return (devices[device_id])
        else:
            return ("Device not found", 404)
    
    @app.route("/devices/<device_id>", methods=["DELETE"])
    def delete_device(device_id):
        if device_id in devices:
            del devices[device_id]
            storage.save_object(devices, "devices.json", storage.Devices_Schema())
            return ("Success")
        else:
            return ("Device not found", 404)

    @app.route("/devices/<device_id>/model/start_training", methods=["POST"])
    def start_training(device_id):
        try:
            room = request.json["room"]
            append = request.json["append"] if "append" in request.json else False
            if device_id not in devices:
                return ("Device not found", 404)
            if room not in rooms:
                return ("Room not found", 404)
            devices[device_id].start_training(room, append = append)
            return ("Success")
        except KeyError as e:
            return (str(e), 400)

    @app.route("/devices/<device_id>/model/stop_training")
    def stop_training(device_id):
        if devices[device_id].training:
            devices[device_id].stop_training()
            storage.save_object(devices, "devices.json", storage.Devices_Schema())
            return ("Success")
        else:
            return ("Device is not training", 400)
    
    @app.route("/devices/<device_id>/model/retrain", methods=["POST"])
    def retrain(device_id):
        if not devices[device_id].training:
            devices[device_id].retrain()
            return ("Success")
        else:
            return ("Device is already training", 400)
    
    @app.route("/devices/<device_id>/model/cancel_training")
    def cancel_training(device_id):
        if devices[device_id].training:
            devices[device_id].cancel_training()
            return ("Success")
        else:
            return ("Device is not training", 400)

    @app.route("/devices/<device_id>/model/set_room/<room_id>", methods=["POST"])
    def set_room(device_id, room_id):
        if device_id in devices:
            if room_id in rooms:
                if devices[device_id].model is not None:
                    devices[device_id].model.set_room(room_id)
                    return ("Success")
                else:
                    return ("Device is not training", 400)
            else:
                return ("Room not found", 404)
        else:
            return ("Device not found", 404)
    
    @app.route("/devices/<device_id>/model" , methods=["GET"])
    def get_model(device_id):
        return devices[device_id].model.get_info()
    
    @app.route("/devices/<device_id>/model/training_progress" , methods=["GET"])
    def get_training_progress(device_id):
        if device_id in devices:
            progress = devices[device_id].model.get_training_progress()
            if progress == {}: # model is not training
                return ("Device is not training", 400)
            else:
                encoded_progress = json.dumps(progress)
                print (encoded_progress)
                return(encoded_progress, 200)
        else:
            return ("Device not found", 404)

    @app.route("/rooms/<room_id>", methods=["PUT", "DELETE"])
    def add_delete_room(room_id):
        if request.method == "PUT":
            name = request.json["name"]
            color = request.json["color"]
            rooms[room_id] = Room(room_id, name, color)
            storage.save_object(rooms, "rooms.json", storage.Rooms_Schema())
            return ("Success")
        else:
            if room_id in rooms:
                del rooms[room_id]
                storage.save_object(rooms, "rooms.json", storage.Rooms_Schema())
                return ("Success")
            else:
                return("Room not found", 404)
    
    @app.route("/rooms/<room_id>", methods=["GET"])
    def get_room(room_id):
        if room_id in rooms:
            return(rooms[room_id])
        else:
            return("Room not found", 404)
    
    @app.route("/rooms", methods=["POST"])
    def create_room():
        room_id = str(uuid.uuid4())
        try:
            name = request.json["name"]
            color = request.json["color"]
            rooms[room_id] = Room(room_id, name, color)
            storage.save_object(rooms, "rooms.json", storage.Rooms_Schema())
            return (room_id)
        except KeyError as e:
            return (str(e), 400)
        
    
    @app.route("/rooms", methods=["GET"])
    def get_rooms():
        return(stringify_dict_items(rooms, api_schemas.Room_Schema()), 200)
    
    @app.route("/device/check_entity_id/<entity_id>", methods=["GET"])
    def check_entity_id(entity_id):
        try:
            client.get_entity(entity_id=entity_id)
            return ("Success")
        except EndpointNotFoundError:
            return ("Entity not found", 404)



    if __name__ == "__main__":
        try:
            trackers = storage.load_object("trackers.json", storage.Trackers_Schema())
            for tracker in trackers.values():
                tracker.ha_client = client
        except FileNotFoundError:
            print("Trackers file not found, starting from scratch")
        except ValidationError as e:
            print("A validation error occurred while loading trackers: " + str(e), "File will be overwritten")
        try:
            devices = storage.load_object("devices.json", storage.Devices_Schema())
            for device in devices.values():
                device.data_gatherer = get_data_from_trackers_and_sensors
                device.model.data_gatherer = get_data_from_trackers_and_sensors
        except FileNotFoundError as e:
            print("Devices file not found, {}, starting from scratch".format(e))
        except ValidationError as e:
            print("A validation error occurred while loading devices: " + str(e), "File will be overwritten")
        try:
            rooms = storage.load_object("rooms.json", storage.Rooms_Schema())
        except FileNotFoundError:
            print("Rooms file not found, starting from scratch")
        except ValidationError as e:
            print("A validation error occurred while loading rooms: " + str(e), "File will be overwritten")
        try:
            sensors = storage.load_object("sensors.json", storage.Sensors_Schema())
            for sensor in sensors.values():
                sensor.ha_client = client
        except FileNotFoundError:
            print("Sensors file not found, starting from scratch")
        except ValidationError as e:
            print("A validation error occurred while loading sensors: " + str(e), "File will be overwritten")
        
        app.run(debug=True)
        
