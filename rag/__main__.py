#from rag.data_utils.document import doc_handler
#from rag.data_utils.database import db
import uvicorn
#from rag.core.ai import AI
from rag.api import app

if __name__ == "__main__":
  
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

    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=5000)