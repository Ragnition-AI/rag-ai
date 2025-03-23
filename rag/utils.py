import os




def get_all_files(root_folder):
    file_paths = []

    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            file_paths.append(full_path)
    
    return file_paths


def format_doc_text(docs:list):
    """
    Returns formatted text from multiple documents
    """
    return "\n\n".join(doc.page_content for doc in docs)