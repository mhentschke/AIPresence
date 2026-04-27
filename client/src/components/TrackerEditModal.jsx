
import React, { useState } from 'react';
import "./Modal.css"



const TrackerEditModal = ({data, setData, modal, setModal, trackerCursor, backend, forceUpdate}) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    //const [modal, setModal] = useState(false);
    const [entityId, setEntityId] = useState("entityMock");//data[trackerCursor].entity_id);
    const [name, setName] = useState("NameMock");//data[trackerCursor].name);
    const [entityIDValid, setEntityIDValid] = useState(false);

    const handleSave = () => {
        let tracker = {};
        const updatedData = JSON.parse(JSON.stringify(data));
        if(trackerCursor === -1){ // Creating
            backend.CheckEntityId(entityId).then((result) => {
                if(result){
                    tracker.entity_id = entityId;
                    setEntityIDValid(true);
                    backend.CreateTracker(tracker);
                    updatedData.push(tracker);
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
                    tracker = data[trackerCursor]
                    tracker.entity_id = entityId;
                    console.log(data[trackerCursor])
                    backend.UpdateTracker(tracker);
                    updatedData[trackerCursor] = tracker;
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
                {trackerCursor>=0 && (<h2>Edit Tracker</h2>)}
                {trackerCursor<0 && (<h2>Add Tracker</h2>)}
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

export default TrackerEditModal;