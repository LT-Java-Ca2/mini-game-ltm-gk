import asyncio
import json
from aiohttp import web
import aiohttp
import os
import mimetypes

class RPSGameServer:
    def __init__(self):
        self.players = []
        self.choices = {}
        self.scores = [0, 0]
        self.game_started = False
        
    async def register(self, ws):
        if len(self.players) >= 2:
            await ws.send_json({
                'type': 'error',
                'message': 'Game is full. Only 2 players allowed.'
            })
            return False
            
        self.players.append(ws)
        player_num = len(self.players)
        
        await ws.send_json({
            'type': 'connected',
            'player_num': player_num,
            'message': f'You are Player {player_num}'
        })
        
        print(f"Player {player_num} connected")
        
        if len(self.players) == 2:
            self.game_started = True
            await self.broadcast({
                'type': 'game_start',
                'message': 'Both players connected! Game starting...'
            })
            await self.start_round()
        else:
            await ws.send_json({
                'type': 'waiting',
                'message': 'Waiting for opponent...'
            })
            
        return True
    
    async def unregister(self, ws):
            if ws in self.players:
                player_num = self.players.index(ws) + 1
                self.players.remove(ws)
                print(f"Player {player_num} disconnected")
                
                if self.game_started:
                    await self.broadcast({
                        'type': 'opponent_left',
                        'message': f'Player {player_num} left the game'
                    })
                    
                self.reset_game()
                
    def reset_game(self):
        self.players = []
        self.choices = {}
        self.scores = [0, 0]
        self.game_started = False
        
    async def start_round(self):
        self.choices = {}
        await self.broadcast({
            'type': 'round_start',
            'message': 'Make your choice!',
            'scores': self.scores
        })
        
    async def handle_choice(self, ws, choice):
        if ws not in self.players:
            return
            
        player_idx = self.players.index(ws)
        self.choices[player_idx] = choice
        
        await ws.send_json({
            'type': 'choice_made',
            'choice': choice,
            'message': f'You chose {choice}'
        })
        
        if len(self.choices) == 2:
            await self.determine_winner()
    
    async def determine_winner(self):
        p1_choice = self.choices[0]
        p2_choice = self.choices[1]
        
        if p1_choice == p2_choice:
            result = 'tie'
            winner = None
        else:
            wins = {'rock': 'scissors', 'scissors': 'paper', 'paper': 'rock'}
            if wins[p1_choice] == p2_choice:
                result = 'win'
                winner = 0
                self.scores[0] += 1
            else:
                result = 'win'
                winner = 1
                self.scores[1] += 1
                
        for idx, player in enumerate(self.players):
            if result == 'tie':
                player_result = 'tie'
            elif winner == idx:
                player_result = 'win'
            else:
                player_result = 'lose'
                
            await player.send_json({
                'type': 'result',
                'result': player_result,
                'your_choice': self.choices[idx],
                'opponent_choice': self.choices[1-idx],
                'scores': self.scores
            })
            
    async def broadcast(self, message):
        if self.players:
            await asyncio.gather(
                *[player.send_json(message) for player in self.players if not player.closed],
                return_exceptions=True
            )

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    game_server = request.app['game_server']
    registered = await game_server.register(ws)
    
    if not registered:
        return ws
    
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                
                if data['type'] == 'choice':
                    await game_server.handle_choice(ws, data['choice'])
                elif data['type'] == 'play_again':
                    if len(game_server.players) == 2:
                        await game_server.start_round()
                        
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
    finally:
        await game_server.unregister(ws)
    
    return ws

async def serve_file(request, filename, content_type):
    # CHÚ Ý: Dùng basename để chặn việc truy cập ngược thư mục (vd: ../../password.txt)
    safe_filename = os.path.basename(filename) 
    file_path = os.path.join(os.path.dirname(__file__), safe_filename)
    
    if not os.path.exists(file_path):
        return web.Response(text=f"Error: {filename} not found", status=404)
    
    # Xử lý file ảnh (binary)
    if content_type and content_type.startswith('image/'):
        with open(file_path, 'rb') as f:
            content = f.read()
        return web.Response(body=content, content_type=content_type)
    
    # Xử lý file text
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return web.Response(text=content, content_type=content_type)

async def http_handler(request):
    return await serve_file(request, 'index.html', 'text/html')

async def css_handler(request):
    return await serve_file(request, 'style.css', 'text/css')

async def js_handler(request):
    return await serve_file(request, 'game.js', 'application/javascript')

async def image_handler(request):
    filename = request.match_info['filename']
    content_type, _ = mimetypes.guess_type(filename)
    return await serve_file(request, filename, content_type)


async def main():
    game_server = RPSGameServer()
    
    app = web.Application()
    app['game_server'] = game_server
    app.router.add_get('/', http_handler)
    app.router.add_get('/style.css', css_handler)
    app.router.add_get('/game.js', js_handler)
    app.router.add_get('/{filename:.*\.(png|gif)}', image_handler)
    app.router.add_get('/ws', websocket_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    print("=" * 60)
    print("🎮 Rock Paper Scissors Server Started!")
    print("=" * 60)
    print(f"📱 Local URL: http://localhost:8080")
    print("=" * 60)
    print("⚡ To share with friends, run:")
    print("   ngrok http 8080")
    print("=" * 60)
    print("✅ Server running... Press Ctrl+C to stop")
    print("=" * 60)
    
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")