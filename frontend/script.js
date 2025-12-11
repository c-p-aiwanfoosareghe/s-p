document.getElementById("downloadForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const url = document.getElementById("url").value;
    const status = document.getElementById("status");
    
    status.innerText = "Processing...";
    status.style.color = "yellow";

    try {
        const response = await fetch("https://s-p-1.onrender.com/app/scrape", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            status.innerText = "❌ Error: " + response.statusText;
            status.style.color = "red";
            return;
        }

        const data = await response.json();

        if (data.download_url) {
            status.innerHTML = `<a href="${data.download_url}" download>⬇ Download File</a>`;
            status.style.color = "lightgreen";
        } else {
            status.innerText = "❌ Failed to extract download URL";
            status.style.color = "red";
        }

    } catch (err) {
        status.innerText = "❌ Error: " + err.message;
        status.style.color = "red";
    }
});
