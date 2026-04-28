import { useState, useEffect } from 'react';
import "./Modal.css"
import EntityPicker from './EntityPicker';

const MonitorEditModal = ({ data, setData, modal, setModal, backend }) => {
    const [entityId, setEntityId] = useState("");
    const [entityIDValid, setEntityIDValid] = useState(false);

    useEffect(() => {
        if (modal) {
            setEntityId("");
            setEntityIDValid(false);
        }
    }, [modal]);

    const handleSave = async () => {
        try {
            const exists = await backend.CheckEntityId(entityId);
            if (exists) {
                await backend.CreateBeaconMonitor(entityId);
                const updatedData = [...data, { entity_id: entityId }];
                setData(updatedData);
                setModal(false);
            } else {
                setEntityIDValid(false);
                alert("Entity ID does not exist in Home Assistant");
            }
        } catch (err) {
            alert("Error adding monitor: " + err.message);
        }
    };

    return (
        <>
            {modal && (
                <div className='modal'>
                    <div onClick={() => setModal(false)} className="overlay"></div>
                    <div className="modal-content">
                        <h2>Add Monitor</h2>
                        <EntityPicker
                            domain="sensor"
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
                        <button onClick={() => setModal(false)}>Cancel</button>
                    </div>
                </div>
            )}
        </>
    );
};

export default MonitorEditModal;
