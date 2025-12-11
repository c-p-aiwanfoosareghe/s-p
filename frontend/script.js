const downloadBtn = document.getElementById("downloadBtn");
const urlInput = document.getElementById("urlInput");
const loading = document.getElementById("loading");
const result = document.getElementById("result");
const downloadLink = document.getElementById("downloadLink");

downloadBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) {
        alert("Please enter a URL");
        return;
    }

    result.classList.add("hidden");
    loading.classList.remove("hidden");

    try {
        const res = await fetch("/scrape", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url, prefer_proxy: false })
        });

        const data = await res.json();
        loading.classList.add("hidden");

        if (data.ok && data.data.video_url) {
            const fileUrl = data.data.video_url;

            downloadLink.href = fileUrl;
            downloadLink.download = fileUrl.split("/").pop();
            result.classList.remove("hidden");

            // Auto-download for phones
            setTimeout(() => {
                const a = document.createElement("a");
                a.href = fileUrl;
                a.download = "";
                a.click();
            }, 300);

        } else {
            alert("Failed to download this reel.");
        }

    } catch (err) {
        loading.classList.add("hidden");
        alert("Server error: " + err);
    }
});
