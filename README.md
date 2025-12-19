# VNPT AI Hackathon

## Overview
This repository contains the source code and scripts for the VNPT AI Hackathon. It provides a complete pipeline for processing data, building a vector database using FAISS, and running inference.

## Components

### 1. Inference
The inference module allows you to run the model on your data.
- **Script**: `scripts/inference.sh`
- **Function**: Executes the inference pipeline.

### 2. Vector Database Construction
To enable efficient similarity search, we build a vector database using FAISS. This process involves two main steps:

#### a. Data Chunking
- **Script**: `scripts/chunk.sh`
- **Function**: Loads the raw data and splits it into manageable chunks for processing.

#### b. FAISS Database Build
- **Script**: `scripts/faiss.sh`
- **Function**: Takes the chunked data and indexes it into a FAISS vector database.

## Usage

### Prerequisites
Ensure you have the necessary environment set up (e.g., Python, FAISS, required libraries).

### Running Inference
To run the inference script:
```bash
bash scripts/inference.sh
```

### Building the Database
1. **Prepare Data**: Run the chunking script.
   ```bash
   bash scripts/chunk.sh
   ```
2. **Build Index**: Run the FAISS script.
   ```bash
   bash scripts/faiss.sh
   ```

## Data Access
### Processed Data (Private)
Access to the processed data is restricted. Authorized users can access it via the following link:
[Google Drive Folder](https://drive.google.com/drive/folders/1VtLlBzLp7spsSwka101me-HrP6v2xF0z?usp=sharing).