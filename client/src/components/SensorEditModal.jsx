import React, { useState, useEffect } from 'react';
import "./Modal.css"
import EntityPicker from './EntityPicker';



const SensorEditModal = ({data, setData, modal, setModal, sensorCursor, backend, forceUpdate}) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    const [entityId, setEntityId] = useState("");
    const [entityIDValid, setEntityIDValid] = useState(false);

    // Initialize state from selected sensor when editing, reset when creating
    useEffect(() => {
        if (modal && sensorCursor >= 0 && data[sensorCursor]) {
            setEntityId(data[sensorCursor].entity_id || "");
            setEntityIDValid(true);
        } else if (modal && sensorCursor === -1) {
            setEntityId("");
            setEntityIDValid(false);
        }
    }, [modal, sensorCursor, data]);

    const handleSave = async () => {
        let sensor = {};
        const updatedData = JSON.parse(JSON.stringify(data));
        if(sensorCursor === -1){ // Creating
            try {
                const exists = await backend.CheckEntityId(entityId);
                if(exists){
                    sensor.entity_id = entityId;
                    setEntityIDValid(true);
                    const result = await backend.CreateSensor(sensor);
                    sensor.id = result.id;
                    updatedData.push(sensor);
                    toggleModal();
                    setData(updatedData);
                    forceUpdate();
                } else {
                    setEntityIDValid(false);
                    alert("Entity ID does not Exist in Home Assistant");
                }
            } catch (err) {
                console.error("Error creating sensor:", err);
            }
        }
        else{ // Updating
            try {
                const exists = await backend.CheckEntityId(entityId);
                if(exists){
                    setEntityIDValid(true);
                    sensor = data[sensorCursor];
                    sensor.entity_id = entityId;
                    await backend.UpdateSensor(sensor);
                    updatedData[sensorCursor] = sensor;
                    toggleModal();
                    setData(updatedData);
                    forceUpdate();
                } else {
                    setEntityIDValid(false);
                    alert("Entity ID does not Exist in Home Assistant");
                }
            } catch (err) {
                console.error("Error updating sensor:", err);
            }
        }
    };

    return ( <>
        {modal && (<div className='modal'>
            <div onClick={toggleModal}className="overlay"></div>
            <div className="modal-content">
                {sensorCursor>=0 && (<h2>Edit Sensor</h2>)}
                {sensorCursor<0 && (<h2>Add Sensor</h2>)}
                <EntityPicker
                    domain="binary_sensor"
                    value={entityId}
                    onChange={(val) => {
                        setEntityId(val);
                        backend.CheckEntityId(val).then((result) => {
                            setEntityIDValid(result);
                        });
                    }}
                    label={"Entity ID " + entityIDValid}
                />
                <p></p>
                <button onClick={handleSave}>Save</button>
                <button onClick={toggleModal}>Cancel</button>
            </div>
        </div>
        )}
    </>);
};

export default SensorEditModal;
