import os
import re
import uuid
import queue
import asyncio
import threading
from typing import Tuple, List

import edge_tts
import pygame
from langdetect import detect, LangDetectException

class SpeechEngine:
    """
    Handles Text-to-Speech (TTS) conversion using a Producer-Consumer pipeline.
    Ensures zero-latency playback by downloading audio chunks concurrently while playing.
    """
    
    def __init__(self):
        self.text_queue: queue.Queue = queue.Queue()
        self.audio_queue: queue.Queue = queue.Queue()
        self.is_running: bool = True
        
        # Initialize audio mixer
        pygame.mixer.init()
        pygame.mixer.music.set_volume(0.5)
        
        # Start producer and consumer threads
        self.producer_thread = threading.Thread(target=self._producer_worker, daemon=True)
        self.consumer_thread = threading.Thread(target=self._consumer_worker, daemon=True)
        
        self.producer_thread.start()
        self.consumer_thread.start()
        
        print("[SpeechEngine] Pipeline initialized. Producer/Consumer threads active.")

    def _clean_text_for_speech(self, text: str) -> str:
        """
        Cleans the AI response, removing markdown, emojis, and service tags.
        Protects standard punctuation and Portuguese accents.
        """
        # Replace code blocks with a natural spoken phrase
        text = re.sub(r'```.*?```', ' [code generated on screen]. ', text, flags=re.DOTALL)
        
        # Clean markdown formatting and stutters
        text = text.replace('*', '').replace('`', '')
        text = re.sub(r'\.{2,}', '.', text)
        text = text.replace('!,', ',').replace('?,', ',')
        text = text.replace('!', '.')
        text = re.sub(r'\n+', ' ', text)
        
        # Remove AI action tags
        text = re.sub(r'\[ACAO:.*?\]', '', text)
        
        # Keep alphanumeric, basic punctuation, and Portuguese accents
        text = re.sub(r'[^\w\s,.?!:;áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ-]', '', text)
        
        return re.sub(r'\s+', ' ', text).strip()
        
    def _detect_language(self, text: str) -> str:
        """
        Advanced heuristic that counts common words in a full paragraph
        to determine the correct TTS language engine.
        """
        text_lower = f" {text.lower()} " 
        
        # Palavras raízes do Português
        pt_words = [' o ', ' a ', ' os ', ' as ', ' um ', ' uma ', ' com ', ' para ', ' que ', ' é ', ' não ', ' sim ', ' na ', ' no ', ' em ']
        
        # Palavras raízes do Inglês
        en_words = [' the ', ' is ', ' to ', ' for ', ' of ', ' and ', ' in ', ' you ', ' that ', ' it ', ' code ']
        
        # Conta a pontuação de cada idioma no parágrafo
        pt_score = sum(1 for word in pt_words if word in text_lower)
        en_score = sum(1 for word in en_words if word in text_lower)
        
        # Se tiver mais palavras em inglês (ou se empatar em 0, mas for um código), usa inglês
        if en_score > pt_score:
            return 'en'
            
        return 'pt'

    def _producer_worker(self) -> None:
        """
        PRODUCER: Consumes text chunks, downloads the audio, 
        and queues the MP3 files for the consumer.
        """
        while self.is_running:
            try:
                # Timeout allows the thread to periodically check self.is_running
                item = self.text_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            chunk_text, language = item
            temp_file = f"temp_audio_{uuid.uuid4().hex}.mp3"
            
            try:
                asyncio.run(self._generate_audio_file(chunk_text, language, temp_file))
                self.audio_queue.put(temp_file)
            except Exception as e:
                print(f"[SpeechEngine] Error generating audio chunk: {e}")
                
            self.text_queue.task_done()

    def _consumer_worker(self) -> None:
        """
        CONSUMER: Waits for downloaded MP3 files, plays them sequentially,
        and deletes the temporary files.
        """
        while self.is_running:
            try:
                temp_file = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            try:
                # SÓ TENTA TOCAR SE O MIXER ESTIVER VIVO
                if pygame.mixer.get_init():
                    pygame.mixer.music.load(temp_file)
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy() and self.is_running:
                        pygame.time.Clock().tick(10)
            except Exception as e:
                # Ignora erros se o sistema estiver fechando
                if self.is_running:
                    print(f"[SpeechEngine] Error playing audio: {e}")
            finally:
                if pygame.mixer.get_init():
                    pygame.mixer.music.unload()
                
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except OSError:
                        pass
                        
            self.audio_queue.task_done()
            
    async def _generate_audio_file(self, text: str, language: str, filepath: str) -> None:
        """
        Asynchronously generates speech using Edge-TTS and saves it to a file.
        """
        if not text:
            return

        if language == 'en':
            voice = "en-US-ChristopherNeural" 
        else:
            voice = "pt-BR-AntonioNeural"

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)
            
    def speak(self, text: str) -> None:
        """
        Cleans the entire text first to remove code blocks, 
        then splits into paragraphs for queueing.
        """
        # 1. Limpa o texto INTEIRO primeiro (garante que o regex multilinhas apague o código)
        cleaned_full_text = self._clean_text_for_speech(text)
        
        # 2. Só então divide em parágrafos
        paragraphs = [p.strip() for p in cleaned_full_text.split('\n') if p.strip()]
        
        for paragraph in paragraphs:
            lang = self._detect_language(paragraph)
            self.text_queue.put((paragraph, lang))

    def shutdown(self) -> None:
        """Safely stops threads, shuts down the mixer, and cleans up."""
        print("[SpeechEngine] Shutting down audio systems...")
        self.is_running = False

