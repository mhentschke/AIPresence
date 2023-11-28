import React, { useState } from 'react';
import "./Modal.css"



const RoomEditModal = ({data, setData, modal, setModal, roomCursor, backend, forceUpdate}) => {

    const toggleModal = () => {
        setModal(!modal)
    };

    //const [modal, setModal] = useState(false);
    const [name, setName] = useState("NameMock");
    const [color, setColor] = useState("#ffffff");

    const handleSave = () => {
        var room = {};
        var updatedData = JSON.parse(JSON.stringify(data));
        if(roomCursor == -1){ // Creating
            room.name = name;
            room.color = color;
            backend.CreateRoom(room);
            updatedData.push(room);
            toggleModal();
            setData(updatedData);
            forceUpdate();            
        }
        else{ // Updating
            room.name = name;
            room.color = color;
            room.id = data[roomCursor].id;
            backend.UpdateRoom(room);
            updatedData[roomCursor] = room;
            toggleModal();
            setData(updatedData);
            forceUpdate();
        }
    }


    return ( <>
        {modal && (<div className='modal'>
            <div onClick={toggleModal}className="overlay"></div>
            <div className="modal-content">
                {roomCursor>=0 && (<h2>Edit Room</h2>)}
                {roomCursor<0 && (<h2>Add Room</h2>)}
                <label>Room Name</label>
                <input
                    type="text"
                    defaultValue={(roomCursor >= 0)?data[roomCursor].name:"Name"}
                    onChange={
                        (e) => {
                            setName(e.target.value);
                    }}
                />
                <label>Color</label>
                <input type="color" id="room_color" name="room_color" value={(roomCursor >= 0)?data[roomCursor].color:color} onChange={
                  (e) => {
                    setColor(e.target.value);
                  }
                }></input>
                <p></p>
                <button onClick={handleSave}>Save</button>
                <button onClick={toggleModal}>Cancel</button>
            </div>
        </div>
        )}
    </>);
};

export default RoomEditModal;