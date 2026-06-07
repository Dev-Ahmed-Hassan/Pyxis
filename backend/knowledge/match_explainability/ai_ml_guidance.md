# AI ML Guidance

This document supports AI and machine learning career suggestions, match
explanations, project recommendations, and interview preparation.

## Machine Learning Intern Role Signals

chunk_type: career
field: ai_ml
role: Machine Learning Intern
skills: Python, pandas, scikit-learn, model evaluation, data preprocessing
purpose: role-fit

Machine learning internships usually value evidence of data preprocessing,
model training, evaluation metrics, experiment comparison, and clear
explanation of model choices. Strong student evidence can come from notebooks,
Kaggle-style projects, classification or regression projects, model evaluation
reports, and small deployed prediction APIs.

Strong evidence names:

```text
dataset
preprocessing steps
model family
evaluation metric
baseline comparison
limitations
```

## Deep Learning Role Signals

chunk_type: career
field: ai_ml
role: Deep Learning Intern
skills: PyTorch, TensorFlow, neural networks, CNN, NLP, training
purpose: role-fit

Deep learning evidence is stronger when the student has trained or fine-tuned
a neural network and can explain architecture, data shape, loss function,
training loop, validation strategy, overfitting, and model limitations.

Partial evidence includes using an AI API or prompt engineering. API usage
supports AI integration, but it is not the same as training or evaluating a
machine learning model.

## AI Integration Role Signals

chunk_type: career
field: ai_ml
role: AI Application Developer Intern
skills: LLM API, prompt design, RAG, FastAPI, embeddings
purpose: role-fit

AI application developer roles value evidence that the student can integrate
AI services into real applications. Strong evidence includes API integration,
prompt design, structured outputs, retrieval augmented generation, embeddings,
rate-limit handling, and user-facing workflows.

Good project evidence explains:

```text
what model or API was used
what input was sent
how output was validated
how errors or limits were handled
how the AI feature improved the app
```

## ML Project Suggestion Classification

chunk_type: project
field: ai_ml
role: Machine Learning Intern
skills: scikit-learn, pandas, classification, metrics
purpose: missing-skill-project

Use this project when the student lacks model training or evaluation evidence.

Project:

```text
Build a classification project using a public dataset. Clean the data, train a
baseline model, compare at least two algorithms, show confusion matrix,
precision, recall, F1 score, and explain model limitations.
```

Resume bullet:

```text
Built a supervised classification pipeline with pandas and scikit-learn,
including data cleaning, model comparison, confusion matrix analysis, and
precision/recall evaluation.
```

## RAG Project Suggestion

chunk_type: project
field: ai_ml
role: AI Application Developer Intern
skills: RAG, embeddings, vector database, LLM API
purpose: missing-skill-project

Use this project when the student has AI API exposure but lacks retrieval or
grounding evidence.

Project:

```text
Create a small RAG assistant over a set of Markdown or PDF documents. Chunk
the documents, embed chunks, retrieve top matches for a query, and pass only
retrieved context to an LLM.
```

Resume bullet:

```text
Implemented a RAG assistant that chunks documents, stores embeddings in a
vector index, retrieves relevant context, and generates grounded answers with
structured LLM output.
```

## AI ML Interview Guidance

chunk_type: interview
field: ai_ml
role: Machine Learning Intern
skills: model evaluation, data preprocessing, overfitting
purpose: interview-prep

Common AI and ML interview questions:

```text
How did you clean and prepare your dataset?
Why did you choose this model?
How did you evaluate performance?
What is overfitting and how did you reduce it?
What metric matters most for your problem and why?
How is using an LLM API different from training a model?
```

Strong answers should mention dataset quality, train/test split, validation,
metric choice, baselines, error analysis, and limitations.

