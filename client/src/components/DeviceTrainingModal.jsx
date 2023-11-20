
import React, { useState } from 'react';
import "./Modal.css"



const DeviceTrainingModal = ({data, setData, onSave, modal, setModal, deviceCursor, backend, forceUpdate}) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    //const [modal, setModal] = useState(false);
    const [entityId, setEntityId] = useState("entityMock");//data[deviceCursor].entity_id);
    const [name, setName] = useState("NameMock");//data[deviceCursor].name);
    const [entityIDValid, setEntityIDValid] = useState(false);

    const handleSave = () => {
        var device = {};
        var updatedData = JSON.parse(JSON.stringify(data));
        if(deviceCursor == -1){ // Creating
            backend.CheckEntityId(entityId).then((result) => {
                if(result){
                    device.entity_id = entityId;
                    device.name = name;
                    setEntityIDValid(true);
                    backend.CreateDevice(device);
                    updatedData.push(device);
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
        
        
    };

    return ( <>
        {modal && (<div className='modal'>
            <div onClick={toggleModal}className="overlay"></div>
            <div className="modal-content">
                {deviceCursor>=0 && (<h2>Edit Device</h2>)}
                {deviceCursor<0 && (<h2>Add Device</h2>)}
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
                <label>Name</label>
                <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />
                <p></p>
                <button onClick={handleSave}>Save</button>
                <button onClick={toggleModal}>Cancel</button>
            </div>
        </div>
        )}
    </>);
};

export default DeviceTrainingModal;