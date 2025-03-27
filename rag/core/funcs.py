import json

from langchain.schema import Document
from langchain_core.messages import HumanMessage, SystemMessage

from rag.utils import format_doc_text
from rag.data_utils.vectorstore import db
from rag.core.prompts import Prompts
from rag.core.web import web_search_tool

from rag import llm

def retrieve(state):
    """
    Retrieve documents from vectorstore
    Args:
        state (dict): The current graph state
    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]

    documents = db.search(question)
    return {"documents": documents}

def generate(state):
    """
    Generate answer using RAG on retrieved documents, incorporating chat history
    Args:
        state (dict): The current graph state
    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    loop_step = state.get("loop_step", 0)
    chat_history = state.get("chat_history", [])

    # Format chat history for context
    history_text = ""
    if chat_history:
        history_text = "Chat History:\n"
        for msg in chat_history:
            prefix = "Human: " if msg["role"] == "human" else "Assistant: "
            history_text += f"{prefix}{msg['content']}\n"
        history_text += "\n"

    docs_txt = format_doc_text(documents)

    rag_prompt_formatted = Prompts.RAG_PROMPT.format(
        context=docs_txt, 
        question=question,
        chat_history=history_text
    )
    
    generation = llm.core_llm.invoke([HumanMessage(content=rag_prompt_formatted)])
    
    new_chat_history = chat_history.copy()
    new_chat_history.append({"role": "human", "content": question})
    new_chat_history.append({"role": "assistant", "content": generation.content})
    
    return {
        "generation": generation, 
        "loop_step": loop_step + 1,
        "chat_history": new_chat_history
    }

def simple_generate(state):
    """
    Generate answer using LLM incorporating chat history
    Args:
        state (dict): The current graph state
    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    loop_step = state.get("loop_step", 0)
    chat_history = state.get("chat_history", [])

    history_text = ""
    if chat_history:
        history_text = "Chat History:\n"
        for msg in chat_history:
            prefix = "Human: " if msg["role"] == "human" else "Assistant: "
            history_text += f"{prefix}{msg['content']}\n"
        history_text += "\n"

    generation = llm.core_llm.invoke([HumanMessage(content=Prompts.SIMPLE_PROMPT.format(
        question=question,
        chat_history=chat_history
    ))])
    
    new_chat_history = chat_history.copy()
    new_chat_history.append({"role": "human", "content": question})
    new_chat_history.append({"role": "assistant", "content": generation.content})
    
    return {
        "generation": generation, 
        "loop_step": loop_step + 1,
        "chat_history": new_chat_history
    }

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question
    If any document is not relevant, we will set a flag to run web search
    Args:
        state (dict): The current graph state
    Returns:
        state (dict): Filtered out irrelevant documents and updated web_search state
    """
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    chat_history = state.get("chat_history", [])

    # consider chat history when grading documents
    recent_context = question
    if chat_history:
        # get the last few messages to provide context (limiting to avoid token issues)
        recent_messages = chat_history[-4:] if len(chat_history) > 4 else chat_history
        recent_context_parts = [msg["content"] for msg in recent_messages]
        recent_context_parts.append(question)
        recent_context = " ".join(recent_context_parts)

    filtered_docs = []
    web_search = "No"
    for d in documents:
        doc_grader_prompt_formatted = Prompts.DOC_GRADER_PROMPT.format(
            document=d.page_content, question=recent_context
        )
        result = llm.json_llm.invoke(
            [SystemMessage(content=Prompts.DOC_GRADER_INSTRUCTIONS)]
            + [HumanMessage(content=doc_grader_prompt_formatted)]
        )
        grade = json.loads(result.content)["binary_score"]

        if grade.lower() == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            web_search = "Yes"
            continue
    return {"documents": filtered_docs, "web_search": web_search}

