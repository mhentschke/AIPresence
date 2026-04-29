import React, { useState, useEffect } from 'react';
import { useToast } from './ToastContext';
import modalStyles from './Modal.module.css';
import btnStyles from './Button.module.css';
import EntityPicker from './EntityPicker';



const SensorEditModal = ({data, setData, modal, setModal, sensorCursor, backend}) => {

    const { addToast } = useToast();

    const toggleModal = () => {
        setModal(!modal)
    };

    const [entityId, setEntityId] = useState("");
    const [entityIDValid, setEntityIDValid] = useState(false);
    const [saving, setSaving] = useState(false);

    // Initialize state from selected sensor when editing, reset when creating
    useEffect(() => {
        if (modal && sensorCursor >= 0 && data[sensorCursor]) {
            setEntityId(data[sensorCursor].entity_id || "");
            setEntityIDValid(true);
            setSaving(false);
        } else if (modal && sensorCursor === -1) {
            setEntityId("");
            setEntityIDValid(false);
            setSaving(false);
        }
    }, [modal, sensorCursor, data]);

    const handleSave = async () => {
        let sensor = {};
        const updatedData = JSON.parse(JSON.stringify(data));
        setSaving(true);
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
                    addToast("Sensor created successfully", "success");
                } else {
                    setEntityIDValid(false);
                    addToast("Entity ID does not exist in Home Assistant", "error");
                }
            } catch (err) {
                console.error("Error creating sensor:", err);
            } finally {
                setSaving(false);
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
                    addToast("Sensor updated successfully", "success");
                } else {
                    setEntityIDValid(false);
                    addToast("Entity ID does not exist in Home Assistant", "error");
                }
            } catch (err) {
                console.error("Error updating sensor:", err);
            } finally {
                setSaving(false);
            }
        }
    };

    return ( <>
        {modal && (<div className={modalStyles.modal}>
            <div onClick={toggleModal} className={modalStyles.overlay}></div>
            <div className={modalStyles.content}>
                <div className={modalStyles.header}>
                    {sensorCursor>=0 && (<h2>Edit Sensor</h2>)}
                    {sensorCursor<0 && (<h2>Add Sensor</h2>)}
                </div>
                <div className={modalStyles.body}>
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
                </div>
                <div className={modalStyles.footer}>
                    <button className={btnStyles.secondary} onClick={toggleModal}>Cancel</button>
                    <button className={btnStyles.primary} onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                </div>
            </div>
        </div>
        )}
    </>);
};

export default SensorEditModal;
