const scrapeBtn = document.getElementById("scrapeBtn");
const reelUrlInput = document.getElementById("reelUrl");
const resultDiv = document.getElementById("result");

scrapeBtn.addEventListener("click", async () => {
    const url = reelUrlInput.value.trim();
    if (!url) {
        resultDiv.innerHTML = "<span style='color:red;'>Please enter a URL.</span>";
        return;
    }

    resultDiv.innerHTML = "Scraping... Please wait.";

    try {
        const response = await fetch("/scrape", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.ok && data.data.video_url) {
            const fullVideoUrl = window.location.origin + data.data.video_url;

            // Create a clickable link that triggers download
            resultDiv.innerHTML = `
                <p>Scraped successfully!</p>
                <a href="${fullVideoUrl}" download="reel.mp4">Download Video</a>
            `;
        } else {
            resultDiv.innerHTML = `<span style='color:red;'>Failed to scrape video.</span>`;
        }
    } catch (err) {
        resultDiv.innerHTML = `<span style='color:red;'>Error: ${err.message}</span>`;
    }
});
