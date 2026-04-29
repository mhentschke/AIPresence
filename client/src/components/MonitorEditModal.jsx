import { useState, useEffect } from 'react';
import { useToast } from './ToastContext';
import modalStyles from './Modal.module.css';
import btnStyles from './Button.module.css';
import EntityPicker from './EntityPicker';

const MonitorEditModal = ({ data, setData, modal, setModal, backend }) => {
    const { addToast } = useToast();
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
                addToast("Monitor added successfully", "success");
            } else {
                setEntityIDValid(false);
                addToast("Entity ID does not exist in Home Assistant", "error");
            }
        } catch (err) {
            addToast("Error adding monitor: " + err.message, "error");
        }
    };

    return (
        <>
            {modal && (
                <div className={modalStyles.modal}>
                    <div onClick={() => setModal(false)} className={modalStyles.overlay}></div>
                    <div className={modalStyles.content}>
                        <div className={modalStyles.header}>
                            <h2>Add Monitor</h2>
                        </div>
                        <div className={modalStyles.body}>
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
                        </div>
                        <div className={modalStyles.footer}>
                            <button className={btnStyles.secondary} onClick={() => setModal(false)}>Cancel</button>
                            <button className={btnStyles.primary} onClick={handleSave}>Save</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default MonitorEditModal;
