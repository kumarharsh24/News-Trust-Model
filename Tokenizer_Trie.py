import re
import nltk
from nltk.corpus import stopwords
# from sklearn.feature_extraction.text import TfidfVectorizer

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self, data):
        self.root = TrieNode()
        self.num_words = 0

        # Insert all stop words into the Trie
        for word in data:
            self.insert(word)

    def insert(self, word):
        self.num_words += 1
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end_of_word = True

    def search(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end_of_word

# Download NLTK stopwords if not already installed
nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

# Define additional filler words (common in chatbot conversations)
filler_words = {
    "um", "uh", "like", "you know", "so", "actually", "basically", "literally",
    "right", "okay", "well", "I mean", "just", "kind of", "sort of", "totally",
    "seriously", "honestly", "obviously", "really", "anyway", "thing", "stuff",
    "maybe", "perhaps", "alright", "yeah", "no", "yes", "hmm", "hey"
}

# Combine stopwords and filler words
remove_words = stop_words.union(filler_words)

def extract_keywords(news_text, to_Trie=False):
    # Remove punctuation and tokenize words
    words = re.findall(r"\b\w+\b", news_text.lower())
    
    # Remove stopwords and fillers
    filtered_words = [word for word in words if word not in remove_words]
    unique_words = list(set(filtered_words))
    
    # Convert list back to cleaned text for TF-IDF processing
    # cleaned_text = " ".join(filtered_words)
    
    # # TF-IDF to rank most relevant words
    # vectorizer = TfidfVectorizer()
    # tfidf_matrix = vectorizer.fit_transform([cleaned_text])
    
    # # Get feature names and corresponding scores
    # feature_names = vectorizer.get_feature_names_out()
    # scores = tfidf_matrix.toarray()[0]
    
    # # Sort words by importance
    # ranked_words = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
    
    if (to_Trie):
        return Trie(unique_words)
    else:
        return unique_words

def compare_data(Trie_obj, text):
    word_list = extract_keywords(text)
    n = 0

    for word in word_list:
        if Trie_obj.search(word):
            n += 1

    return n/Trie_obj.num_words
