import uvicorn

from rag.data_utils.vectorstore import db
from rag.data_utils.document import doc_handler
from rag.api import app
from rag.utils import get_all_files



if __name__ == "__main__":
    
    while(True):
        opt = int(input("1:Process Data  2:Run Server  3:List Files\nEnter the option to run : "))
        if opt == 1:
            unfiles = get_all_files('/teamspace/studios/this_studio/notes')
            for file in unfiles:
                doc = doc_handler.convert(file)
                for d in doc:
                    db.add_datas(d)
        elif opt == 2:
            uvicorn.run(app, host="0.0.0.0", port=5000)
        elif opt == 3:
            files = db.list_documents()
            for f in files:
                print(f)
        else:
            pass

        print("\n")

    """while(True):
        file = input("Enter : ")
        doc = doc_handler.convert(file)
        for d in doc:
            db.add_datas(d)"""

    """res = db.search('market structure')
    for i in res:
        print(i.page_content)"""

    """ai = AI()
    while(True):
        query = input("Enter query : ")
        ai.generate(query)"""

    print(db.list_documents())