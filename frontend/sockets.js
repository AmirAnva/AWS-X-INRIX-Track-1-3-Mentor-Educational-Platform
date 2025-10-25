const WS_URL = "/socket.io"

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

function sendMessage(message) {
    socket.emit("send_message", message)
}