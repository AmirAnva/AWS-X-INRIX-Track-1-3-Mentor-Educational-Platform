const WS_URL = "http://localhost:8082"

socket = io(WS_URL, {
    withCredentials: true
})

socket.on("connected", () => {
    console.log("Connected to WebSocket server")
})

socket.on("initial_data", (data) => {
    console.log("Received initial data:", data)
    let message_history = data["messages"]
    let own_user_id = data["own_user_id"]
    for (let i = 0; i < message_history.length; i++) {
        let message = message_history[i]
        if (message["sender_id"] === own_user_id) {
            appendSentMessage(message["message"])
        } else {
            appendReceivedMessage(message["message"])
        }
    }
})

socket.on("new_message", (message) => {
    console.log("New message received:", message)
    processNewMentorMessage(message["message"])
})



socket.on("disconnect", () => {
    console.log("Disconnected from WebSocket server")
})

function sendMessage(message) {
    socket.emit("send_message", message)
}



function debug(){
    socket.emit("pingpong")
    setInterval(() => {
        socket.emit("pingpong")
        console.log("trying to pingpong")
        console.log(socket.connected)
    }, 1000);
}

debug()