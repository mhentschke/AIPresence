
import React, { useState } from 'react';
import "./Modal.css"



const DeviceEditModal = ({data, setData, modal, setModal, deviceCursor, backend, forceUpdate}) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    //const [modal, setModal] = useState(false);
    const [entityId, setEntityId] = useState("entityMock");//data[deviceCursor].entity_id);
    const [name, setName] = useState("NameMock");//data[deviceCursor].name);
    const [entityIDValid, setEntityIDValid] = useState(true);
    const [type, setType] = useState("Tracker");

    const handleSave = () => {
        var device = {};
        var updatedData = JSON.parse(JSON.stringify(data));
        if(deviceCursor == -1){ // Creating
            if (type == "Tracker"){
                backend.CheckEntityId(entityId).then((result) => {
                    if(result){
                        device.entity_id = entityId;
                        device.name = name;
                        setEntityIDValid(true);
                        backend.CreateDevice(device);
                        updatedData.push(device);
                        var tracker = {
                            entity_id: entityId,
                            mobile: true,
                        }
                        backend.CreateTracker(tracker);
                        toggleModal();
                        setData(updatedData);
                        forceUpdate();
                    }
                    else{
                        setEntityIDValid(false);
                        alert("Entity ID does not Exist in Home Assistant")
                    }
                });
            }
            else if (type == "Beacon"){
                device.beacon_id = entityId;
                device.name = name;
                backend.CreateDevice(device);
                updatedData.push(device);
                toggleModal();
                setData(updatedData);
                forceUpdate();
            }
            
        }
        else{ // Updating
            if (type == "Tracker"){
                backend.CheckEntityId(entityId).then((result) => {
                    if(result){
                        setEntityIDValid(true);
                        console.log("Full Data:")
                        console.log(data)
                        device = data[deviceCursor]
                        device.entity_id = entityId;
                        device.name = name; 
                        console.log(data[deviceCursor])
                        backend.UpdateDevice(device);
                        updatedData[deviceCursor] = device;
                        toggleModal();
                        setData(updatedData);
                        forceUpdate();
                    }
                    else{
                        setEntityIDValid(false);
                        alert("Entity ID does not Exist in Home Assistant")
                    }
                });
            }
            else if (type == "Beacon"){
                device = data[deviceCursor]
                device.beacon_id = entityId;
                device.name = name; 
                backend.UpdateDevice(device);
                updatedData[deviceCursor] = device;
                toggleModal();
                setData(updatedData);
                forceUpdate();
            }
        }
        
        
    };

    return ( <>
        {modal && (<div className='modal'>
            <div onClick={toggleModal}className="overlay"></div>
            <div className="modal-content">
                {deviceCursor>=0 && (<h2>Edit Device</h2>)}
                {deviceCursor<0 && (<h2>Add Device</h2>)}
                <label>Identifier {" " + entityIDValid}</label>
                <input
                    type="text"
                    defaultValue={(deviceCursor >= 0)?data[deviceCursor].entity_id:"Identifier"}
                    onChange={
                        (e) => {
                            setEntityId(e.target.value);
                            if (type == "Tracker")
                            {
                                backend.CheckEntityId(e.target.value).then((result) => {
                                    setEntityIDValid(result);
                                });
                            }
                            else if (type == "Beacon")
                            {
                                setEntityIDValid(true);
                            }
                    }}
                />
                <p></p>
                <label>Name</label>
                <input
                    type="text"
                    defaultValue={(deviceCursor >= 0)?data[deviceCursor].name:"Name"}
                    onChange={(e) => setName(e.target.value)}
                />
                <p></p>
                <p>
                    <fieldset>
                        <legend>Select Type Of Device</legend>
                        <div>
                            <input type="radio" id="Tracker" name="type" value="Tracker" onChange={
                                (e) => {
                                    setType(e.target.value);
                                    backend.CheckEntityId(entityId).then((result) => {
                                        setEntityIDValid(result);
                                    });
                                }
                            } defaultChecked={(deviceCursor >= 0)?(data[deviceCursor].type == "Tracker"):false} checked={type=="Tracker"}/>
                            <label for="Tracker">Tracker</label><br/>
                        </div>
                        <div>
                            <input type="radio" id="Beacon" name="type" value="Beacon" onChange={
                                (e) => {
                                    setType(e.target.value);
                                    setEntityIDValid(true);
                                }
                            } defaultChecked={(deviceCursor >= 0)?(data[deviceCursor].type == "Beacon"):false} checked={type=="Beacon"}/>
                            <label for="Beacon">Beacon</label><br/>
                        </div>
                    </fieldset>
                </p>
                <button onClick={handleSave} disabled={!(entityIDValid)
                }>Save</button>
                <button onClick={toggleModal}>Cancel</button>
            </div>
        </div>
        )}
    </>);
};

export default DeviceEditModal;