import os
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, UnstructuredPowerPointLoader, TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from exception import UnsupportedFileTypeError, handle_rag_errors


embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".txt": TextLoader,
}


@handle_rag_errors("build_retriever")
def build_retriever(file_path: str):
    """Builds a retriever for the given file. Called at runtime per-request,
    NOT at module load time, because we don't know the file path in advance."""
    ext = os.path.splitext(file_path)[1].lower()
    loader_class = LOADER_MAP.get(ext)
    if loader_class is None:
        raise UnsupportedFileTypeError(f"Unsupported file type: {ext}")

    loader = loader_class(file_path)
    document = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(document)

    vectorstore = FAISS.from_documents(chunks, embedding_model)
    return vectorstore.as_retriever(search_kwargs={"k": 4})