def web_search(state):
    """
    Web search based on the question and possibly chat history context
    Args:
        state (dict): The current graph state
    Returns:
        state (dict): Appended web results to documents
    """
    print("---WEB SEARCH---")
    question = state["question"]
    documents = state.get("documents", [])
    chat_history = state.get("chat_history", [])

    search_query = question
    if chat_history:
        last_human_messages = [msg for msg in chat_history[-4:] if msg["role"] == "human"]
        if last_human_messages:
            # Use LLM to create a better search query based on conversation context
            search_context = "\n".join([msg["content"] for msg in last_human_messages])
            search_query_prompt = f"Based on this conversation context:\n{search_context}\n\nAnd this latest question:\n{question}\n\nFormulate the best search query to find relevant information. Give only the query (must):"
            search_query_result = llm.core_llm.invoke([HumanMessage(content=search_query_prompt)])
            search_query = search_query_result.content

    docs = web_search_tool.invoke({"query": search_query})
    web_results = "\n".join([d["content"] for d in docs['results']])
    web_results = Document(page_content=web_results)
    documents.append(web_results)
    return {"documents": documents}

def route_question(state):
    """
    Route question to web search or RAG, considering chat history
    Args:
        state (dict): The current graph state
    Returns:
        str: Next node to call
    """
    print("---ROUTE QUESTION---")
    question = state["question"]
    chat_history = state.get("chat_history", [])
    
    routing_context = question
    if chat_history:
        recent_messages = chat_history[-4:] if len(chat_history) > 4 else chat_history
        history_context = "\n".join([f"{'Human' if msg['role'] == 'human' else 'Assistant'}: {msg['content']}" for msg in recent_messages])
        routing_context = f"Chat history:\n{history_context}\n\nCurrent question: {question}"
    
    route_question = llm.json_llm.invoke(
        [SystemMessage(content=Prompts.ROUTER_INSTRUCTIONS)]
        + [HumanMessage(content=routing_context)]
    )
    source = json.loads(route_question.content)["datasource"]
    
    if source == "websearch":
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return "websearch"
    elif source == "vectorstore":
        print("---ROUTE QUESTION TO RAG---")
        return "vectorstore"
    elif source == "generate":
        print("---ROUTE QUESTION TO LLM---")
        return "generate"

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or add web search
    Args:
        state (dict): The current graph state
    Returns:
        str: Binary decision for next node to call
    """
    print("---ASSESS GRADED DOCUMENTS---")
    web_search = state["web_search"]
    
    if web_search == "Yes":
        print(
            "---DECISION: NOT ALL DOCUMENTS ARE RELEVANT TO QUESTION, INCLUDE WEB SEARCH---"
        )
        return "websearch"
    else:
        print("---DECISION: GENERATE---")
        return "generate"

def grade_generation_v_documents_and_question(state):
    """
    Determines whether the generation is grounded in the document and answers question
    Args:
        state (dict): The current graph state
    Returns:
        str: Decision for next node to call
    """
    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]
    max_retries = state.get("max_retries", 3)  # Default to 3
    loop_step = state.get("loop_step", 0)
    chat_history = state.get("chat_history", [])

    grading_context = question
    if chat_history and len(chat_history) >= 2:
        recent_context = chat_history[-4:-1] if len(chat_history) > 4 else chat_history[:-1]
        context_text = "\n".join([f"{'Human' if msg['role'] == 'human' else 'Assistant'}: {msg['content']}" for msg in recent_context])
        grading_context = f"Chat context:\n{context_text}\n\nQuestion: {question}"

    hallucination_grader_prompt_formatted = Prompts.HALLUCINATION_GRADER_PROMPT.format(
        documents=format_doc_text(documents), generation=generation.content
    )
    result = llm.json_llm.invoke(
        [SystemMessage(content=Prompts.HALLUCINATION_GRADER_INSTRUCT)]
        + [HumanMessage(content=hallucination_grader_prompt_formatted)]
    )
    grade = json.loads(result.content)["binary_score"]

    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        print("---GRADE GENERATION vs QUESTION---")
        answer_grader_prompt_formatted = Prompts.ANSWER_GRADER_PROMPT.format(
            question=grading_context, generation=generation.content
        )
        result = llm.json_llm.invoke(
            [SystemMessage(content=Prompts.ANSWER_GRADER_INSTRUCT)]
            + [HumanMessage(content=answer_grader_prompt_formatted)]
        )
        grade = json.loads(result.content)["binary_score"]
        if grade == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        elif loop_step <= max_retries:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
        else:
            print("---DECISION: MAX RETRIES REACHED---")
            return "max retries"
    elif loop_step <= max_retries:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"
    else:
        print("---DECISION: MAX RETRIES REACHED---")
        return "max retries"