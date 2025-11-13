document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const chatArea = document.getElementById("chatArea");
  const accountBtn = document.getElementById("accountBtn");
  const modal = document.getElementById("accountModal");
  const closeModalBtn = document.getElementById("closeModalBtn");

  // Send message logic
  async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    const userDiv = document.createElement("div");
    userDiv.className = "bg-[#2e2e2e] rounded p-3 text-sm";
    userDiv.textContent = "You: " + message;
    chatArea.appendChild(userDiv);

    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();

    const replyDiv = document.createElement("div");
    replyDiv.className = "bg-[#2e2e2e] rounded p-3 text-sm";
    replyDiv.textContent = "Bot: " + data.reply;
    chatArea.appendChild(replyDiv);

    chatArea.scrollTop = chatArea.scrollHeight;
    input.value = "";
  }

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  // Modal open/close
  accountBtn.addEventListener("click", () => {
    modal.classList.remove("hidden");
  });

  closeModalBtn.addEventListener("click", () => {
    modal.classList.add("hidden");
  });

  // Close modal when clicking outside of it
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.classList.add("hidden");
    }
  });
});
