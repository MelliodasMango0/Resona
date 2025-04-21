from flask import Flask, request, jsonify
import recommend  # Your recommend.py module

app = Flask(__name__)

@app.route('/recommend', methods=['POST'])
def recommend_songs():
    data = request.get_json()
    title = data.get('title')
    artist = data.get('artist')
    filename = data.get('filename')

    # Call your recommendation function
    recommendations = recommend.get_top_matches(title, artist, filename)

    return jsonify(recommendations)

if __name__ == '__main__':
    app.run(debug=True)
