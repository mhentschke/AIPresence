import React, { useState, useEffect } from 'react';
import "./Modal.css"
import EntityPicker from './EntityPicker';



const DeviceEditModal = ({data, setData, modal, setModal, deviceCursor, backend}) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    const [entityId, setEntityId] = useState("");
    const [name, setName] = useState("");
    const [entityIDValid, setEntityIDValid] = useState(true);
    const [type, setType] = useState("Tracker");

    // Initialize state from selected device when editing, reset to defaults when creating
    useEffect(() => {
        if (modal && deviceCursor >= 0 && data[deviceCursor]) {
            const device = data[deviceCursor];
            setName(device.name || "");
            setEntityId(device.identifier || device.entity_id || device.beacon_id || "");
            setType(device.type || "Tracker");
            setEntityIDValid(true);
        } else if (modal && deviceCursor === -1) {
            setName("");
            setEntityId("");
            setType("Tracker");
            setEntityIDValid(true);
        }
    }, [modal, deviceCursor, data]);

    const handleSave = async () => {
        let device = {};
        const updatedData = JSON.parse(JSON.stringify(data));
        if(deviceCursor === -1){ // Creating
            if (type === "Tracker"){
                try {
                    const exists = await backend.CheckEntityId(entityId);
                    if(exists){
                        device.entity_id = entityId;
                        device.name = name;
                        setEntityIDValid(true);
                        const result = await backend.CreateDevice(device);
                        device.id = result.id;
                        const tracker = {
                            entity_id: entityId,
                            mobile: true,
                        };
                        await backend.CreateTracker(tracker);
                        updatedData.push(device);
                        toggleModal();
                        setData(updatedData);
                    } else {
                        setEntityIDValid(false);
                        alert("Entity ID does not Exist in Home Assistant");
                    }
                } catch (err) {
                    console.error("Error creating tracker device:", err);
                }
            }
            else if (type === "Beacon"){
                device.beacon_id = entityId;
                device.name = name;
                try {
                    const result = await backend.CreateDevice(device);
                    device.id = result.id;
                    updatedData.push(device);
                    toggleModal();
                    setData(updatedData);
                } catch (err) {
                    console.error("Error creating beacon device:", err);
                }
            }
        }
        else{ // Updating
            if (type === "Tracker"){
                try {
                    const exists = await backend.CheckEntityId(entityId);
                    if(exists){
                        setEntityIDValid(true);
                        device = data[deviceCursor];
                        device.entity_id = entityId;
                        device.name = name;
                        await backend.UpdateDevice(device);
                        updatedData[deviceCursor] = device;
                        toggleModal();
                        setData(updatedData);
                    } else {
                        setEntityIDValid(false);
                        alert("Entity ID does not Exist in Home Assistant");
                    }
                } catch (err) {
                    console.error("Error updating tracker device:", err);
                }
            }
            else if (type === "Beacon"){
                device = data[deviceCursor];
                device.beacon_id = entityId;
                device.name = name;
                try {
                    await backend.UpdateDevice(device);
                    updatedData[deviceCursor] = device;
                    toggleModal();
                    setData(updatedData);
                } catch (err) {
                    console.error("Error updating beacon device:", err);
                }
            }
        }
    };

    return ( <>
        {modal && (<div className='modal'>
            <div onClick={toggleModal}className="overlay"></div>
            <div className="modal-content">
                {deviceCursor>=0 && (<h2>Edit Device</h2>)}
                {deviceCursor<0 && (<h2>Add Device</h2>)}
                {type === "Tracker" ? (
                    <EntityPicker
                        domain="device_tracker"
                        value={entityId}
                        onChange={(val) => {
                            setEntityId(val);
                            backend.CheckEntityId(val).then((result) => {
                                setEntityIDValid(result);
                            });
                        }}
                        label={"Identifier " + entityIDValid}
                    />
                ) : (
                    <>
                        <label>{"Identifier " + entityIDValid}</label>
                        <input
                            type="text"
                            value={entityId}
                            onChange={(e) => {
                                setEntityId(e.target.value);
                                setEntityIDValid(true);
                            }}
                        />
                    </>
                )}
                <p></p>
                <label>Name</label>
                <input
                    type="text"
                    value={name}
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
                            } checked={type==="Tracker"}/>
                            <label htmlFor="Tracker">Tracker</label><br/>
                        </div>
                        <div>
                            <input type="radio" id="Beacon" name="type" value="Beacon" onChange={
                                (e) => {
                                    setType(e.target.value);
                                    setEntityIDValid(true);
                                }
                            } checked={type==="Beacon"}/>
                            <label htmlFor="Beacon">Beacon</label><br/>
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
