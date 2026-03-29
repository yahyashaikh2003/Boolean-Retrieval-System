import os
import re
from nltk.stem import PorterStemmer
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox

def load_documents(folder_path):
    doc_id_map = {}
    corpus = {}
    
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' was not found.")
        return {}, {}

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            
            # Extract number from filenames
            match = re.search(r'\d+', filename)
            if match:
                doc_id = int(match.group()) # Separate the number and assign it to doc id
            else:
                continue
            
            #Put the entire file content into corpus as string. matched with doc id.
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                doc_id_map[doc_id] = filename
                corpus[doc_id] = text
                
    return doc_id_map, corpus

def load_stopwords(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            return set(text.strip().split())
    except FileNotFoundError:
        print(f"Error: file '{filepath}' not found. Returning empty set.")
        return set()

def preprocess_text(text, stop_words):
    text = text.lower()
    tokens = re.findall(r'\b[a-z0-9]+\b', text) # Separates words and number tokens, also ignore punctuations
    filtered_tokens = [word for word in tokens if word not in stop_words] #this removes stop words
    stemmer = PorterStemmer()
    stemmed_tokens = [stemmer.stem(word) for word in filtered_tokens]# Reduce the words to their root form
    
    return stemmed_tokens

def build_indexes(corpus, stop_words):
    inverted_index = {}
    positional_index = {}
    
    for doc_id, text in corpus.items():
        clean_tokens = preprocess_text(text, stop_words)
        for position, term in enumerate(clean_tokens):
            
            if term not in inverted_index:
                inverted_index[term] = set()
            inverted_index[term].add(doc_id)
            
            if term not in positional_index:
                positional_index[term] = {}
            
            if doc_id not in positional_index[term]:
                positional_index[term][doc_id] = []
                
            positional_index[term][doc_id].append(position)
    return inverted_index, positional_index

#Store on disk for faster loads
def save_indexes(inverted_index, positional_index, inv_file="inverted_index.json", pos_file="positional_index.json"):
    inv_index_serializable = {term: list(doc_ids) for term, doc_ids in inverted_index.items()}#Converting to list because JSON cannot understand python sets
    with open(inv_file, 'w', encoding='utf-8') as f:
        json.dump(inv_index_serializable, f)
        
    with open(pos_file, 'w', encoding='utf-8') as f:
        json.dump(positional_index, f)
        
    print(f"Indexes saved to '{inv_file}' and '{pos_file}'!")

def load_indexes(inv_file="inverted_index.json", pos_file="positional_index.json"):
    try:
        with open(inv_file, 'r', encoding='utf-8') as f:
            inv_index_raw = json.load(f)
            inverted_index = {term: set(doc_ids) for term, doc_ids in inv_index_raw.items()}
            
        with open(pos_file, 'r', encoding='utf-8') as f:
            positional_index = json.load(f)
            
        pos_index_clean = {}
        for term, docs in positional_index.items(): 
            pos_index_clean[term] = {}
            for doc_id, positions in docs.items(): 
                clean_doc_id = int(doc_id) # Convert the string doc id stored in JSON back to int
                pos_index_clean[term][clean_doc_id] = positions #then put every thing in positional index
            
        print("Indexes loaded from disk")
        return inverted_index, pos_index_clean
        
    except FileNotFoundError:
        print("Saved indexes files not found.")
        return None, None

def fetch_posting(term, inverted_index, stop_words):
    clean_terms = preprocess_text(term, stop_words)
    if not clean_terms:
        return set()
    
    stemmed_word = clean_terms[0]#after stemming the input word store it.
    return inverted_index.get(stemmed_word, set())

def process_boolean_query(query, inverted_index, stop_words, total_docs=56):
    ALL_DOCS = set(range(0, total_docs))
    query = query.replace("(", " ( ").replace(")", " ) ")
    tokens = query.split()
    sets_dict = {}
    eval_string = "" #to build the evaluation string eventually
    prev_type = None
    
    for token in tokens:
        upper_token = token.upper()
        
        if upper_token == "AND":
            eval_string += " & "
            prev_type = "OP"
        elif upper_token == "OR":
            eval_string += " | "
            prev_type = "OP"
        elif upper_token == "NOT":
            if prev_type in ["TERM", "PAREN_CLOSE"]: 
                eval_string += " & "
            eval_string += " ALL_DOCS - "
            prev_type = "OP"
            
        elif token == "(":
            if prev_type in ["TERM", "PAREN_CLOSE"]:
                eval_string += " & "
            eval_string += " ( "
            prev_type = "PAREN_OPEN"
        elif token == ")":
            eval_string += " ) "
            prev_type = "PAREN_CLOSE"
            
        else:
            if prev_type in ["TERM", "PAREN_CLOSE"]:
                eval_string += " & "
                
            sets_dict[token] = fetch_posting(token, inverted_index, stop_words)
            eval_string += f" sets_dict['{token}'] "
            prev_type = "TERM"
            
    try:
        result_set = eval(eval_string)
        return result_set
    except Exception as e:
        print(f"Error evaluating query. Details: {e}")
        return set()
    
def process_proximity_query(query, inverted_index, positional_index, stop_words):
    try:
        parts = query.split('/')
        words_part = parts[0].strip().split()
        raw_term1 = words_part[0]
        raw_term2 = words_part[1]
        k = int(parts[1].strip())
    except:
        print("Invalid proximity query format.")
        return set()

    clean1 = preprocess_text(raw_term1, stop_words)
    clean2 = preprocess_text(raw_term2, stop_words)
    if not clean1 or not clean2: #removing stop words from proximity query 
        return set()
        
    term1, term2 = clean1[0], clean2[0]
    docs1 = inverted_index.get(term1, set())
    docs2 = inverted_index.get(term2, set())
    common_docs = docs1 & docs2 #only common document.
    matched_docs = set()

    for doc_id in common_docs:
        positions1 = positional_index[term1][doc_id]
        positions2 = positional_index[term2][doc_id]
        
        i, j = 0, 0
        match_found = False
        
        #below is the same method discussed in class to find proximity matches
        while i < len(positions1) and j < len(positions2):
            pos1 = positions1[i]
            pos2 = positions2[j]
            distance = abs(pos1 - pos2)
            if distance == k+1: #search for words within k distance
                match_found = True
                break
            
            if pos1 < pos2:
                i += 1
            else:
                j += 1
                
        if match_found:
            matched_docs.add(doc_id)
    return matched_docs

def launch_gui(inv_idx, pos_idx, stopwords_set, total_docs):
    root = tk.Tk()
    root.title("Assignment 1")
    root.geometry("700x500")
    root.configure(padx=10, pady=10)

    title_label = tk.Label(root, text="Boolean & Proximity Query retrieval", font=("Times New Roman", 18, "underline"))
    title_label.pack(pady=(10, 10))

    search_frame = tk.Frame(root)
    search_frame.pack(fill=tk.X, pady=20)

    search_entry = tk.Entry(search_frame, font=("Times New Roman", 14))
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    search_entry.insert(0, "Enter Boolean or Proximity Query")

    def clear_placeholder(event):
        if search_entry.get() == "Enter Boolean or Proximity Query":
            search_entry.delete(0, tk.END)#Delete the placeholder text upon click
    search_entry.bind("<FocusIn>", clear_placeholder)

    result_text = scrolledtext.ScrolledText(root, font=("Times New Roman", 13), height=13, wrap=tk.WORD)#Just adding scroll bar in case long results
    result_text.pack(fill=tk.BOTH, expand=True, pady=10)

    def execute_search(event=None):
        query = search_entry.get().strip()
        if not query or query == "Enter Boolean or Proximity Query":
            messagebox.showwarning("Empty Query", "Please enter a search query.")
            return

        result_text.delete(1.0, tk.END) # Clear prev results
        try:
            if "/" in query:
                res = process_proximity_query(query, inv_idx, pos_idx, stopwords_set)
                query_type = "Proximity Query"
                
            elif "AND" not in query.upper() and "OR" not in query.upper() and "NOT" not in query.upper() and len(query.split()) == 2:
                phrase_query = f"{query} /0"
                res = process_proximity_query(phrase_query, inv_idx, pos_idx, stopwords_set)
                query_type = "Phrase Query"
                
            else:
                res = process_boolean_query(query, inv_idx, stopwords_set, total_docs)
                query_type = "Boolean Query"
            
            if res:
                sorted_docs = sorted(list(res))
                result_text.insert(tk.END, f"Query Type: {query_type}\n")
                result_text.insert(tk.END, f"Total Matches: {len(sorted_docs)} documents\n")
                result_text.insert(tk.END, f"Document IDs:\n{sorted_docs}")
            else:
                result_text.insert(tk.END, "No matching documents found.")
                
        except Exception as e:
            result_text.insert(tk.END, f"Error processing query.\nDetails: {e}")

    search_btn = tk.Button(search_frame, text="Search", font=("Times New ROman", 14, "underline"), bg="#528EC7", fg="white", cursor="hand2", command=execute_search)
    search_btn.pack(side=tk.RIGHT)

    root.bind('<Return>', execute_search)
    root.mainloop()
    
if __name__ == "__main__":
    DATASET_FOLDER = "dataset"
    STOPWORDS_FILE = "stopwords.txt"
    TOTAL_DOCS = 56
    
    doc_map, raw_corpus = load_documents(DATASET_FOLDER)
    stopwords_set = load_stopwords(STOPWORDS_FILE)
    
    if raw_corpus and stopwords_set:
        if os.path.exists("inverted_index.json") and os.path.exists("positional_index.json"): #To look for indexes stored on disk
            print("Loading from disk")
            inv_idx, pos_idx = load_indexes()
        else:
            inv_idx, pos_idx = build_indexes(raw_corpus, stopwords_set)
            save_indexes(inv_idx, pos_idx)
            
        launch_gui(inv_idx, pos_idx, stopwords_set, TOTAL_DOCS)
        
        