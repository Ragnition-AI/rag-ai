import os

from pathlib import Path
from docling.chunking import HybridChunker
from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode, AcceleratorOptions, AcceleratorDevice
from langchain_core.documents import Document

from rag.utils import get_all_files
from config import Config

IMAGE_RESOLUTION_SCALE = 2.0


class DocumentHandler:
    def __init__(self):

        self.chunker = HybridChunker(
            tokenizer=Config.EMBEDDING_MODEL,
            max_tokens=Config.EMBEDDING_TOKENS,
            merge_peers=True,
        )

        self.output_dir = Path('/teamspace/studios/this_studio/RAG/dataset/')

        accelerator_options = AcceleratorOptions(
         num_threads=8, device=AcceleratorDevice.CUDA
        )

        pipeline_options = PdfPipelineOptions(
            accelerator_options = accelerator_options,
            do_table_structure=True,
            #do_ocr=True,
            #ocr_options=TesseractOcrOptions(force_full_page_ocr=True, lang=["eng"]),
            #ocr_options=EasyOcrOptions(force_full_page_ocr=True, lang=["en"]),
            table_structure_options=dict(
                do_cell_matching=False,
                mode=TableFormerMode.ACCURATE
            ),
            generate_page_images=True,
            generate_picture_images=True,
            images_scale=IMAGE_RESOLUTION_SCALE
        )

        format_options = {InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}

        self.processor = DocumentConverter(format_options=format_options)


    def convert(self, file: str, output='chunks') -> list:
        """
        Returns
            documents: list of all processed documents
        """
        processed = []
        if file.startswith('http') or os.path.isfile(file):
            result = self.processor.convert(file)
            processed.append(result.document)
        else:
            # suppose the path is a folder
            files = get_all_files(file)
            results = self.processor.convert_all(files)
            for result in results:
                processed.append(result.document)
            """for file in files:
                result = converter.convert(file)
                processed.append(result.document)"""

        if output == 'md':
            return self.make_markdown(processed)
        elif output == 'chunks':
            return self.make_chunks(processed)
        return []


    def make_markdown(self, docs: list) -> list:
        """
        Args:
            docs: list of processed documents
        Returns:
            files: list of markdown files
        """
        files = []
        for doc in docs:
            markdown = doc.export_to_markdown()
            filename = self.output_dir / 'IEFT_Module_3_Notes.md'
            doc.save_as_markdown(filename, image_mode=ImageRefMode.REFERENCED)
            files.append(markdown)

        return markdown

    def make_chunks(self, files):
        """
        Args:
            files: list of converted files
        Returns:
            chunks: list of file group (list) containing chunks (list)
        """
        file_group = []
        for file in files:
            chunk_iter = self.chunker.chunk(dl_doc=file)
            doc_chunks = []
            for chunk in list(chunk_iter):
                enriched_text = self.chunker.serialize(chunk)
                doc = Document(
                    enriched_text,
                    metadata = {
                        "filename": chunk.meta.origin.filename,
                        "title": chunk.meta.headings[0] if chunk.meta.headings else 'Undefined'
                    }
                )
                doc_chunks.append(doc)
            file_group.append(list(doc_chunks)) 
        
        return file_group

        
doc_handler = DocumentHandler()
