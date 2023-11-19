
import React, { useState } from 'react';
import "./Modal.css"



const DeviceEditModal = ({ data, onSave, onCancel, modal, setModal}) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    //const [modal, setModal] = useState(false);
    const [entityId, setEntityId] = useState(data.entity_id);
    const [name, setName] = useState(data.name);

    const handleSave = () => {
        const updatedData = { ...data, entity_id: entityId, name };
        onSave(updatedData);
    };

    return ( <>
        {modal && (<div className='modal'>
            <div onClick={toggleModal}className="overlay"></div>
            <div className="modal-content">
                <input
                    type="text"
                    value={entityId}
                    onChange={(e) => setEntityId(e.target.value)}
                />
                <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />
                <button onClick={handleSave}>Save</button>
                <button onClick={toggleModal}>Cancel</button>
            </div>
        </div>
        )}
    </>);
};

export default DeviceEditModal;