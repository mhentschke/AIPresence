import React, { useState, useEffect } from 'react'
import DeviceTable from './components/DeviceTable'
import DeviceEditModal from './components/DeviceEditModal'



function App() {
    const [data, setData] = useState([{}])
    const [deviceEditModal, setDeviceEditModal] = useState(false)
    useEffect(() => {
        fetch('/devices').then(
            res => res.json()
        ).then(
            data => {
                for(var d = 0; d < data.length; d++) {
                    if (data[d].model === null) {
                        data[d].trained = false
                        data[d].accuracy = "-"
                    }
                    else{
                        data[d].trained = true
                        data[d].accuracy = data[d].model.trained_model_stats.accuracy
                    }
                }
                setData(data)
                console.log(data)
            }
        )
    }, [])
    return (
        <div>
            <h1>Devices</h1>
            <div class = "w3-responsive">
                <DeviceTable data = {data} deviceEditModal = {setDeviceEditModal}/>
            </div> 
            <div class = "w3-responsive">
                <DeviceEditModal data = {data} modal={deviceEditModal} setModal={setDeviceEditModal}/>
            </div>


        </div>
    )
}

export default App