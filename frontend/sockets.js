const WS_URL = "http://localhost:8082"

socket = io(WS_URL, {
    withCredentials: true
})

socket.on("connected", () => {
    console.log("Connected to WebSocket server")
})

socket.on("initial_data", (data) => {
    console.log("Received initial data:", data)
})

socket.on("new_message", (message) => {
    console.log("New message received:", message)
})

socket.on("scratchpad_updated", (data) => {
    console.log("Scratchpad updated:", data)
    continueWriting()
})

socket.on("scratchpad_desync", (data) => {
    console.log("Scratchpad desynced:", data)
    // You might want to handle desync here, e.g., by requesting the full content again
    handleDesync(data['full_content'])
})

socket.on("initial_scratchpad", (data) => {
    console.log("Received initial scratchpad data:", data)
    initialize_scratchpad(data);
})

socket.on("disconnect", () => {
    console.log("Disconnected from WebSocket server")
})

function sendMessage(message) {
    socket.emit("send_message", message)
}

function updateScratchpad(patch_text, scratchpad_id) {
    socket.emit("update_scratchpad", {
        'patch_text': patch_text,
        'scratchpad_id': scratchpad_id
    })
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