import React, { useState, useEffect } from 'react';
import { useToast } from './ToastContext';
import modalStyles from './Modal.module.css';
import btnStyles from './Button.module.css';



const RoomEditModal = ({data, setData, modal, setModal, roomCursor, backend}) => {

    const { addToast } = useToast();

    const toggleModal = () => {
        setModal(!modal)
    };

    const [name, setName] = useState("");
    const [color, setColor] = useState("#ffffff");

    // Initialize state from selected room when editing, reset to defaults when creating
    useEffect(() => {
        if (modal && roomCursor >= 0 && data[roomCursor]) {
            setName(data[roomCursor].name || "");
            setColor(data[roomCursor].color || "#ffffff");
        } else if (modal && roomCursor === -1) {
            setName("");
            setColor("#ffffff");
        }
    }, [modal, roomCursor, data]);

    const handleSave = async () => {
        const room = {};
        const updatedData = JSON.parse(JSON.stringify(data));
        if(roomCursor === -1){ // Creating
            room.name = name;
            room.color = color;
            try {
                const result = await backend.CreateRoom(room);
                room.id = result.id;
                updatedData.push(room);
                toggleModal();
                setData(updatedData);
                addToast("Room created successfully", "success");
            } catch (err) {
                console.error("Error creating room:", err);
            }
        }
        else{ // Updating
            room.name = name;
            room.color = color;
            room.id = data[roomCursor].id;
            try {
                await backend.UpdateRoom(room);
                updatedData[roomCursor] = room;
                toggleModal();
                setData(updatedData);
                addToast("Room updated successfully", "success");
            } catch (err) {
                console.error("Error updating room:", err);
            }
        }
    }


    return ( <>
        {modal && (<div className={modalStyles.modal}>
            <div onClick={toggleModal} className={modalStyles.overlay}></div>
            <div className={modalStyles.content}>
                <div className={modalStyles.header}>
                    {roomCursor>=0 && (<h2>Edit Room</h2>)}
                    {roomCursor<0 && (<h2>Add Room</h2>)}
                </div>
                <div className={modalStyles.body}>
                    <label>Room Name</label>
                    <input
                        type="text"
                        value={name}
                        onChange={
                            (e) => {
                                setName(e.target.value);
                        }}
                    />
                    <label>Color</label>
                    <input type="color" id="room_color" name="room_color" value={color} onChange={
                      (e) => {
                        setColor(e.target.value);
                      }
                    }></input>
                </div>
                <div className={modalStyles.footer}>
                    <button className={btnStyles.secondary} onClick={toggleModal}>Cancel</button>
                    <button className={btnStyles.primary} onClick={handleSave}>Save</button>
                </div>
            </div>
        </div>
        )}
    </>);
};

export default RoomEditModal;
