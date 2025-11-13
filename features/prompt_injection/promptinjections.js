// static/js/promptinjections.js
async function testPrompt() {
  const prompt = document.getElementById("testPrompt").value;
  const protectionLevel = document.querySelector('input[name="protectionLevel"]:checked').value;

  const res = await fetch("/api/score_prompt", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ prompt, protectionLevel })
  });
  const data = await res.json();
  const container = document.getElementById("testResult");
  container.classList.remove("hidden");
  container.innerHTML = `
    <div class="text-white font-medium">Score: ${data.score}</div>
    <div class="text-gray-300 text-sm">Heuristics: ${data.heuristics.join(", ")}</div>
    <div class="mt-2 text-sm text-gray-200">Explanation: ${data.explanation ?? "—"}</div>
  `;

  // Optionally: ask server for explanation from Gemini (separate call)
  // const explainResp = await fetch("/api/explain", { ... })
}
document.getElementById("testPromptBtn").addEventListener("click", testPrompt);
