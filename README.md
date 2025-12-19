# VNPT AI Hackathon

## Overview
Complete pipeline for processing data, chunking, building a FAISS vector database, and running inference for efficient similarity search.

## Table of Contents
- [Components](#components)
- [Data Flow](#data-flow)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Components
- **Classify Label** 
- **LLM with each role**
    - **LLM for RAG**
    - **LLM for STEM**
    - **LLM for precision-critical**
    - **LLM for Multi-domain and ...**
- **Answer Extraction LLM**
## Reference_data

## Crawl_data_flow

## Prerequisites
- Python 3.8+
- pip (or conda)
- Bash shell
- Recommended: 2GB+ free disk for indexes

## Installation
```bash
git clone <repository-url>
cd VNPT_AI_Hackathon
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
1) Chunk raw data
```bash
bash scripts/chunk.sh
```
2) Build FAISS index
```bash
bash scripts/faiss.sh
```
3) Run inference
```bash
bash scripts/inference.sh
```

## Project Structure
```
VNPT_AI_Hackathon/
├── scripts/
│   ├── chunk.sh       # Data chunking
│   ├── faiss.sh       # Build FAISS index
│   └── inference.sh   # Run inference pipeline
├── data/              # Raw and processed data
├── models/            # Model artifacts
├── src/               # Source code
├── requirements.txt
└── README.md
```

## Troubleshooting
- Ensure virtual environment is activated before running scripts.
- Verify input data paths expected by `chunk.sh`.
- If FAISS build fails, check that system BLAS/FAISS dependencies are installed.

## Contributing
Issues and PRs are welcome. Please include concise descriptions and tests where applicable.

## License
Specify your license (e.g., MIT) in this section.