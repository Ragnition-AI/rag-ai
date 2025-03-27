from config import Config
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_together import ChatTogether


class LLM:
    def __init__(self, mode='cloud'):

        self.local_model = Config.OLLAMA_MODEL_ID

        if mode == 'local':
            self.core_llm = ChatOllama(
                model=self.local_model, 
                temperature=0.3
            )
            self.json_llm = ChatOllama(
                model=self.local_model, 
                temperature=0.3, 
                format="json"
            )
        elif mode == 'cloud':
            self.core_llm = ChatGoogleGenerativeAI(
                model='gemini-2.0-flash',
                temperature=0.3
            )
            # ChatTogether is bugged and is not working on latest (3.xx somthing)
            # Currently using refs/pr for package fix (someguy)
            json_llm = ChatTogether(
                model='meta-llama/Llama-3.3-70B-Instruct-Turbo-Free', 
                temperature=0, 
                api_key=Config.TOGETHER_API_KEY
            )
            # also the bind function is not working as it seems to
            # so prompting the llm to be strict (ref - Prompts Class)
            self.json_llm = json_llm.bind(response_format={"type": "json_object"})