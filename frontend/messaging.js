





//DOM FUNCTIONS
function getMentorStatus() {
           
}

function updateMentorStatus() {
    const status = getMentorStatus();
    const statusElement = document.getElementById('mentor-status');
    if (!statusElement) return; 
    statusElement.classList.remove('online', 'offline', 'away', 'unknown');

    switch (status) {
        case 'ONLINE':
            statusElement.textContent = 'Online';
            statusElement.classList.add('online');
            break;
        case 'OFFLINE':
            statusElement.textContent = 'Offline';
            statusElement.classList.add('offline');
            break;
        case 'AWAY':
            statusElement.textContent = 'Away';
            statusElement.classList.add('away');
            break;
        default:
            statusElement.textContent = 'Unknown';
            statusElement.classList.add('unknown');
    }
}

function saveMessageToDatabase(messageText) {
    console.log("Pretending to save sum bs");
    sendMessage({message: messageText});
}


function appendSentMessage(messageText) {
    // Find the chat window
    const chatWindow = document.getElementById('chat-messages-container');
    if (!chatWindow) return; 

    // Create all the new HTML elements
    const container = document.createElement('div');
    container.className = 'message-container sent'; // Aligns to the right

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble sent'; // Styles as a blue bubble

    const textElement = document.createElement('p');
    textElement.textContent = messageText; // Adds the user's text

    
    bubble.appendChild(textElement);
    container.appendChild(bubble);

    
    chatWindow.appendChild(container);

    
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function handleSendMessage() {
    const input = document.getElementById('chat-input');
    if (!input) return; 

    const messageText = input.value.trim(); // remove whitespace

    
    if (messageText === "") {
        return;
    }
    
    
    //Thanks very much !!!!


    // Call  (empty) database function
    saveMessageToDatabase(messageText);

    
    appendSentMessage(messageText);

    //clear
    input.value = '';
}

function appendReceivedMessage(messageText) {
    // Find the chat window
    const chatWindow = document.getElementById('chat-messages-container');
    if (!chatWindow) return; 

    //  the outer container
    const container = document.createElement('div');
    //  KEEP left
    container.className = 'message-container received'; 

    // make the message bubble
    const bubble = document.createElement('div');
    
    bubble.className = 'message-bubble received'; 

    // make the text paragraph
    const textElement = document.createElement('p');
    textElement.textContent = messageText; // Adds the mentor's text
    
    console.log("testing appendReceivedMessage IT WORKEDS");

    // <p> inside <bubble> inside <container>
    bubble.appendChild(textElement);
    container.appendChild(bubble);

    // the new message to the end of the chat window
    chatWindow.appendChild(container);

    // bottom so the new message is visible
    chatWindow.scrollTop = chatWindow.scrollHeight;

    
}

function processNewMentorMessage(messageData) {
    
    console.log("testing processNewMentorMessage");

    
    appendReceivedMessage(messageData);
}






// EVENT LISTENERS
document.addEventListener('DOMContentLoaded', () => {
    updateMentorStatus();
    setInterval(updateMentorStatus, 3000);
    
    const sendButton = document.getElementById('send-button');
    if (sendButton) {
        sendButton.addEventListener('click', handleSendMessage);
    }

    
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', (event) => {
            // Check if the key pressed was Enter
            if (event.key === 'Enter') {
                event.preventDefault(); // Stop it from adding a new line
                handleSendMessage();
            }
        });
    }
});