import React, { useState } from 'react';
import "./Modal.css"



const SensorEditModal = ({data, setData, modal, setModal, sensorCursor, backend, forceUpdate}) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    //const [modal, setModal] = useState(false);
    const [entityId, setEntityId] = useState("entityMock");//data[sensorCursor].entity_id);
    const [name, setName] = useState("NameMock");//data[sensorCursor].name);
    const [entityIDValid, setEntityIDValid] = useState(false);

    const handleSave = () => {
        var sensor = {};
        var updatedData = JSON.parse(JSON.stringify(data));
        if(sensorCursor == -1){ // Creating
            backend.CheckEntityId(entityId).then((result) => {
                if(result){
                    sensor.entity_id = entityId;
                    setEntityIDValid(true);
                    backend.CreateSensor(sensor);
                    updatedData.push(sensor);
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
        else{ // Updating
            backend.CheckEntityId(entityId).then((result) => {
                if(result){
                    setEntityIDValid(true);
                    console.log("Full Data:")
                    console.log(data)
                    sensor = data[sensorCursor]
                    sensor.entity_id = entityId;
                    console.log(data[sensorCursor])
                    backend.UpdateSensor(sensor);
                    updatedData[sensorCursor] = sensor;
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
        
        
    };

    return ( <>
        {modal && (<div className='modal'>
            <div onClick={toggleModal}className="overlay"></div>
            <div className="modal-content">
                {sensorCursor>=0 && (<h2>Edit Sensor</h2>)}
                {sensorCursor<0 && (<h2>Add Sensor</h2>)}
                <label>Entity ID {" " + entityIDValid}</label>
                <input
                    type="text"
                    value={entityId }
                    onChange={
                        (e) => {
                            setEntityId(e.target.value);
                            backend.CheckEntityId(e.target.value).then((result) => {
                                setEntityIDValid(result);
                            });
                    }}
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