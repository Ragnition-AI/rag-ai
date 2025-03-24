import uvicorn
from rag.api import app



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
    """files = doc_handler.convert('/teamspace/studios/this_studio/dataset/IEFT_Module_3_Notes.pdf')
    for file in files:
        db.add_datas(file)"""

    """res = db.search('market structure')
    for i in res:
        print(i.page_content)"""

    """ai = AI()
    while(True):
        query = input("Enter query : ")
        ai.generate(query)"""