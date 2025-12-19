# VNPT AI Hackathon

## Overview

This pipeline provides a complete solution for processing data, chunking text, building a FAISS vector database, and running inference for efficient similarity search. It is designed to handle multiple-choice questions (MCQs) across various domains, with advanced support for STEM (Science, Technology, Engineering, and Mathematics) questions through multi-step reasoning.  

The system is optimized for the Vietnamese context, enabling fast and accurate retrieval and answer generation while leveraging both retrieval-augmented and domain-adaptive strategies.


## Table of Contents
- [Components](#components)
- [Data Flow](#data-flow)
- [General Pipeline](#general-pipeline)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Docker Hub](#docker-hub)
- [Usage](#usage)

## Components
- **Question Classification**: Automatically classify MCQs into labels (e.g., STEM, RAG, Precision-Critical, Multi-Domain) using LLM.
- **LLM with Specialized Roles**:
    - **LLM for RAG**: Retrieval-Augmented Generation for factual questions requiring external knowledge.
    - **LLM for STEM**: Multi-phase reasoning for science/math questions (Question-Driven or Answer-Validation modes).
    - **LLM for Precision-Critical**: Safe handling of sensitive or harmful queries.
    - **LLM for Multi-Domain**: Adaptive processing for general knowledge questions.
- **Answer Extraction LLM**: Post-process raw LLM outputs to extract final answers.
- **RAG System**: FAISS-based vector search for context retrieval.
- **Data Processing**: Chunking, embedding, and indexing for efficient search.

## Pipeline Flow
1. **Input**: Raw MCQ dataset (JSON with qid, question, choices).
2. **Classification**: Use LLM to classify questions into labels (STEM, RAG, etc.).
3. **Separation**: Split data by label into separate files.
4. **Inference**:
   - For STEM: Classify mode (Question-Driven/Answer-Validation), apply multi-phase reasoning, fallback if needed.
   - For Multi-Domain: Gate decision for retrieval external content or not, then feed to LLM.
   - For others: Direct LLM prediction with corresponding role.
5. **Post-Processing**: Extract answer letters (A/B/C/...), handle errors.
6. **Output**: CSV with qid and predicted answer.

## General Pipeline
```mermaid
flowchart TD

    %% Input
    U[User MCQ question and options and context]
    U --> PRE[Preprocessing]

    %% Classification
    PRE --> CLF[Question Classifier]

    %% Routing
    CLF -->|Precision Critical| PC_ENTRY
    CLF -->|RAG| RAG_ENTRY
    CLF -->|Multi Domain| MD_ENTRY
    CLF -->|STEM| STEM_ENTRY

    %% Precision Critical
    subgraph PRECISION_CRITICAL
        PC_ENTRY --> PC_OUT[Select refusal option]
    end

    %% RAG branch
    subgraph RAG
        RAG_ENTRY --> RG1[Split given context]
        RG1 --> RG2[Embed question]
        RG2 --> RG3[Embed chunks]
        RG3 --> RG4[Similarity retrieval]
        RG4 --> RG5[Large model answering]
        RG5 --> RAG_OUT[RAG answer]
    end

    %% Multi Domain branch
    subgraph MULTI_DOMAIN
        MD_ENTRY --> C{Need RAG?}
        C -->|No| L1[Send Question to LLM]
        C -->|Yes| S[Search Vector DB]
        S --> D{DB Contains Knowledge?}
        D -->|No| L2[Skip RAG and send Question to LLM]
        D -->|Yes| R[RAG Retrieval]
        R --> MD_OUT[LLM Answer Using Retrieved Context]
    end

    %% STEM branch
    subgraph STEM
        STEM_ENTRY --> ST1[Classify]
        ST1 -->|Question-Driven| ST2[Question-Driven Mode]
        ST1 --> |Answer Validation| ST3[Answer Validation Mode]
        ST2 --> ST_OUT[STEM answer]
        ST3 --> ST_OUT
    end

    %% Post processing
    PC_OUT --> POST[Post processing]
    RAG_OUT --> POST
    MD_OUT --> POST
    ST_OUT --> POST

    POST --> FINAL[Final Answer]

    %% ============================================
    %% === COLOR STYLES ===========================
    %% ============================================

    %% Category blocks
    classDef pc fill:#f8d7da,stroke:#c53030,stroke-width:1px,color:#000;
    classDef rag fill:#d1ecf1,stroke:#0c5460,stroke-width:1px,color:#000;
    classDef md fill:#fff3cd,stroke:#856404,stroke-width:1px,color:#000;
    classDef stem fill:#e2e3e5,stroke:#6c757d,stroke-width:1px,color:#000;

    %% Special highlight
    classDef post fill:#d4edda,stroke:#155724,stroke-width:1px,color:#000;
    classDef inputNode fill:#fde2ff,stroke:#7a057a,stroke-width:1px,color:#000;

    %% Assign classes
    class U,PRE,CLF inputNode;
    class PC_ENTRY,PC_OUT pc;
    class RAG_ENTRY,RG1,RG2,RG3,RG4,RG5,RAG_OUT rag;
    class MD_ENTRY,C,L1,S,D,L2,R,MD_OUT md;
    class STEM_ENTRY,ST1,ST2,ST_OUT,ST3, stem;
    class POST,FINAL post;
```
## RAG Pipeline

The **Retrieval-Augmented Generation (RAG) Pipeline** answers factual questions by retrieving relevant information from external data sources.

### Flow:
1. Extract context from the original question and split it into paragraphs.  
2. Embed the question and paragraphs using `Embedding_VNPTAI`.  
3. Compute similarity between the question and each paragraph; keep the top-k most relevant paragraphs.  
4. Concatenate the retrieved passages and feed them to the LLM using `SYSTEM_RAG_PROMPT` and `USER_RAG_PROMPT`.  
5. Map the model’s output to the final choice label via [utils/post_processing.py](utils/post_processing.py).

---

## Multi-Domain Pipeline

The **Multi-Domain Pipeline** handles heterogeneous questions, dynamically deciding whether to use RAG, and adapts responses accordingly.

### Key Features:
- **Gate Decision**: The LLM automatically determines:  
  - **Need RAG** – whether the question can be answered using the LLM’s base knowledge or requires external information.  
  - **Domain** – identifies the domain of the question. If supported by external knowledge, relevant content is retrieved.  
- **Faiss Similarity Search** for retrieving relevant context.

### Flow:
1. Receive input consisting of a question and choices. Feed the question into the Gate Decision module to get `use_rag` and `domain`.  
2. If `use_rag=True` and the domain is supported, retrieve context using Faiss similarity search.  
3. Prompt selection:  
   - If context exists → use `SYSTEM_RAG_PROMPT` + `USER_RAG_PROMPT` with `<INFORMATION>` to build the RAG prompt for the LLM.  
   - If no context → fall back to `GENERAL_SYSTEM_PROMPT` without additional context.  
4. Map the generated answer to the corresponding letter choice via post-processing.

### Fallback Mechanisms:
- Gate parsing uses robust JSON extraction; if it fails, defaults to `use_rag=False`.  
- If retrieval returns no passages, the model continues in non-RAG mode.

### Supported Domains:
- Law  
- Ho Chi Minh-related knowledge  
- Medical  
- Political science  
- Civic knowledge  

---

## Precision-Critical Pipeline

The **Precision-Critical Pipeline** ensures safety by refusing to answer unsafe questions. Questions classified as Precision-Critical must trigger the refusal option.

### Flow:
1. Classify questions as “Precision-Critical” for unsafe, harmful, or how-to intents.  
2. Use `PR_SYSTEM_PROMPT` to instruct the model to strictly refuse and select the refusal choice.  
3. Map the output text to the corresponding choice letter.

### Behavioral Rules:
- Always select the refusal option for disallowed questions.  
- Do not generate instructions or content that could facilitate harm.  
- Output is constrained to a single answer string; no explanations.

## STEM Processing Pipeline

The STEM module (`stem_solver/`) handles questions in Science, Technology, Engineering, and Mathematics (STEM), using structured multi-phase reasoning to ensure **high accuracy** and reduce errors.

### Key Features
- **Mode Classification**: Automatically determines if the question is:
  - **Question-Driven** – solve independently of the choices, then compare with choices.
  - **Answer-Validation (Choice-Driven)** – solve while **considering each choice as a hypothesis**.
- **Multi-Phase Reasoning**: Breaks down solving into phases for clarity and verification.
- **Fallback Mechanism**: Activated when the model's generated result does not match any of the given choices. This usually indicates that the model could not extract some hidden knowledge needed for calculation, or the problem is missing necessary data.
- **Robustness**: Handles retries, JSON parsing, and edge cases (e.g., approximations, rounding).

### Detailed Flow

#### 1. Input Preparation
- Receive question, choices, and mode ("strict" or "allow_no_answer").
- Initialize 4 LLM instances: Classifier, Question-Driven, Choice-Driven, Second-Think.

#### 2. Mode Classification
- Use `STEM_CLASSIFY_PROMPT` to classify into `"QUESTION_DRIVEN"` or `"ANSWER_VALIDATION"`.
- Output: JSON with `analysis_mode`.

#### 3. Reasoning by Mode

##### Question-Driven Mode (`STEM_PROMPT_QUESTION_DRIVEN`)
- **PHASE_1**: Analyze requirements, explicit/implicit data, and solution strategy.
- **PHASE_2**: Solve step-by-step (`solution_steps` and `final_result` for the final computed result).
- **PHASE_3**: Compare result with choices to determine match (`has_result`), ensuring compatibility with unit differences, alternative representations, approximate values/rounding, or equivalent expressions.
- **PHASE_4**: Select final answer corresponding to one of the choices (`A/B/C/...` or `"X"` if no match).

##### Answer-Validation Mode (Choice-Driven) (`STEM_PROMPT_ANSWER_VALIDATION`)
- **PHASE_1**: Identify question type, evaluation criteria, and list all required knowledge, formulas, laws, or models needed to reason about the problem.
- **PHASE_2**: For **each choice**:
  - Assume the choice is correct.
  - Perform all necessary calculations, reasoning, or simulations based on PHASE_1.
  - Include approximations, unit conversions, or equivalent representations if needed.
  - Write all steps explicitly and output a **final result or logical conclusion** for the choice (without comparing to other choices yet).
- **PHASE_3**: Validate each choice by checking if the result from PHASE_2 satisfies the criteria from PHASE_1.
  - Analyze each choice independently.
  - Evaluate its compatibility with the problem and reasoning.
- **PHASE_4**: Select the choice that best fits the problem.
  - Output the **letter corresponding to the choice**.
  - If no choice is clearly correct, return `"X"`.

#### 4. Fallback / Second-Think
- Can only be activated when set `mode = 'strict'`, meaning the final answer must match one of the given choices. 
- Use `STEM_SECOND_THINK` for assumption-based reasoning if Question-Driven solving fails. This is typically activated when the model's generated result does not match any of the given choices, indicating that the model could not extract hidden knowledge or the problem lacks necessary data, leads to false result. In this phase, each choice is treated as a hypothesis, reasonable assumptions are made, and calculations or reasoning are repeated to select the choice most consistent with the problem and assumptions.
- **PHASE_1**: Re-analyze the requirements, constraints, and relevant knowledge.
- **PHASE_2**: For each choice, assume it is correct, propose reasonable assumptions, and re-solve the problem using calculations or logical reasoning.
- **PHASE_3**: Evaluate the reasonableness and consistency of the assumptions for each choice.
- **PHASE_4**: Select the answer corresponding to the choice with the most reasonable assumptions.


#### 5. Post-Processing
- Parse JSON output, extract `final_answer`.
- Retry on errors (up to `max_retries`).
- Return answer letter or `"X"` if unresolved.

### Prompts Used
- `STEM_CLASSIFY_PROMPT`: Mode selection
- `STEM_PROMPT_QUESTION_DRIVEN`: 4-phase independent solving
- `STEM_PROMPT_ANSWER_VALIDATION`: 4-phase choice-driven solving
- `STEM_SECOND_THINK`: 4-phase fallback with assumption reasoning

### Notes
- This pipeline ensures high accuracy by mimicking structured, human-like expert reasoning.

## Reference_data
We used five external datasets to build the RAG vector search layer:
1. Civic Knowledge: data built from Vietnamese central government resolutions (2022–2025).
2. Ho Chi Minh: data extracted from Wikipedia documents related to Hồ Chí Minh President.
3. Law: data from Hugging Face – VTSNLP/base_vbpl_full (135k legal documents).
4. Medical: data from Hugging Face – VTSNLP/base_yTe (65.2k medical documents).
5. Political Science: lecture materials from the “General Political Theory” course of Thai Nguyen University.

The datasets were not merged into a single structure. Only the text field was extracted from each dataset for processing.
All extracted texts were cleaned and chunked, then transformed into embedding vectors.
Each dataset was indexed independently using Faiss IndexFlatIP, because the overall data volume is very large and this index type provides efficient and scalable vector similarity search.

**Final result:** five separate Faiss IndexFlatIP databases (civic knowledge, Hồ Chí Minh, law, medical, political science) ready for retrieval in the RAG system.

## Prerequisites
- Python 3.10+
- pip (or conda)
- Bash shell
- Recommended: 10GB+ free disk for indexes

## Installation

### Option 1: Using Virtual Environment (venv)
```bash
git clone https://github.com/phongtdd/VNPT_AI_Hackathon.git
cd VNPT_AI_Hackathon
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Using Conda
```bash
git clone https://github.com/phongtdd/VNPT_AI_Hackathon.git
cd VNPT_AI_Hackathon
conda create -n vnpt_ai python=3.10
conda activate vnpt_ai
pip install -r requirements.txt
```

### Option 3: Using Docker
```bash
git clone https://github.com/phongtdd/VNPT_AI_Hackathon.git
cd VNPT_AI_Hackathon
docker build -t team_submission .  
docker run -v /path/to/data:/app/data team_submission 
```

## Docker Hub

Pre-built Docker images are available on Docker Hub for quick deployment without local installation.

### Pull and Run from Docker Hub
```bash
# Pull the latest image
docker pull sagp1012/vnpt_ai:v1

# Run without GPU (CPU only)
docker run --rm -v path/to/file/private_test.json:/code/private_test.json sagp1012/vnpt_ai:v1
```

### Run interactively (if want)
```
docker run -it sagp1012/vnpt_ai:v1
bash scripts/inference.sh
```


## Usage
1) Chunk and build faiss
```
bash scripts/run_preprocess.sh <dataset> [text_field] [split]
```
3) Run inference
```bash
bash scripts/inference.sh <file_test.json>
```
