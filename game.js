let ws = null;
let playerNum = 0;
let choiceMade = false;

const status = document.getElementById('status');
const resultPanel = document.getElementById('resultPanel');
const playAgainBtn = document.getElementById('playAgainBtn');

window.onload = () => {
    connect();
};

function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('Connected to server');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };

    ws.onerror = (error) => {
        updateStatus('Connection error!', 'error');
    };

    ws.onclose = () => {
        updateStatus('Disconnected. Refresh to reconnect.', 'error');
    };
}