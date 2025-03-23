from langgraph.graph import StateGraph
from langgraph.graph import END

from .types import GraphState

from .funcs import web_search, retrieve, grade_documents, generate, route_question, \
    grade_generation_v_documents_and_question, decide_to_generate, simple_generate



class AI:
    workflow: StateGraph
    state: dict  # To store chat history between calls

    def __init__(self):
        self.state = {"chat_history": []}
        
        self.workflow = StateGraph(GraphState)

        self.workflow.add_node("websearch", web_search)
        self.workflow.add_node("retrieve", retrieve)
        self.workflow.add_node("grade_documents", grade_documents)
        self.workflow.add_node("generate", generate)
        self.workflow.add_node("simple_generate", simple_generate)

        self.workflow.set_conditional_entry_point(
            route_question,
            {
                "websearch": "websearch",  # key - node
                "vectorstore": "retrieve",
                "generate": "simple_generate"
            },
        )
        self.workflow.add_edge("websearch", "generate")
        self.workflow.add_edge("retrieve", "grade_documents")
        self.workflow.add_conditional_edges(
            "grade_documents",
            decide_to_generate,
            {
                "websearch": "websearch",
                "generate": "generate",
            },
        )
        self.workflow.add_conditional_edges(
            "generate",
            grade_generation_v_documents_and_question,
            {
                "not supported": "generate",
                "useful": END,
                "not useful": "websearch",
                "max retries": END,
            },
        )

        self.workflow.add_edge(
            "simple_generate",
            END
        )

        self.graph = self.workflow.compile()
        

    def generate(self, query, max_retries=3):
        """
        Generate a response for the given query while maintaining chat history
        Args:
            query (str): User query
            max_retries (int): Maximum number of retries
        Returns:
            str: Generated response
        """
        # Add user query to chat history
        self.state["chat_history"].append({"role": "human", "content": query})
        
        input_state = {
            "question": query,
            "max_retries": max_retries,
            "chat_history": self.state["chat_history"],
            "loop_step": 0,
        }
        
        # Process through the graph
        final_state = None
        for event in self.graph.stream(input_state, stream_mode="values"):
            #print(event)
            final_state = event
        
        if final_state and "generation" in final_state:
            response = final_state["generation"].content
            print(response)
            # Update the persistent chat history with the assistant's response
            self.state["chat_history"].append({"role": "assistant", "content": response})
            
            # If we got an updated chat history from the graph, use that
            if "chat_history" in final_state:
                self.state["chat_history"] = final_state["chat_history"]
                
            return response
        
        return "I couldn't generate a response. Please try again."