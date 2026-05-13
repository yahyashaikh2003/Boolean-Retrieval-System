# Information Retrieval Search Engine 🔎

A robust, custom-built Information Retrieval (IR) system developed in Python. This search engine processes a corpus of text documents, builds mathematical indexes from scratch, and processes complex Boolean and Proximity queries through a user-friendly graphical interface.

## 🚀 Features

* **Custom Preprocessing Pipeline:** Implements tokenization, stop-word removal, and NLTK's Porter Stemmer to normalize text data.
* **Inverted & Positional Indexing:** Builds and serializes highly efficient index structures (`O(1)` lookups) directly to JSON files to prevent redundant computational overhead on startup.
* **Boolean Logic Parsing:** Dynamically evaluates complex Boolean queries (`AND`, `OR`, `NOT`) using set operations across the document corpus.
* **Proximity Search (`/k`):** Utilizes a two-pointer array algorithm to find exact spatial distance matches between terms within the documents.
* **Interactive GUI:** A responsive desktop application built with Tkinter, featuring automatic phrase-query routing and clean result rendering.

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **NLP Processing:** `nltk` (PorterStemmer)
* **GUI Framework:** `tkinter`
* **Data Serialization:** `json`

## 🧠 Under the Hood

Unlike modern Vector Space Models that rely on probabilistic weights, this engine uses strict Boolean retrieval. When a corpus is loaded, the engine maps every unique stem to its document IDs (Inverted Index) and its exact integer positions within those documents (Positional Index). 

Queries are parsed mathematically. For example, a query like `keep out /2` scans the positional index arrays to find instances where the exact mathematical distance between the two terms satisfies the strict proximity constraints.

## 💻 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yahyashaikh2003/Information-Retrieval-Engine.git](https://github.com/yahyashaikh2003/Information-Retrieval-Engine.git)
   cd Information-Retrieval-Engine
