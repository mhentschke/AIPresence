import { useState, useEffect } from 'react';
import { useToast } from './ToastContext';
import modalStyles from './Modal.module.css';
import btnStyles from './Button.module.css';
import EntityPicker from './EntityPicker';

const DeviceEditModal = ({ data, setData, modal, setModal, deviceCursor, backend }) => {

    const { addToast } = useToast();

    const toggleModal = () => {
        setModal(!modal)
    };

    const [entityId, setEntityId] = useState("");
    const [beaconId, setBeaconId] = useState("");
    const [name, setName] = useState("");
    const [entityIDValid, setEntityIDValid] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (modal && deviceCursor >= 0 && data[deviceCursor]) {
            const device = data[deviceCursor];
            setName(device.name || "");
            setEntityId(device.entity_id || "");
            setBeaconId(device.beacon_id || "");
            setEntityIDValid(true);
            setSaving(false);
        } else if (modal && deviceCursor === -1) {
            setName("");
            setEntityId("");
            setBeaconId("");
            setEntityIDValid(true);
            setSaving(false);
        }
    }, [modal, deviceCursor, data]);

    const hasAtLeastOneId = entityId.trim() !== "" || beaconId.trim() !== "";

    const handleSave = async () => {
        if (!hasAtLeastOneId) {
            addToast("At least one of Entity ID or Beacon ID must be filled", "error");
            return;
        }

        const device = {
            name: name,
            entity_id: entityId.trim() || null,
            beacon_id: beaconId.trim() || null,
        };

        // Validate entity_id exists in HA if provided
        if (device.entity_id) {
            try {
                const exists = await backend.CheckEntityId(device.entity_id);
                if (!exists) {
                    setEntityIDValid(false);
                    addToast("Entity ID does not exist in Home Assistant", "error");
                    return;
                }
            } catch (err) {
                addToast("Error validating entity: " + err.message, "error");
                return;
            }
        }
        setEntityIDValid(true);

        const updatedData = JSON.parse(JSON.stringify(data));

        setSaving(true);
        try {
            if (deviceCursor === -1) {
                const result = await backend.CreateDevice(device);
                device.id = result.id;
                updatedData.push(device);
                addToast("Device created successfully", "success");
            } else {
                device.id = data[deviceCursor].id;
                await backend.UpdateDevice(device);
                updatedData[deviceCursor] = device;
                addToast("Device updated successfully", "success");
            }
            toggleModal();
            setData(updatedData);
        } catch (err) {
            addToast("Error saving device: " + err.message, "error");
        } finally {
            setSaving(false);
        }
    };

    return (
        <>
            {modal && (
                <div className={modalStyles.modal}>
                    <div onClick={toggleModal} className={modalStyles.overlay}></div>
                    <div className={modalStyles.content}>
                        <div className={modalStyles.header}>
                            {deviceCursor >= 0 ? <h2>Edit Device</h2> : <h2>Add Device</h2>}
                        </div>
                        <div className={modalStyles.body}>
                            <label>Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                            />

                            <fieldset>
                                <legend>Monitor (Entity ID)</legend>
                                <p style={{ fontSize: '0.85em', margin: '4px 0 8px' }}>
                                    HA sensor entity for this device's beacon monitor (e.g. phone running BLE scanner)
                                </p>
                                <EntityPicker
                                    domain="sensor"
                                    value={entityId}
                                    onChange={(val) => {
                                        setEntityId(val);
                                        if (val.trim()) {
                                            backend.CheckEntityId(val).then((result) => {
                                                setEntityIDValid(result);
                                            });
                                        } else {
                                            setEntityIDValid(true);
                                        }
                                    }}
                                    label=""
                                />
                            </fieldset>

                            <fieldset>
                                <legend>Beacon ID</legend>
                                <p style={{ fontSize: '0.85em', margin: '4px 0 8px' }}>
                                    BLE beacon identifier this device advertises (uuid_major_minor)
                                </p>
                                <input
                                    type="text"
                                    value={beaconId}
                                    onChange={(e) => setBeaconId(e.target.value)}
                                    placeholder="e.g. a3f498e7-c46f-47b4-a767-7c3ad16044fc_100_40004"
                                    style={{ width: '100%' }}
                                />
                            </fieldset>

                            {!hasAtLeastOneId && (
                                <p className={modalStyles.errorText}>
                                    At least one of Entity ID or Beacon ID is required
                                </p>
                            )}
                        </div>
                        <div className={modalStyles.footer}>
                            <button className={btnStyles.secondary} onClick={toggleModal}>Cancel</button>
                            <button className={btnStyles.primary} onClick={handleSave} disabled={saving || !hasAtLeastOneId || !name.trim()}>{saving ? 'Saving...' : 'Save'}</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default DeviceEditModal;
