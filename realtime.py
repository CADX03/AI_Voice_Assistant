#!/usr/bin/env python
# -*- coding: utf-8 -*- # Add this line for Portuguese characters in comments/strings

# Copyright 2019 Google LLC
# Adapted for Portuguese (Portugal) real-time STT testing

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Aplicação de exemplo da API Google Cloud Speech usando a API de streaming.

NOTA: Este módulo requer as dependências `google-cloud-speech` e
`sounddevice`. Para instalar usando pip:

    pip install google-cloud-speech sounddevice numpy

Exemplo de uso:
    python realtime_stt_pt_pt.py
"""

import time
import queue
import re
import sys
import threading

import sounddevice as sd
import numpy  # Certifique-se que NumPy está importado

from google.cloud import speech

# --- Configuração ---
# Parâmetros de gravação de áudio
RATE = 16000
CHUNK = int(RATE / 10)  # Blocos de 100ms
# Configuração da API Google Cloud Speech
LANGUAGE_CODE = "pt-PT"  # Código de idioma BCP-47 para Português (Portugal)

# Uma flag para sinalizar quando o fluxo do microfone deve parar
stop_event = threading.Event()

class MicrophoneStream:
    """Abre um fluxo de gravação como um gerador que produz blocos de áudio."""

    def __init__(self, rate: int, chunk: int):
        self._rate = rate
        self._chunk = chunk

        # Cria um buffer de dados de áudio seguro para threads (thread-safe)
        self._buff = queue.Queue()
        self.closed = True
        self._audio_stream = None
        self._audio_interface = None # Mantém registo da interface de áudio

    def __enter__(self):
        self.closed = False
        # Usa o dispositivo padrão
        try:
            self._audio_interface = sd.InputStream(
                channels=1,
                samplerate=self._rate,
                dtype='int16', # A API Google espera PCM de 16 bits
                blocksize=self._chunk,
                callback=self._fill_buffer,
            )
            self._audio_stream = self._audio_interface.__enter__() # Entra manualmente no contexto
            print("Fluxo do microfone aberto.")
        except Exception as e:
            print(f"Erro ao abrir o fluxo do microfone: {e}", file=sys.stderr)
            print("Verifique se um microfone está conectado e configurado como padrão.", file=sys.stderr)
            raise # Re-lança a exceção para parar a execução
        return self

    def __exit__(self, type, value, traceback):
        if self._audio_stream and self._audio_interface:
             self._audio_interface.__exit__(type, value, traceback) # Sai manualmente do contexto
        self.closed = True
        # Sinaliza o gerador para terminar para que o método
        # streaming_recognize do cliente não bloqueie o término do processo.
        self._buff.put(None)
        print("Fluxo do microfone fechado.")


    def _fill_buffer(self, indata, frames, time, status):
        """Coleta continuamente dados do fluxo de áudio para o buffer."""
        if status:
            print(f"Estado do áudio: {status}", file=sys.stderr)
        # Usa fila LIFO para lidar com buffers a transbordar. Descarta dados se a fila estiver cheia.
        try:
            # Converte array numpy para bytes
            self._buff.put(indata.tobytes(), block=False)
        except queue.Full:
            # print("Buffer cheio, a descartar frames", file=sys.stderr)
            pass # Descarta silenciosamente se o buffer estiver cheio


    def generator(self):
        """Produz blocos de áudio a partir do buffer."""
        while not self.closed and not stop_event.is_set():
            # Usa um get() bloqueante para garantir que há pelo menos um bloco de
            # dados, e para a iteração se o bloco for None, indicando o
            # fim do fluxo de áudio.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Agora consome quaisquer outros dados que ainda estejam no buffer.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def listen_print_loop(responses):
    """Itera através das respostas do servidor e imprime-as.

    As 'responses' passadas são um gerador que bloqueará até que uma resposta
    seja fornecida pelo servidor.

    Cada resposta pode conter múltiplos resultados, e cada resultado pode conter
    múltiplas alternativas; para detalhes, veja https://goo.gl/tjCPAU. Aqui nós
    imprimimos apenas a transcrição para a melhor alternativa do primeiro resultado.

    Neste caso, as respostas são fornecidas também para resultados provisórios. Se a
    resposta for provisória, imprime um avanço de linha no final, para permitir
    que o próximo resultado a sobrescreva, até que a resposta seja final. Para a
    final, imprime uma nova linha para preservar a transcrição finalizada.
    """
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # A lista `results` é consecutiva. Para streaming, só nos interessa
        # o primeiro resultado a ser considerado, pois uma vez que seja `is_final`,
        # passa a considerar a próxima elocução.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Exibe a transcrição da melhor alternativa.
        transcript = result.alternatives[0].transcript

        # Exibe resultados provisórios, mas com um retorno de carro no final da
        # linha, para que linhas subsequentes os sobrescrevam.
        #
        # Se o resultado anterior foi mais longo que este, precisamos imprimir
        # alguns espaços para sobrescrever o resultado anterior.
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)

            # Sai do reconhecimento se alguma das frases transcritas for
            # uma das nossas palavras-chave. Use 'sair' ou 'terminar'.
            if re.search(r"\b(sair|terminar)\b", transcript, re.I):
                print("A sair...")
                stop_event.set() # Sinaliza o fluxo do microfone para parar

            num_chars_printed = 0


def main():
    """Inicia o reconhecimento de fala por streaming."""
    print("A conectar à API Google Cloud Speech...")
    # Configurações específicas do idioma aqui
    client = speech.SpeechClient()

    recognition_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=LANGUAGE_CODE, # Configurado para pt-PT
        enable_automatic_punctuation=True, # Opcional: Adiciona pontuação automática
        # model="telephony", # Opcional: Especificar modelo (telephony, medical, etc.)
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=recognition_config, interim_results=True # Habilita resultados provisórios
    )

    print(f"Configuração do microfone: {RATE}Hz, {CHUNK} amostras/bloco")
    print(f"Configuração da API: Idioma={LANGUAGE_CODE}, Resultados provisórios=True")
    print("\nDiga 'sair' ou 'terminar' para parar.")
    print("A escutar... Pressione Ctrl+C para parar.\n")

    try:
        with MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()
            requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )

            responses = client.streaming_recognize(streaming_config, requests)

            # Agora, usa as respostas de transcrição.
            listen_print_loop(responses)

    except Exception as e:
        print(f"\nOcorreu um erro: {e}")
        print("Por favor, certifique-se que:")
        print("1. Tem ligação à internet.")
        print("2. A API Google Cloud Speech está ativa no seu projeto.")
        print("3. A variável de ambiente GOOGLE_APPLICATION_CREDENTIALS está definida corretamente.")
        print("4. O seu microfone está a funcionar e selecionado como entrada padrão.")
        print("5. Instalou as bibliotecas necessárias: pip install google-cloud-speech sounddevice numpy")
    except KeyboardInterrupt:
        print("\nA parar...")
    finally:
        stop_event.set() # Garante que o fluxo do microfone para se o loop terminar/interromper


if __name__ == "__main__":
    main()