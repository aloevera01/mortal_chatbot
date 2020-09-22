from flask import Flask, render_template, request
import random  # for choosing between answers
import nltk  # for part of speech detection, tokenization and wordlist for noise removal
import re  # for regular expressions
from nltk.corpus import stopwords

nltk.download('stopwords')  # a list with stop words for noise removal
nltk.download('averaged_perceptron_tagger')  # for getting a part of speech
nltk.download('brown')  # for getting a part of speech


# search for a key by value
def get_key(d, value):
    for key in d.keys():
        for v in d.get(key):
            if v == value:
                return key


# returns a formulaic answer guided by the user's phrase tag

def formulaic_answer(questions_dict, answers_dict, question):
    tag_answer = get_key(questions_dict, question)
    values = answers_dict.get(tag_answer)
    return values[random.randrange(len(values))]


''' 
 checks if the user's phrase is a template 
 if yes, then returns the answer
 if not, returns None
'''


def formal_response_check(questions_dict, answers_dict, phrase):
    result = None
    pattern_phrase = r'[^a-zA-Z\s]'
    phrase = re.sub(pattern_phrase, '', phrase).lower()
    for tag in list(questions_dict.keys()):
        for word in list(questions_dict.get(tag)):
            if phrase.find(word) >= 0:
                result = formulaic_answer(questions_dict, answers_dict, word)
                return result
    return result


# returns tokenized phrase without noise

def phrase_correction(user_phrase, stop_words_list):
    tokenized_phrase = nltk.word_tokenize(user_phrase)
    result = []
    for w in tokenized_phrase:
        if w not in stop_words_list:
            result.append(w)
    return result


''' creates a dictionary where the key is a part of speech (for which there are answers) and the value is the list with 
words that are that part of speech '''


def morphological_analysis(sentence, answers_tags):
    tagger = nltk.pos_tag(sentence)
    tags = {}
    for word, tag in tagger:
        if tag in answers_tags:
            if tag not in tags:
                tags[tag] = [word]
            else:
                words = tags.get(tag)
                words.append(word)
                tags[tag] = words
    return tags


''' selects a keyword and returns a list in where 
 [0] element is the part of speech of the selected word
 [1] the selected word comes'''


def keyword_selection(tag_word_dict):
    result = []
    tags_keys = list(tag_word_dict.keys())
    chosen_tag = tags_keys[random.randrange(len(tags_keys))]
    word_values = list(tag_word_dict.get(chosen_tag))
    chosen_word = word_values[random.randrange(len(word_values))]
    result.append(chosen_tag)
    result.append(chosen_word)
    return result


''' formulates the answer by inserting the keyword into the sentence for words that refer to the part of speech of the 
 selected word '''


def compose_answer(answers_dict, answer_tag, answer_word):
    answers = []
    for t in answers_dict.keys():
        if t == answer_tag:
            answers = answers_dict.get(t)
            break
    answer = answers[random.randrange(len(answers))]
    if '*' in answer:
        answer = answer.replace('*', answer_word)
    return answer


# adding new symbols in a stop-words list

stop_words = set(stopwords.words('english'))
new_stopwords = [",", ".", "?", ":", ";", '/']
stop_words = stop_words.union(new_stopwords)

# adding info from files to dicts


fileUserFormulaicQuestions = open('userTemplate.txt')
userFormulaicQuestions = dict()

for line in fileUserFormulaicQuestions:
    line = line.rstrip()
    line = line.split('_')
    userFormulaicQuestions[line[0]] = line[1:]

fileUserFormulaicQuestions.close()

fileFormulaicAnswers = open('responses.txt')
formulaicAnswers = dict()

for line in fileFormulaicAnswers:
    line = line.rstrip()
    line = line.split('_')
    formulaicAnswers[line[0]] = line[1:]

fileFormulaicAnswers.close()

fileError_404 = open('error_404.txt')
error_404 = []

for line in fileError_404:
    error_404.append(line)

fileError_404.close()

fileAnswersPartOfSpeech = open('AnswersPartOfSpeech.txt')
answersPartOfSpeech = {}
currentPartOfSpeech = ''
currentPhrases = []
answersTags = []

for line in fileAnswersPartOfSpeech:
    line = line.rstrip()
    if len(line) == 2 or len(line) == 3:
        if currentPartOfSpeech != '':
            answersPartOfSpeech[currentPartOfSpeech] = currentPhrases
        currentPartOfSpeech = line
        currentPhrases = []
        answersTags.append(line)
    else:
        currentPhrases.append(line)

fileAnswersPartOfSpeech.close()

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get")
def get_bot_response():
    user_phrase = ''
    while user_phrase.lower() not in userFormulaicQuestions.get('farewell'):
        absent_answer = True
        user_phrase = request.args.get('msg')
        formal_answer = formal_response_check(userFormulaicQuestions, formulaicAnswers, user_phrase)
        if formal_answer:
            absent_answer = False
            return str(formal_answer)
        if absent_answer:
            filtered_sent = phrase_correction(user_phrase, stop_words)
            tags_words = morphological_analysis(filtered_sent, answersTags)
            if len(list(tags_words.keys())) > 0:
                tag_word = keyword_selection(tags_words)
                absent_answer = False
                return str(compose_answer(answersPartOfSpeech, tag_word[0], tag_word[1]))
        if absent_answer:
            return str(error_404[random.randrange(len(error_404))])


if __name__ == "__main__":
    app.run()
