import { useState, useEffect } from 'react';
import "./Modal.css"
import EntityPicker from './EntityPicker';

const DeviceEditModal = ({ data, setData, modal, setModal, deviceCursor, backend }) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    const [entityId, setEntityId] = useState("");
    const [beaconId, setBeaconId] = useState("");
    const [name, setName] = useState("");
    const [entityIDValid, setEntityIDValid] = useState(true);

    useEffect(() => {
        if (modal && deviceCursor >= 0 && data[deviceCursor]) {
            const device = data[deviceCursor];
            setName(device.name || "");
            setEntityId(device.entity_id || "");
            setBeaconId(device.beacon_id || "");
            setEntityIDValid(true);
        } else if (modal && deviceCursor === -1) {
            setName("");
            setEntityId("");
            setBeaconId("");
            setEntityIDValid(true);
        }
    }, [modal, deviceCursor, data]);

    const hasAtLeastOneId = entityId.trim() !== "" || beaconId.trim() !== "";

    const handleSave = async () => {
        if (!hasAtLeastOneId) {
            alert("At least one of Entity ID or Beacon ID must be filled");
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
                    alert("Entity ID does not exist in Home Assistant");
                    return;
                }
            } catch (err) {
                alert("Error validating entity: " + err.message);
                return;
            }
        }
        setEntityIDValid(true);

        const updatedData = JSON.parse(JSON.stringify(data));

        try {
            if (deviceCursor === -1) {
                const result = await backend.CreateDevice(device);
                device.id = result.id;
                updatedData.push(device);
            } else {
                device.id = data[deviceCursor].id;
                await backend.UpdateDevice(device);
                updatedData[deviceCursor] = device;
            }
            toggleModal();
            setData(updatedData);
        } catch (err) {
            alert("Error saving device: " + err.message);
        }
    };

    return (
        <>
            {modal && (
                <div className='modal'>
                    <div onClick={toggleModal} className="overlay"></div>
                    <div className="modal-content">
                        {deviceCursor >= 0 ? <h2>Edit Device</h2> : <h2>Add Device</h2>}

                        <label>Name</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                        />

                        <p></p>

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

                        <p></p>

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

                        <p></p>

                        {!hasAtLeastOneId && (
                            <p style={{ color: 'red', fontSize: '0.85em' }}>
                                At least one of Entity ID or Beacon ID is required
                            </p>
                        )}

                        <button onClick={handleSave} disabled={!hasAtLeastOneId || !name.trim()}>Save</button>
                        <button onClick={toggleModal}>Cancel</button>
                    </div>
                </div>
            )}
        </>
    );
};

export default DeviceEditModal;
