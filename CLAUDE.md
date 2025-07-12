# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sapyyn is a patient referral system. The repository currently contains:
- A `patient-referral/` directory with various uploaded files (documents, images, QR codes)
- Files appear to be organized by type (medical reports, insurance documents, supporting documents, etc.)

## Repository Structure

```
sapyyn/
├── patient-referral/     # Contains uploaded patient referral documents
│   ├── fileType-*       # Various document types (medical, insurance, supporting docs, etc.)
│   └── messageattachment_* # Message attachments
├── test.PNG             # Test image file
└── README.md           # Currently empty
```

## Development Setup

Currently, no source code or build configuration files are present in the repository. When implementing the patient referral system, consider:

1. **Technology Stack**: Choose appropriate framework based on requirements (e.g., Node.js/Express, Python/Django, etc.)
2. **File Management**: The system will need to handle various file types including PDFs, images (JPEG, PNG), and other documents
3. **Document Categories**: System should support categorization of documents (medical reports, insurance documents, qualification documents, etc.)

## Important Notes

- The repository appears to be in early stages with no implemented code yet
- Focus on secure handling of patient data and documents when implementing features
- Consider HIPAA compliance and data privacy requirements for patient referral systems