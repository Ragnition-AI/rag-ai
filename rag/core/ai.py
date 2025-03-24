from langgraph.graph import StateGraph
from langgraph.graph import END

from rag.types import GraphState
from rag.data_utils.pg_db import pgdb

from .funcs import web_search, retrieve, grade_documents, generate, route_question, \
    grade_generation_v_documents_and_question, decide_to_generate, simple_generate



class AI:
    workflow: StateGraph
    state: dict

    def __init__(self):
        self.state = {"chat_history": []}
        
        self.user_graphs = {}

        

    async def get_or_create_graph(self, user_id: str):
        if user_id in self.user_graphs:
            return self.user_graphs[user_id]

        workflow = StateGraph(GraphState)

        workflow.add_node("websearch", web_search)
        workflow.add_node("retrieve", retrieve)
        workflow.add_node("grade_documents", grade_documents)
        workflow.add_node("generate", generate)
        workflow.add_node("simple_generate", simple_generate)

        workflow.set_conditional_entry_point(route_question, {
            "websearch": "websearch",
            "vectorstore": "retrieve",
            "generate": "simple_generate"
        })

        workflow.add_edge("websearch", "generate")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents", 
            decide_to_generate, {
                "websearch": "websearch",
                "generate": "generate",
            }
        )
        workflow.add_conditional_edges(
            "generate", 
            grade_generation_v_documents_and_question, 
            {
                "not supported": "generate", 
                "useful": END, 
                "not useful": "websearch", 
                "max retries": END,
            }
        )
        workflow.add_edge("simple_generate", END)

        compiled_graph = workflow.compile()
        self.user_graphs[user_id] = compiled_graph  # Store compiled graph per user
        return compiled_graph

    async def generate(self, user_id: str, chat_id: str, query: str, max_retries=3):
        await pgdb.get_or_create_user(user_id)
        chat = await pgdb.get_or_create_chat(user_id, chat_id)

        # Append user message
        await pgdb.save_message(chat['chatId'], "human", query)

        input_state = {
            "question": query,
            "max_retries": max_retries,
            "chat_history": await pgdb.get_chat_messages(chat['chatId']),
            "loop_step": 0,
            "user_id": user_id,
            "chat_id": chat['chatId'],
        }

        graph = await self.get_or_create_graph(user_id)  # Fetch cached user-specific graph

        final_state = None
        for event in graph.stream(input_state, stream_mode="values"):
            final_state = event

        if final_state and "generation" in final_state:
            response = final_state["generation"].content
            await pgdb.save_message(chat['chatId'], "assistant", response)
            return response

        return "I couldn't generate a response. Please try again."