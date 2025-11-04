const roleEl = document.getElementById('role');
const messageEl = document.getElementById('message');
const sendBtn = document.getElementById('send');
const chatEl = document.getElementById('chat');

function appendMessage(text, cls='bot-message'){
  const div = document.createElement('div');
  div.className = cls;
  div.innerText = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

async function sendMessage(){
  const role = roleEl.value;
  const message = messageEl.value.trim();
  if(!message) return;
  appendMessage(message, 'user-message');
  messageEl.value = '';
  try{
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ role, message })
    });
    const data = await res.json();
    if(data.answer) appendMessage(data.answer, 'bot-message');
    else appendMessage('Unexpected response from server', 'bot-message');
  } catch(err){
    appendMessage('Could not reach server. Try again later.', 'bot-message');
  }
}

sendBtn.addEventListener('click', sendMessage);
messageEl.addEventListener('keydown', (e)=>{ if(e.key === 'Enter') sendMessage(); });