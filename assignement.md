# ASSIGNMENT #1: DESIGN, IMPLEMENTATION, AND EVALUATION OF A BIOMEDICAL INFORMATION RETRIEVAL SYSTEM

**Instructor:** Prof. Miguel García-Remesal (mgremesal@fi.upm.es)

The goal of this practical assignment is to develop an Information Retrieval system — specifically, a binary text classifier — to identify scientific articles in the PubMed database that are related to a given set of abstracts within a defined research topic. [cite_start]In this case, the focus is on a collection of 1,308 manuscripts containing information on the polyphenol composition of various foods[cite: 3, 4].

[cite_start]Polyphenols are natural compounds synthesized by plants as a defense mechanism against sunlight, pests, and other environmental stressors[cite: 5]. They are widely distributed in fruits such as grapes, apples, berries, and pomegranates; in vegetables such as spinach, broccoli, and onions; as well as in commonly consumed beverages such as tea, coffee, red wine, and cocoa[cite: 6, 7]. They are also present in olive oil, legumes, and a variety of spices[cite: 8]. Their relevance stems from their strong antioxidant activity, which helps protect cells against oxidative stress[cite: 9]. In addition, polyphenols contribute to cardiovascular health, reduce inflammation, and support the balance of the intestinal microbiota[cite: 10]. A common example is the intense coloration of red wine or blueberries, which is attributed to polyphenols and simultaneously illustrates their potential health benefits[cite: 11].

The information regarding these 1,308 publications is compiled in the Excel document `publications.xlsx` (go to Moodle to download this file), where each row corresponds to a relevant article[cite: 12]. Based on this dataset, students are required to:

---

### 1) Task 1 (Mandatory, 2.5% of the grade)
Retrieve from PubMed the abstracts associated with each publication in `publications.xlsx`[cite: 14]. To accomplish this task, the use of the NCBI E-utilities web services is recommended[cite: 15]. These services, provided by the National Center for Biotechnology Information (NCBI), constitute a suite of programmatic tools that enable automated access to biomedical and genetic databases[cite: 16]. In practical terms, NCBI E-utilities function as a programmable gateway, allowing researchers, developers, and students to connect to resources such as PubMed, GenBank, and GEO, among others, without relying on the manual use of the web interface[cite: 17]. Some key features include[cite: 18]:

* A web-based API, accessible primarily through URLs or programmatic queries[cite: 19].
* The capability to search, retrieve, and process information from millions of articles, DNA sequences, proteins, and molecular structures[cite: 20].
* A set of utilities including, among others[cite: 21]:
    * **ESearch**: to search records within a database.
    * **EFetch**: to download complete data entries.

The official documentation for the NCBI E-utilities API can be found at: [EUtilities Usage Guidelines and API Key - NCBI E-Utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/)[cite: 23].

By combining these utilities with the Python programming language, it is possible to automatically retrieve all abstracts using the following sample code[cite: 24]:

```python
import requests

# Step 1: Search for the PMID of the article by title
esearch_url = "[https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi)"
params = {
    "db": "pubmed",
    "term": "Polyphenol composition and antioxidant activity in strawberry purees impact of achene level and storage [Title]"
}
pmid_response = requests.get(esearch_url, params=params)
print("ESearch result (PMID):")
print(pmid_response.text)

# Once the PMID (17550269) is identified, use EFetch:
efetch_url = "[https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi)"
params = {
    "db": "pubmed",
    "id": "32431335", # Retrieved PMID
    "retmode": "text",
    "rettype": "abstract"
}
abstract_response = requests.get(efetch_url, params=params)
print("\nAbstract:")
print(abstract_response.text)
```

### 2) Task 2 (Mandatory, 2.5% of the grade):
To build the requested retrieval system, 
it is necessary not only to have a set of documents belonging to the class of 
relevant documents, but also a set of documents belonging to the class of non
relevant documents. For this purpose, the student must use the EUtilities tool to 
search for articles whose content is not relevant to this task. The size of this dataset 
must match that of the relevant documents. 

### 3) Task 3 (Mandatory, 20% of the grade):

Conduct a review of the state of the art 
on the topic of this practical assignment. Search for methods, techniques, and 
systems that share the same purpose as the information retrieval system to be 
developed. The approaches must have been published in high-impact journals or 
prestigious international conferences within the last 5 years. Select the system that 
the student considers to be the best option for addressing the proposed problem. 
The choice must be justified through a comparison with other existing systems

### 4) Task 4 (Mandatory, 40% of the grade):
The student must implement the chosen 
retrieval system using the programming language of their choice. The use of 
Python is recommended, as it offers many libraries that will facilitate the 
implementation. The student must provide the system’s source code, along with 
all the necessary dependencies, so that the instructor can reproduce the execution 
and the experiments if deemed necessary. If the information retrieval system is 
based on machine learning techniques, the student must split the existing datasets 
(relevant and non-relevant documents) into three distinct groups (training, 
validation, and testing) to carry out the model training.

### 5) Task 5 (Optional, 20% of the grade):
 Carry out an evaluation of the developed 
information retrieval system using the evaluation metrics studied in the theory 
classes. The evaluation must be conducted against the system of another group in 
the class. Both set-based metrics and ranking-based metrics must be used. A 
discussion and critical assessment of the results is required. The mere presentation 
of results without discussion will not be considered. 

### 6) Task 6 (Mandatory, up to 15% of the grade):
The work completed for this 
assignment must be documented in a report with a minimum length of 10 pages, 
following the structure outlined in this brief. The report must be submitted in PDF 
format. Additionally, students must prepare a presentation for an in-class oral 
defense of the work. The presentation should last no longer than 12 minutes, 
followed by up to 3 minutes for questions. It is mandatory that all group members 
participate equally in the presentation. Each member will be individually assessed 
on the clarity of their explanations and their ability to respond effectively to 
questions from the instructor and their fellow classmates. The report will be 
evaluated as a group, with consideration given to both the depth of content and 
the overall quality of the document. 
