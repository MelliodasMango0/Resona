// api.js
import { OPENAI_API_KEY } from './openaiConfig.js';

const isMock = false; // Toggle this for demo/dev mode

export async function disambiguateUploadedSong(query, filename) {
  const prompt = `
A user uploaded a file named "${filename}", and from the filename, the tentative song title is "${query}".
Disambiguate what the most official title and artist is — for example, if the title is "My Way" and the filename is "My Way - Limp Bizkit", you should favor Limp Bizkit over Frank Sinatra.
Make sure to return only one match, and ensure it's an official version (not remixes, karaoke, or covers).
Also return the most relevant genre.

Respond in JSON format like this:
{
  "title": "Official Title",
  "artist": "Official Artist",
  "genre": "Genre"
}
`;

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "gpt-3.5-turbo",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.5,
      max_tokens: 200
    })
  });

  const data = await res.json();
  console.log("[OpenAI] Disambiguation response:", data);

  try {
    const json = JSON.parse(data.choices[0].message.content);
    return json;
  } catch (err) {
    console.error("❌ Failed to parse disambiguation result:", data.choices[0].message.content);
    return null;
  }
}


// prompting gpt to return the similar songs
export async function getRecommendations(songTitle, songFileName) {
    if (isMock) {
        return new Promise((res) => setTimeout(() => res(mockRecommendations), 1000));
    }

    const prompt = `
    A user uploaded a song titled "${songTitle}". The full filename was: "${songFileName}".
    Please use this context to disambiguate what version or artist it may be — for example, if it's "My Way" by Limp Bizkit (metal/rock) and not "My Way" by Frank Sinatra (jazz).
    Now, suggest exactly 5 **sonically similar songs** based only on acoustic features such as rhythm, tempo, instrumentation, harmony, energy, or mood.
    Avoid using lyrics, popularity, or genre names alone to guess similarity. If unsure, lean on sound traits. Make sure the recommendations are offictial releases, 
    not remixes or covers and that they are able to be found on apple music.
    Return only the results in valid JSON format like:
    
    [
      {
        "title": "Song Name",
        "artist": "Artist Name",
        "genre": "Genre",
        "matchScore": 92
      }
    ]
    `;
    
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${OPENAI_API_KEY}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            model: "gpt-3.5-turbo",
            messages: [{ role: "user", content: prompt }],
            temperature: 0.7,
            max_tokens: 400
        })
    });

    const data = await res.json();
    console.log("[OpenAI] Response received:", data);
    const content = data.choices[0].message.content;

    try {
        const recommendations = JSON.parse(content);
        return recommendations;
    } catch (err) {
        console.error("Failed to parse OpenAI response:", content);
        throw new Error("OpenAI returned invalid format.");
    }
}