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

function handleMessage(data) {
    switch(data.type) {
        case 'connected':
            playerNum = data.player_num;
            updateStatus(`Connected as Player ${playerNum}`, 'connected');
            break;

        case 'waiting':
            updateStatus(data.message, 'waiting');
            document.getElementById('resultTitle').textContent = 'Waiting for opponent...';
            break;

        case 'game_start':
            updateStatus(data.message, 'connected');
            break;

        case 'round_start':
            startRound(data.scores);
            break;

        case 'choice_made':
            updateStatus('Waiting for opponent...', 'waiting');
            disableButtons();
            break;

        case 'result':
            showResult(data);
            break;

        case 'opponent_left':
            updateStatus(data.message, 'error');
            disableButtons();
            document.getElementById('resultTitle').textContent = 'Opponent left. Waiting...';
            break;

        case 'error':
            updateStatus(data.message, 'error');
            document.getElementById('resultTitle').textContent = data.message;
            break;
    }
}