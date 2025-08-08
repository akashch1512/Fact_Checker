# app.py
from flask import Flask, render_template, request, jsonify
from API import Gemini_API, Sonet_API

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def handle_form():
    question = ""
    gemini_says = ""
    sonet_says = ""
    error = None

    if request.method == 'POST':
        question = request.form.get('question_input')
        if question:
            try:
                gemini_says = Gemini_API.query_gemini(question)
                sonet_says = Sonet_API.query_perplexity(question)
            except Exception as e:
                error = f"An error occurred: {str(e)}"
        else:
            error = "Please enter a question."

    return render_template('index.html', 
                           question=question, 
                           gemini_says=gemini_says, 
                           sonet_says=sonet_says,
                           error=error)

@app.route('/api/check', methods=['POST'])
def api_check():
    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({'error': 'Please provide a question'}), 400

    try:
        gemini_says = Gemini_API.query_gemini(question)
        sonet_says = Sonet_API.query_perplexity(question)
        return jsonify({'gemini': gemini_says, 'sonet': sonet_says})
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)