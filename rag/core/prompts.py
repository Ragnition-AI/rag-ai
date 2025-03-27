class Prompts:

    SIMPLE_PROMPT = """Question : {question}
Previous Chats : {chat_history}"""

    RAG_PROMPT = """You are an assistant for question-answering tasks. 

Here is the context to use to answer the question:

{context} 

Think carefully about the above context. 

Now, review the user question:

{question}

Provide an answer to this questions using only the above context. 
After providing answer, ask if the user needs more help.

Here is the previos chat history:
{chat_history}

Answer:"""


    DOC_GRADER_INSTRUCTIONS = """You are a grader assessing relevance of a retrieved document to a user question.

If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant."""


    DOC_GRADER_PROMPT = """Here is the retrieved document: \n\n {document} \n\n Here is the user question: \n\n {question}. 

This carefully and objectively assess whether the document contains at least some information that is relevant to the question.

Return only JSON with single key, binary_score, that is 'yes' or 'no' score to indicate whether the document contains at least some information that is relevant to the question.

eg: {{"binary_score": "answer"}}"""



    ROUTER_INSTRUCTIONS = """You are an expert at routing a user question to a vectorstore or web search or direcly generate response.

The vectorstore contains academic documents, notes, explanations, questions and answers.

Use the vectorstore for questions on these topics. For all else, and especially for current events, use web-search.

For casual talks, you can use generate fucntion

Return only JSON with single key, datasource, that is 'websearch', 'vectorstore' or 'generate' depending on the question.

eg: {{"datasource": "answer"}}"""


    HALLUCINATION_GRADER_INSTRUCT = """

You are a teacher grading a quiz. 

You will be given FACTS and a STUDENT ANSWER. 

Here is the grade criteria to follow:

(1) Ensure the STUDENT ANSWER is grounded in the FACTS. 

(2) Ensure the STUDENT ANSWER does not contain "hallucinated" information outside the scope of the FACTS.

Score:

A score of yes means that the student's answer meets all of the criteria. This is the highest (best) score. 

A score of no means that the student's answer does not meet all of the criteria. This is the lowest possible score you can give.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset."""


    HALLUCINATION_GRADER_PROMPT = """FACTS: \n\n {documents} \n\n STUDENT ANSWER: {generation}. 

Return only JSON with two two keys, binary_score is 'yes' or 'no' score to indicate whether the STUDENT ANSWER is grounded in the FACTS. And a key, explanation, that contains an explanation of the score.

eg: {{"binary_score": "answer", "explanation": "answer"}}"""


    ANSWER_GRADER_INSTRUCT = """You are a teacher grading a quiz. 

You will be given a QUESTION and a STUDENT ANSWER. 

Here is the grade criteria to follow:

(1) The STUDENT ANSWER helps to answer the QUESTION

Score:

A score of yes means that the student's answer meets all of the criteria. This is the highest (best) score. 

The student can receive a score of yes if the answer contains extra information that is not explicitly asked for in the question.

A score of no means that the student's answer does not meet all of the criteria. This is the lowest possible score you can give.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset."""


    ANSWER_GRADER_PROMPT = """QUESTION: \n\n {question} \n\n STUDENT ANSWER: {generation}. 

Return only JSON with two two keys, binary_score is 'yes' or 'no' score to indicate whether the STUDENT ANSWER meets the criteria. And a key, explanation, that contains an explanation of the score.

eg: {{"binary_score": "answer", "explanation": "answer"}}"""