const rerender = (() => {
    const messagesDiv = document.getElementById("messages");

    function addMessage(text, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.textContent = text;
        msgDiv.classList.add("message");
        if (sender === "user") {
            msgDiv.classList.add("user-message");
        } else {
            msgDiv.classList.add("bot-message");
        }
        messagesDiv.appendChild(msgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    return { addMessage };
})();
