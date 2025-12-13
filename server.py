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