# Architecture

This document describes the system **as it exists today**. It is updated
only when components, responsibilities, or data flow actually change (see
`docs/DECISIONS.md` for why a change was made, and `docs/ROADMAP.md` for
what hasn't been built yet).

## Layering

The codebase is split into four layers with a strict dependency direction:
`api` depends on `services` and `schemas`, `services` depends on nothing
above it, and `core` is shared by everyone.

```mermaid
flowchart TD
    subgraph API["app/api"]
        documents["documents.py<br/>FastAPI router"]
    end

    subgraph Schemas["app/schemas"]
        schema["document.py<br/>Pydantic request/response models"]
    end

    subgraph Services["app/services"]
        service["document_service.py<br/>save_document / extract_text (dispatcher) / persist_metadata"]
    end

    subgraph Core["app/core"]
        config["config.py<br/>Settings"]
        logging_["logging.py<br/>configure_logging"]
    end

    documents --> schema
    documents --> service
    documents --> config
    documents --> logging_
    service --> logging_
```

**Why this split:**

- `api/` only translates HTTP in and out - validation of the *shape* of a
  request, calling a service, mapping results/exceptions to status codes.
  It has no PDF-parsing or filesystem logic in it.
- `services/` holds the actual business logic (how a PDF is stored, how
  text is extracted) so it can be tested or reused without spinning up
  HTTP at all.
- `schemas/` defines the response contract independently of both, so the
  API's public shape doesn't leak internal service types.
- `core/` holds things every layer needs (configuration, logging) without
  those layers needing to know about each other.

This is a deliberate, small-scale version of the classic controller /
service / model split - chosen now because the project already has
validation logic that doesn't belong in a route handler, not because
"layered architecture" is a goal in itself.

## Request flow: `POST /documents/upload`

```mermaid
sequenceDiagram
    participant Client
    participant Router as documents.py
    participant Service as DocumentService
    participant Extractor as format extractor

    Client->>Router: multipart upload
    Router->>Router: look up extension in SUPPORTED_FORMATS
    Router->>Router: validate MIME type, size, signature (if the format defines one)
    Router->>Service: save_document(file, upload_directory, extension)
    Service-->>Router: saved file path (UUID-named, real extension preserved)
    Router->>Service: extract_text(path)
    Service->>Service: look up extractor by extension
    Service->>Extractor: _extract_pdf(path) or _extract_plain_text(path)
    Extractor-->>Service: (text, page_count)
    alt unsupported / unreadable / undecodable
        Service-->>Router: raise ValueError
        Router->>Router: delete saved file
        Router-->>Client: 422
    else success
        Service-->>Router: (text, page_count)
        Router->>Service: persist_metadata(DocumentRecord, upload_directory)
        Service-->>Router: sidecar path (<document_id>.json)
        Router-->>Client: 201 DocumentUploadResponse
    end
```

Validation is intentionally layered defense-in-depth, in this order:
extension -> MIME type -> emptiness -> size -> file signature (only for
formats that define one) -> actual parse. Cheap, client-controllable
checks run first so obviously bad requests fail fast before any file I/O
happens.

## Current constraints (by design, for now)

- **Storage:** local filesystem under `uploads/`, filenames are generated
  UUIDs (never trust user-supplied filenames for paths).
- **Memory:** the full upload is read into memory before validation. Fine
  at current file-size limits (10 MB default); will need streaming if
  large-file support is added later.
- **State:** extracted text and metadata are persisted as a JSON sidecar
  file (`uploads/<document_id>.json`) via `DocumentRecord` +
  `DocumentService.persist_metadata`. This is deliberately not a database
  yet - there's nothing to query across documents until Phase 3 needs it.
- **Formats:** PDF, TXT, and Markdown are supported via a registry
  (`SUPPORTED_FORMATS`, a `dict[str, DocumentFormat]`) that both the
  router (for validation) and `DocumentService` (for extraction) read
  from. Adding DOCX/PPTX/HTML means adding one registry entry and one
  extractor method - the router's validation logic doesn't grow per
  format. Text formats have no signature check, since plain text has no
  reliable magic bytes; a mislabeled file that happens to decode as
  UTF-8 would currently be silently accepted.

## Where this goes next

Per `docs/ROADMAP.md`, the next architectural additions (each will update
this file when they land) are:

1. **More formats** - DOCX, PPTX, and HTML through the same
   `SUPPORTED_FORMATS` registry and extractor dispatch already in place.
2. **A real database** - once something needs to query or list across
   documents rather than looking up one JSON file at a time, the sidecar
   files get replaced by a database and likely a `repositories/` layer.
3. **Chunking + embeddings** - a new service that turns stored text into
   vector-ready chunks.
4. **Retrieval** - a vector store dependency and a query-time service.
5. **RAG / agents** - orchestration on top of retrieval, likely LangGraph.

Each addition should be evaluated against the same question used to build
this layer split: does it belong in `api`, `services`, or `core`, and does
it introduce a new layer only if the existing ones can't reasonably hold
it.
