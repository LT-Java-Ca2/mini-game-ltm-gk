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

function startRound(scores) {
    updateStatus('Make your choice!', 'connected');
    choiceMade = false;
    enableButtons();
    updateScores(scores);
    
    resultPanel.className = 'result-panel';
    document.getElementById('resultTitle').textContent = 'Choose your weapon!';
    document.getElementById('resultChoices').textContent = '';
    document.getElementById('resultText').textContent = '';
    playAgainBtn.classList.add('hidden');
}

function makeChoice(choice) {
    if (ws && ws.readyState === WebSocket.OPEN && !choiceMade) {
        choiceMade = true;
        ws.send(JSON.stringify({
            type: 'choice',
            choice: choice
        }));
    }
}

function showResult(data) {
    const choices = {rock: 'Stone.gif', paper: 'Paper.gif', scissors: 'Scissor.gif'};
    
    resultPanel.className = 'result-panel ' + data.result;
    
    let title = '';
    if (data.result === 'win') {
        title = 'YOU WIN!';
    } else if (data.result === 'lose') {
        title = 'YOU LOSE';
    } else {
        title = 'TIE!';
    }
    
    document.getElementById('resultTitle').textContent = title;
    // --- PHẦN ĐÃ SỬA ---
    // 1. Tạo chuỗi HTML chứa thẻ <img>
    // Bạn có thể thêm class hoặc style width để chỉnh kích thước ảnh cho đẹp
    const yourImgHTML = `<img src="${choices[data.your_choice]}" alt="${data.your_choice}" style="width: 100px; height: auto;">`;
    const oppImgHTML = `<img src="${choices[data.opponent_choice]}" alt="${data.opponent_choice}" style="width: 100px; height: auto;">`;

    // 2. Sử dụng innerHTML để trình duyệt hiển thị hình ảnh
    document.getElementById('resultChoices').innerHTML = 
        `${yourImgHTML} <span class="mx-3 fw-bold">VS</span> ${oppImgHTML}`;
    // -------------------

    document.getElementById('resultText').textContent = 
        `You: ${data.your_choice.toUpperCase()} | Opponent: ${data.opponent_choice.toUpperCase()}`;
    
    updateScores(data.scores);
    playAgainBtn.classList.remove('hidden');
}