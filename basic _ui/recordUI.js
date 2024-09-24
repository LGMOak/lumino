// It little bit complex, as majority generate by chatGPT 

document.addEventListener("DOMContentLoaded", function() {
    const recordButton = document.getElementById('recordButton'); 
    const recordIcon = document.getElementById('recordIcon');  // ensuring to get the recordIcon element in recordUI.html
    console.log("Page loaded, record button:", recordButton);  

    let SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Speech Recognition API is not supported in this browser.");
        return;
    }

    let recognition = new SpeechRecognition();
    recognition.lang = 'en-US';  // recognise English speaking 
    recognition.continuous = false;  
    recognition.interimResults = false;

    let isRecording = false;

    // monitor the "Record" button, if click, to start record 
    recordButton.addEventListener('click', function() {
        if (!isRecording) {
            recognition.start();
            isRecording = true;
            if (recordIcon) {
                recordIcon.classList.add('recording');  
            }
        } else {
            recognition.stop();
        }
    });

    // Deal with the "Record" event
    recognition.onend = function() {
        if (recordIcon) {
            recordIcon.classList.remove('recording');  
        }
        isRecording = false;
    };

    // Deal with the voice recognition
    recognition.onresult = function(event) {
        let transcript = event.results[0][0].transcript;  // capital voice and transfer to the transcript
        console.log('Recognized text:', transcript);  // check whether imput the transcript 
    
        // check whether is Chinese transcript
        if (isChinese(transcript)) {
            // Currently, if Chinese, put on the right hand side (USER) (Directly put, no translate)
            updateConversation(transcript, null);
        } else {
            // Currently, if not Chinese, translate to Chineses and put on the left hand side (COMPUTER)
            translateText(transcript);
        }
    };
    
    // Deal with if recognition error 
    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);  
        document.getElementById('translationResult').innerText = "Speech recognition error: " + event.error;
    };

    function isChinese(text) {
        const chineseRegex = /[\u4e00-\u9fff]/;  // to Check whether include Chinese character 
        return chineseRegex.test(text);
    }
    
    // Translation function
    function translateText(text) {
        const url = 'http://localhost:3001/translate';  
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'text': text,
                'target_lang': 'ZH',  // translate target language currently only set as Chinese
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.translations && data.translations.length > 0) {
                const translatedText = data.translations[0].text;
                updateConversation(text, translatedText);
            } else {
                throw new Error('No translation found');
            }
        })
        .catch(error => {
            console.error('Error during translation:', error);
            document.getElementById('translationResult').innerText = "Translation error: " + error.message;
        });
    }
    
    // update the conversation and to store in the chat in webUI.html 
    function updateConversation(userText, computerText) {
        
        // get current conversation 
        let conversation = JSON.parse(localStorage.getItem('conversation')) || [];
    
        if (computerText) {
            conversation.push({
                user: userText,
                computer: computerText
            });
        } else {
            conversation.push({
                user: userText
            });
        }
    
        localStorage.setItem('conversation', JSON.stringify(conversation));
    
        window.location.href = 'webUI.html';
    }
});
