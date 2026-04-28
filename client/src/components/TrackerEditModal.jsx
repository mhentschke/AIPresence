import React, { useState, useEffect } from 'react';
import "./Modal.css"
import EntityPicker from './EntityPicker';



const TrackerEditModal = ({data, setData, modal, setModal, trackerCursor, backend}) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    const [entityId, setEntityId] = useState("");
    const [entityIDValid, setEntityIDValid] = useState(false);

    // Initialize state from selected tracker when editing, reset when creating
    useEffect(() => {
        if (modal && trackerCursor >= 0 && data[trackerCursor]) {
            setEntityId(data[trackerCursor].entity_id || "");
            setEntityIDValid(true);
        } else if (modal && trackerCursor === -1) {
            setEntityId("");
            setEntityIDValid(false);
        }
    }, [modal, trackerCursor, data]);

    const handleSave = async () => {
        let tracker = {};
        const updatedData = JSON.parse(JSON.stringify(data));
        if(trackerCursor === -1){ // Creating
            try {
                const exists = await backend.CheckEntityId(entityId);
                if(exists){
                    tracker.entity_id = entityId;
                    setEntityIDValid(true);
                    const result = await backend.CreateTracker(tracker);
                    tracker.id = result.id;
                    updatedData.push(tracker);
                    toggleModal();
                    setData(updatedData);
                } else {
                    setEntityIDValid(false);
                    alert("Entity ID does not Exist in Home Assistant");
                }
            } catch (err) {
                console.error("Error creating tracker:", err);
            }
        }
        else{ // Updating
            try {
                const exists = await backend.CheckEntityId(entityId);
                if(exists){
                    setEntityIDValid(true);
                    tracker = data[trackerCursor];
                    tracker.entity_id = entityId;
                    await backend.UpdateTracker(tracker);
                    updatedData[trackerCursor] = tracker;
                    toggleModal();
                    setData(updatedData);
                } else {
                    setEntityIDValid(false);
                    alert("Entity ID does not Exist in Home Assistant");
                }
            } catch (err) {
                console.error("Error updating tracker:", err);
            }
        }
    };

    return ( <>
        {modal && (<div className='modal'>
            <div onClick={toggleModal}className="overlay"></div>
            <div className="modal-content">
                {trackerCursor>=0 && (<h2>Edit Tracker</h2>)}
                {trackerCursor<0 && (<h2>Add Tracker</h2>)}
                <EntityPicker
                    domain="device_tracker"
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

export default TrackerEditModal;
