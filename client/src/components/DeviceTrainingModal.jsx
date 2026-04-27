
import React, { useState, useEffect } from 'react';
import "./Modal.css"

let interval = undefined;

const DeviceTrainingModal = ({ devices, setDevices, rooms, setRooms, modal, setModal, deviceCursor, backend, forceUpdate, getElementFromId }) => {

    const toggleModal = () => {
        setModal(!modal)
    };
    const [training_overwrite, setTrainingOverwrite] = useState(false);
    const [roomTrainingProgress, setRoomTrainingProgress] = useState(0);
    const [roomTrainingSamples, setRoomTrainingSamples] = useState(0);
    const [training, setTraining] = useState(false);
    const [roomId, setRoomId] = useState("Not Training");
    //var roomId = "Not Training";
    const [roomIndex, setRoomIndex] = useState(0);
    const [roomChanged, setRoomChanged] = useState(false);


    const handleRoomButtonClick = (id, index) => {
        if (!training){
            setTraining(true);
            backend.StartTraining(devices[deviceCursor].id, id, training_overwrite);
        }
        else{
            backend.ChangeRoom(devices[deviceCursor].id, id);            
        }
        setRoomChanged(true);
        setRoomId(id);
        //roomId = id;
        setRoomIndex(index);
        console.log("id:", id, "Room ID:", roomId, "Device:", devices[deviceCursor].name, "Index:", roomIndex);
        updateRoomTrainingProgress(id);
    };

    const updateRoomTrainingProgress = (id) => {
        backend.GetTrainingProgress(devices[deviceCursor].id).then((result) => {
            const res = result
            console.log("Training Progress: ", res);
            console.log("RoomId:", id)
            if (res !== null){
                if(id in res){
                    setRoomTrainingProgress(res[id]["percentage"]*100);
                    setRoomTrainingSamples(res[id]["count"]);
                }
                else{
                    setRoomTrainingProgress(0);
                }
            }
            else{
                setRoomTrainingProgress(0);
            }
            
        });
    }
    

    useEffect(() => {
        console.log("Hook Called. Training:", training, "Modal:", modal);
        if (roomChanged){
            setRoomChanged(false);
            console.log("Room Changed:", roomChanged);
            clearInterval(interval);
            interval = undefined;

        }
        else{
            if (training && modal){
                interval = setInterval(() => {
                    if (training && modal){
                        console.log("Updating Training Progress. Training:", training, "Modal:", modal, "RoomId:", roomId);
                        updateRoomTrainingProgress(roomId);
                    }
                    else{
                        console.log("Skipping Update")
                    }
                }, 1000);
            }
            else{
                console.log("Clearing Interval:", interval, "Training:", training, "Modal:", modal);
                clearInterval(interval);
                interval = undefined;
                console.log("Cleared Interval:", interval, "Training:", training, "Modal:", modal)
            }
        }
    }, [training, modal, roomChanged]);




    return (
        <>
            {modal && (<div className='modal'>
                <div onClick={toggleModal}className="overlay"></div>
                    <div className="modal-content">
                        <h2>Device Training</h2>
                        <p>Chose a room to start!</p>
                        <p></p>
                        <input type="checkbox" id="training_overwrite" name="training_overwrite" defaultChecked={training_overwrite} onChange={
                            (e) => {
                               setTrainingOverwrite(e.target.checked); 
                            }
                        }></input>
                        <label>Overwrite Training</label>
                        <div className="button-grid-rooms">
                            {rooms.map((room, index) => (
                                <button key={room.id} onClick={() => handleRoomButtonClick(room.id, index)} style={{backgroundColor : room.color}}>
                                    {room.name}
                                </button>
                            ))}
                        </div>
                        {training && (
                        <>
                            <div>
                                <progress id="training_progress" value={roomTrainingProgress} max="100"></progress>
                            </div>
                            <div>
                                <p>Training Progress: {roomTrainingProgress}% - {roomTrainingSamples} samples</p>
                            </div>
                            <div>
                                <p>Current Room: {roomId!==0?rooms[roomIndex].name:"Not Training"}</p>
                            </div>
                            <div>
                                <p>Old Model Prediction: {roomId!==0?getElementFromId(rooms, "id", roomId).name:"Not Training"}</p>
                            </div>
                        </>
                        )}
                        <div>
                            <button onClick={() => {
                                if (training){
                                    console.log("Training:", training)
                                    backend.StopTraining(devices[deviceCursor].id)
                                    setTraining(false);
                                    
                                }
                                toggleModal();
                                setTrainingOverwrite(false);
                            }} disabled={!training}>Done</button>
                            <button onClick={() => {
                                if (training){
                                    backend.CancelTraining(devices[deviceCursor].id)
                                    setTraining(false);
                                    
                                }
                                toggleModal();
                                setTrainingOverwrite(false);
                                
                            }}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default DeviceTrainingModal;