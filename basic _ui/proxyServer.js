const express = require('express');
const axios = require('axios');
const cors = require('cors');  // introduce CORS file
const app = express();
const port = 3001;


// Enable CORS to allow cross-domain requests
app.use(cors());


// Parsing JSON Request Body
app.use(express.json());
app.post('/translate', async (req, res) => {
    const apiKey = 'b19248b1-a916-4fdf-aa07-7922d5be47f4:fx'; 
    const text = req.body.text;
    const targetLang = req.body.target_lang;

    try {
        console.log('Sending request to DeepL API with text:', text);  // add log
        const response = await axios.post('https://api-free.deepl.com/v2/translate', new URLSearchParams({
            'text': text,
            'target_lang': targetLang
        }), {
            headers: {
                'Authorization': `DeepL-Auth-Key ${apiKey}`,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
        console.log('Received response from DeepL API:', response.data);  // add log 

        res.json(response.data);
    } catch (error) {
        console.error('Error during translation:', error.response ? error.response.data : error.message);  // capture wrong information 
        res.status(500).send('Translation failed');
    }
});


// Listen 3001 port 
app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});