import google.generativeai as gem
from web.keys import GEMINI_API_KEY

gem.configure(api_key=GEMINI_API_KEY)

model = gem.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Explain basic machine learning models"
                                  "at an undergraduate level.", stream=True)

for chunk in response:
    print(chunk.text)