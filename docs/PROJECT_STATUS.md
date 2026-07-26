# KnowledgeHub AI - Project Status

## Current milestone

Reliable PDF ingestion API.

## Completed

- FastAPI project initialized
- Health endpoint available
- PDF upload endpoint available
- File extension validation
- MIME-type validation
- Empty-file validation
- Maximum-size validation
- PDF signature validation
- PDF text extraction
- Encrypted-PDF rejection
- Structured application logs
- Saved-file cleanup after processing failure

## Current limitations

- Uploaded files are read fully into memory
- Files are stored on the local filesystem
- Only PDF files are supported
- Extracted text is not persisted
- No automated tests yet
- No database
- No background processing
- No embeddings or retrieval

## Next likely milestone

Add focused automated tests for the existing ingestion flow.

Potential tests:

- health endpoint,
- successful PDF upload,
- invalid extension,
- invalid MIME type,
- empty file,
- fake PDF signature,
- corrupted PDF,
- encrypted PDF.
