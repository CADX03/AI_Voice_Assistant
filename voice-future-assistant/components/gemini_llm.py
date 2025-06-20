import unicodedata
from google.cloud import storage 
from google import genai
from google.genai import types
from typing import Optional
from components.llm_base import LLMBase 
import os
import time
import json 
import re  

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "api_keys/voice-future-google.json")

GCS_BUCKET_NAME = "bucket_voice_future_madrid"
GCS_BLOB_NAME = "dataset.json"

def carregar_dados_pedidos_do_gcs(bucket_name, blob_name, project_id="voicefuture"):
    """Carrega o arquivo JSON de pedidos do GCS e o estrutura."""
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        print(f"INFO: Tentando baixar {blob_name} do bucket {bucket_name}...")
        json_data_string = blob.download_as_text()
        print("INFO: Download do dataset.json concluído. Processando JSON...")
        
        todos_os_pedidos = json.loads(json_data_string)
        print(f"INFO: Dados dos pedidos carregados com sucesso. Total de chaves de pedido: {len(todos_os_pedidos)}")
        return todos_os_pedidos
    except Exception as e:
        print(f"ERRO: Erro ao carregar dados dos pedidos do GCS: {e}")
        return {} 

class GeminiLLM(LLMBase):
    def __init__(self):
        super().__init__() 
        try:
            self.client = genai.Client(
                vertexai=True, 
                project="voicefuture",
                location="europe-southwest1",
            )
            print("INFO: genai.Client (vertexai=True) inicializado.")
        except Exception as e:
            print(f"ERRO FATAL: Falha ao inicializar genai.Client: {e}")
            self.client = None

        self.model = "gemini-2.0-flash-001"
        
        if not hasattr(self, 'system_prompt'):
            print("AVISO: self.system_prompt não definido. Usando um valor padrão ou vazio.")
            self.system_prompt = "Você é um assistente." 


        self.conversation_history = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=self.system_prompt)]
            ),
        ]
        self.config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT"],
        )
        
        self.interim_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=256,
            response_modalities=["TEXT"],
        )
        
        self.interim_conversation = None
        self.last_interim_text = ""
        self.last_interim_time = 0
        self.interim_cooldown = 2.0
        
        self.dados_pedidos_gcs = carregar_dados_pedidos_do_gcs(GCS_BUCKET_NAME, GCS_BLOB_NAME, project_id="voicefuture")
        
        if self.client: 
            self.initial_response = self.initialize_chat()
        else:
            self.initial_response = "Desculpe, o assistente não pôde ser inicializado corretamente."


    def get_initial_response(self) -> str:
        return self.initial_response

    def process(self, text: str, is_interim: bool = False) -> tuple[bool, str, str]:
        if not self.client: 
            print("ERRO: Cliente genai não inicializado. Não é possível processar.")
            return (False, "Desculpe, estou com um problema técnico no momento.", "")

        if self.should_exit_conversation(text):
            return (True, "Terminando teste segundo pedido", "")
        
        if is_interim:
            return self.process_interim(text)
        else:
            return self.generate_response(text)
            
    def process_interim(self, text: str) -> tuple[bool, str, str]:
        current_time = time.time()
        
        if current_time - self.last_interim_time < self.interim_cooldown:
            return (False, "", "")
            
        if self._is_similar_text(text, self.last_interim_text):
            return (False, "", "")
            
        if self.interim_conversation is None:
            if not hasattr(self, 'interim_system_prompt'):
                self.interim_system_prompt = "Responda brevemente."
            self.interim_conversation = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=self.interim_system_prompt)]
                ),
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="Compreendido.")]
                )
            ]
            
        self.interim_conversation.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=text)]
            )
        )
        
        try:
            response = self.client.models.generate_content( 
                model=self.model,
                contents=self.interim_conversation,
                config=self.interim_config, 
            )
            
            self.last_interim_text = text
            self.last_interim_time = current_time
            
            response_text_val = getattr(response, 'text', "") 

            self.interim_conversation.append(
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=response_text_val)]
                )
            )
            
            if len(self.interim_conversation) > 6: 
                self.interim_conversation = self.interim_conversation[:2] + self.interim_conversation[-4:]
                
            return (False, response_text_val, "")
            
        except Exception as e:
            print(f"Error in interim processing: {str(e)}")
            return (False, "", "")

    def initialize_chat(self):
        if not self.client:
            print("ERRO: Cliente genai não inicializado. Não é possível inicializar chat.")
            return "Desculpe, não consegui iniciar a conversa."
        try:
            if not self.conversation_history: 
                self.conversation_history = [types.Content(role="user", parts=[types.Part.from_text(text=self.system_prompt)])]

            response = self.client.models.generate_content( 
                model=self.model,
                contents=self.conversation_history,
                config=self.config, 
            )
            
            response_text_val = getattr(response, 'text', "Não foi possível obter uma resposta inicial.") 

            self.conversation_history.append(
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=response_text_val)]
                )
            )
            return response_text_val
        except Exception as e:
            print(f"ERRO ao inicializar chat: {e}")
            return "Desculpe, ocorreu um erro ao iniciar."
        
    def convert_numeric_words_to_digits(self, texto: str) -> str:
        """Converte palavras numéricas por extenso para dígitos no texto,
           lidando com palavras concatenadas como 'zerozero' -> '00'."""
        
        substituicoes_ordenadas = [
            (r'zeros', '0'),
            (r'zero', '0'),
            (r'uma', '1'), 
            (r'um', '1'),
            (r'duas', '2'),
            (r'dois', '2'),
            (r'tr[êe]s', '3'),
            (r'quatro', '4'),
            (r'cinco', '5'),
            (r'seis', '6'),
            (r'sete', '7'),
            (r'oito', '8'),
            (r'nove', '9'),
            (r'dez', '10'),
            (r'd[uú]zia', '12'),
        ]
        
        texto_convertido = texto.lower() 
        for palavra_regex, digito in substituicoes_ordenadas:
            texto_convertido = re.sub(palavra_regex, digito, texto_convertido, flags=re.IGNORECASE)
        
        return texto_convertido

    def extract_package_number(self, texto: str) -> Optional[str]:
        print(f"DEBUG: Texto após conversão de palavras numéricas: '{texto}'")

        padroes_contextuais = [
            r"(?:encomenda|pedido|ordem)\s*(?:n[úu]mero|n[º°])?\s*([A-Z0-9\-\s]{3,25})" 
        ]

        for padrao_ctx in padroes_contextuais:
            match_ctx = re.search(padrao_ctx, texto, re.IGNORECASE)
            if match_ctx:
                candidato_bruto_ctx = match_ctx.group(1)
                digitos_do_candidato_ctx = "".join(filter(str.isdigit, candidato_bruto_ctx))
                
                if re.fullmatch(r"\d{3,15}", digitos_do_candidato_ctx):
                    print(f"INFO: Número de encomenda extraído (padrão contextual, apenas dígitos): {digitos_do_candidato_ctx}")
                    return digitos_do_candidato_ctx

        print(f"DEBUG: Buscando por sequências de dígitos genéricas (e.g., \\b\\d{{3,15}}\\b) em '{texto}'")
        matches_genericos = re.findall(r"\b\d{3,15}\b", texto) 
        
        if matches_genericos:
            numero_encomenda_generico = matches_genericos[-1] 
            print(f"INFO: Número de encomenda extraído (padrão genérico \\b\\d{{3,15}}\\b): {numero_encomenda_generico}")
            return numero_encomenda_generico
        
        print(f"INFO: Nenhum número de encomenda (apenas dígitos) extraído de: '{texto}' (original) / processado como '{texto}'")
        return None
    
    # specific email cleaning for spoken portuguese
    def extract_email_in_sentence_pt(self, text: str) -> tuple[str, str]:

        # normalize: remove special portugese characters, lowercase
        norm = unicodedata.normalize("NFKD", text)
        norm = norm.encode("ascii", "ignore").decode("utf-8").lower()

        norm = self.convert_numeric_words_to_digits(norm)

        # replace common spoken parts with symbols
        norm = re.sub(r"\barroba\b", "@", norm)
        norm = re.sub(r"\bponto\b", ".", norm)
        norm = re.sub(r"\btra[cç]o\b", "-", norm)
        norm = re.sub(r"\bh[ií]fen\b", "-", norm)
        norm = re.sub(r"\bunderscore\b", "_", norm)

        # fix spacing around symbols
        norm = re.sub(r"\s*@\s*", "@", norm)
        norm = re.sub(r"\s*\.\s*", ".", norm)
        norm = re.sub(r"\s*-\s*", "-", norm)
        norm = re.sub(r"\s*_\s*", "_", norm)

        # Remove multiple spaces
        norm = re.sub(r"\s+", " ", norm)

        # Match an email-like string
        email_match = re.search(r"([a-z0-9_.+-]+@[a-z0-9-]+\.[a-z.]+)", norm)
        if not email_match:
            print("No email found in the text")
            return None, None

        email = email_match.group(1)
        start, end = email_match.span(1)  # get start and end indices of the match
        cleaned_norm = norm[:start].strip() + " " + norm[end:].strip()  # remove email and trim

        # clean up spaces again in case of extra whitespace after removal
        cleaned_norm = re.sub(r"\s+", " ", cleaned_norm).strip()

        print(f"INFO: Email extraído (padrão contextual): {email}")
        print("Normalized text without email:", cleaned_norm)
        return email, cleaned_norm
    
    def obtain_package_number_details(self, numero_encomenda: str) -> Optional[dict]:
        if not self.dados_pedidos_gcs: 
            print("AVISO: dados_pedidos_gcs não está carregado ou está vazio.")
            return None
        
        if numero_encomenda in self.dados_pedidos_gcs:
            print(f"INFO: Detalhes encontrados para a encomenda (chave exata): {numero_encomenda}")
            return self.dados_pedidos_gcs[numero_encomenda]
        
        chave_sem_hifens = numero_encomenda.replace("-", "") 
        if chave_sem_hifens in self.dados_pedidos_gcs:
            print(f"INFO: Detalhes encontrados para a encomenda (chave sem hifens): {chave_sem_hifens}")
            return self.dados_pedidos_gcs[chave_sem_hifens]

        if numero_encomenda.isdigit():
            chave_com_prefixo_ped = "PED" + numero_encomenda
            if chave_com_prefixo_ped in self.dados_pedidos_gcs:
                print(f"INFO: Detalhes encontrados para a encomenda (chave com prefixo PED): {chave_com_prefixo_ped}")
                return self.dados_pedidos_gcs[chave_com_prefixo_ped]
            
        print(f"INFO: Nenhum detalhe encontrado para a encomenda {numero_encomenda} (ou variações testadas).")
        return None

    # returns all orders associated with the given email
    def obtain_email_details(self, email: str) -> Optional[dict]:
        if not self.dados_pedidos_gcs:
            print("AVISO: dados_pedidos_gcs não está carregado ou está vazio.")
            return None

        email = email.strip().lower()
        pedidos_relacionados = {}

        for chave_pedido, detalhes in self.dados_pedidos_gcs.items():
            email_detalhes = detalhes.get("email", "").strip().lower()
            if email_detalhes == email:
                pedidos_relacionados[chave_pedido] = detalhes

        if pedidos_relacionados:
            print(f"INFO: Foram encontrados {len(pedidos_relacionados)} pedidos associados ao email {email}.")
            return pedidos_relacionados
        else:
            print(f"INFO: Nenhum pedido associado ao email {email} foi encontrado.")
            return None
    
    def generate_response(self, user_input: str) -> tuple[bool, str, str]:
        if self.should_exit_conversation(user_input):
            return(True, "Terminando teste segundo pedido", "")
        
        contexto_adicional_pedido = ""

        email, cleaned_email_user_input = self.extract_email_in_sentence_pt(user_input)
        numero_encomenda_identificado = self.extract_package_number(cleaned_email_user_input if email else user_input)

        if numero_encomenda_identificado:
            detalhes_pedido = self.obtain_package_number_details(numero_encomenda_identificado)
            if detalhes_pedido:
                contexto_adicional_pedido = f"\n\nContexto Adicional da Encomenda {numero_encomenda_identificado}:\n"
                contexto_adicional_pedido += json.dumps(detalhes_pedido, indent=2, ensure_ascii=False)
                print(f"INFO: Contexto adicional para o LLM será adicionado para a encomenda {numero_encomenda_identificado}.")
            else: 
                contexto_adicional_pedido = f"\n\nContexto Adicional da Encomenda {numero_encomenda_identificado}: AVISO IMPORTANTE - A encomenda com o número {numero_encomenda_identificado} NÃO FOI ENCONTRADA no sistema de dados. Informa o cliente sobre isto.\n"
                print(f"INFO: Contexto adicional para o LLM: Encomenda {numero_encomenda_identificado} NÃO ENCONTRADA.")

        if email:
            detalhes_pedido = self.obtain_email_details(email)
            if detalhes_pedido:
                contexto_adicional_pedido = f"\n\nContexto Adicional de Email {email} identificado:\n"
                contexto_adicional_pedido += json.dumps(detalhes_pedido, indent=2, ensure_ascii=False)
                print(f"INFO: Contexto adicional para o LLM será adicionado para o email {email}.")
            else: 
                contexto_adicional_pedido = f"\n\nContexto Adicional do Email {email}: AVISO IMPORTANTE - O email de cliente {email} NÃO FOI ENCONTRADO no sistema de dados. Informa o cliente sobre isto.\n"
                print(f"INFO: Contexto adicional para o LLM: Email {email} NÃO ENCONTRADO.")

        prompt_para_llm = user_input + contexto_adicional_pedido 
        
        print("DEBUG: Prompt para LLM:", prompt_para_llm)

        MAX_HISTORY_TURNS = 100
        MAX_CONVERSATION_ITEMS = 1 + (MAX_HISTORY_TURNS * 2) 
        if len(self.conversation_history) >= MAX_CONVERSATION_ITEMS :
            itens_recentes_a_manter = (MAX_HISTORY_TURNS -1) * 2 
            if itens_recentes_a_manter < 0: itens_recentes_a_manter = 0
            self.conversation_history = self.conversation_history[:1] + self.conversation_history[-itens_recentes_a_manter:]

        self.conversation_history.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt_para_llm)] 
            )
        )
        
        try:
            response = self.client.models.generate_content( 
                model=self.model,
                contents=self.conversation_history,
                config=self.config, 
            )
            
            response_text_val = getattr(response, 'text', "Não foi possível obter uma resposta.") 

            self.conversation_history.append(
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=response_text_val)] 
                )
            )
        except Exception as e:
            print(f"ERRO ao chamar generate_content do Gemini: {e}")
            self.conversation_history.append(
                 types.Content(role="model", parts=[types.Part.from_text(text="Erro ao gerar resposta.")])
            )
            return (False, "Desculpe, ocorreu um erro ao processar o seu pedido.", "")

        self.interim_conversation = None
        
        final_response_flag, filtered_response, json_block = self.check_final_response(response_text_val)
        print(f"\nPrompt (com RAG se aplicável): {prompt_para_llm}")
        print("Assistant Response: ", filtered_response)
        
        return (final_response_flag, filtered_response, json_block)