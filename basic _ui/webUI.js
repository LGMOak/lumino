// Change the button color if the button is active 
document.getElementById('scenario').addEventListener('click', function() {
    var dropdownMenu = document.getElementById('select_menu');
    var button = this;

    dropdownMenu.classList.toggle('show');

    button.classList.toggle('active');
});


// Click senario, and it will have the drop down menu 
window.onclick = function(event) {
    if (!event.target.matches('#scenario')) {
        var dropdownMenu = document.getElementById('select_menu');
        var button = document.getElementById('scenario');

        if (dropdownMenu.classList.contains('show')) {
            dropdownMenu.classList.remove('show');
            button.classList.remove('active'); 
        }
    }
};


// If click one of the option, the option relevant name will directly display on the button 
document.addEventListener("DOMContentLoaded", function() {
    const scenarioButton = document.getElementById('scenario');
    const options = document.querySelectorAll('#select_menu a');

    options.forEach(option => {
        option.addEventListener('click', function(event) {
            event.preventDefault();
            const selectedText = option.getAttribute('data-value');
            scenarioButton.textContent = selectedText;
        });
    });
});


// Click the start, jump to the recordUI.html
document.getElementById('start').addEventListener('click', function() {
    window.location.href = 'recordUI.html'; 
});


// Logic for displaying conversation history
document.addEventListener("DOMContentLoaded", function() {

    // Get conversation history from localStorage 
    const conversation = JSON.parse(localStorage.getItem('conversation')) || [];
    
    // Get .chat container from webUI.html
    const chatContainer = document.querySelector('.chat');
    
    // clear .chat container, avoid duplicate 
    chatContainer.innerHTML = '';

    // loop through the conversation, and put in the chat container
    conversation.forEach(entry => {
        if (entry.computer) {

            // Only add computer conversation (The Chinese results, not English results)
            // As currently this translator only speak English, and translate to Chinese, but not achieve otherside
            // Currently, is someone speak English, the solution will directly translate and display on the left hand side of the chat box, which is Computer side (Left hand side)
            const computerMessageDiv = document.createElement('div');
            computerMessageDiv.classList.add('message', 'computer');
            computerMessageDiv.innerHTML = `<div class="message-content">${entry.computer}</div>`;
            chatContainer.appendChild(computerMessageDiv);

        } else {

            // Currently, if users speak Chinese, the solution will directly display in the chat as USER (Right hand side)
            const userMessageDiv = document.createElement('div');
            userMessageDiv.classList.add('message', 'user');
            userMessageDiv.innerHTML = `<div class="message-content">${entry.user}</div>`;
            chatContainer.appendChild(userMessageDiv);
        }
    });
});


// Clear the conversation history
document.getElementById('clearConversation').addEventListener('click', function() {
    // Clear local storage history 
    localStorage.removeItem('conversation');

    // Clear the chat container content
    const chatContainer = document.querySelector('.chat');
    chatContainer.innerHTML = '';
});