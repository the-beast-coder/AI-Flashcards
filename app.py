#!/usr/bin/env python3

import openai
import os
from flask import Flask, request, render_template, send_from_directory, redirect, session
from PyPDF2 import PdfReader
import keys

openai.api_key = keys.api_key

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_text_from_pdf(pdf_file):
    text = ''
    with open(pdf_file, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n\n"
    return text

def create_flashcards(notes):

    # System and user prompts
    system_prompt = 'Take in whatever notes are getting inputted in, for each key word or key phrase, write exactly the key phrase first then the "|" delimeter then the definition. Make as many flashcards as possible so that all the contents in the notes are covered. Also no definitions or key words themselves have the "|" delimeter'
    user_prompt = notes

    completion = openai.ChatCompletion.create(
        model = 'gpt-3.5-turbo',
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': notes}
        ],
        temperature = 0
    )

    flashcards_t = completion['choices'][0]['message']['content']
    flashcards = flashcards_t.split("\n")
    with open("flashcards.txt", "w") as f:
        f.write(flashcards_t)
    cards_dict = {}
    for card in flashcards:
        if "|" in card:
            s = card.split("|")
            cards_dict[s[0]] = s[1]

    return cards_dict


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            text = extract_text_from_pdf(file_path)
            flashcards = create_flashcards(text)
            print(flashcards)
            session["flashcards"] = flashcards
            return redirect("/flashcards")

    return render_template('upload.html', text=None)


@app.route('/flashcards')
def display_flashcards():
    flashcards = session.get("flashcards", None)
    return render_template('flashcards.html', flashcards=flashcards)

if __name__ == '__main__':
    app.secret_key = ' secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True)
