
const code = document.getElementById("code");
const gutter = document.getElementById("gutter");
const button = document.getElementById("analyze");

function updateLines() {
    const count = Math.max(1, code.value.split("\n").length);
    gutter.textContent = Array.from(
        { length: count },
        (_, i) => i + 1
    ).join("\n");
}

code.addEventListener("input", updateLines);
updateLines();

button.addEventListener("click", async () => {
    const results = document.getElementById("results");
    const error = document.getElementById("error");

    results.hidden = true;
    error.textContent = "";

    if (!code.value.trim()) {
        error.textContent = "Please enter Python code first.";
        return;
    }

    button.disabled = true;
    button.textContent = "Analyzing...";

    try {
        const response = await fetch("/api/review", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                code: code.value,
                language: "python",
                problem: document.getElementById("problem").value
            })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(
                data.detail || data.error || "Analysis failed"
            );
        }

        document.getElementById("complexity").textContent =
            data.complexity.estimate;

        document.getElementById("target").textContent =
            data.optimization.target_time;

        document.getElementById("issues").textContent =
            data.summary.security_issues;

        document.getElementById("functions").textContent =
            data.metrics.functions;

        document.getElementById("complexity-notes").textContent =
            data.complexity.notes.join(" ");

        document.getElementById("guidance").textContent =
            data.optimization.guidance;

        document.getElementById("target-detail").textContent =
            data.optimization.target_time + " time / " +
            data.optimization.target_space + " space";

        // Render security findings safely as text.
        const securityList =
            document.getElementById("security-list");

        securityList.replaceChildren();

        if (data.security.length === 0) {
            const message = document.createElement("p");
            message.textContent =
                "No configured security patterns detected. " +
                "This does not guarantee the code is secure.";
            securityList.appendChild(message);
        }

        data.security.forEach((finding) => {
            const item = document.createElement("div");
            item.className = "finding";

            const title = document.createElement("strong");
            title.textContent =
                finding.title + " · Line " + finding.line;

            const severity = document.createElement("span");
            severity.className = "severity";
            severity.textContent = finding.severity;

            const description = document.createElement("p");
            description.textContent = finding.detail;

            item.append(title, severity, description);
            securityList.appendChild(item);
        });

        // Display limitations.
        const limitations =
            document.getElementById("limitations");

        limitations.replaceChildren();

        data.limitations.forEach((text) => {
            const li = document.createElement("li");
            li.textContent = text;
            limitations.appendChild(li);
        });

        document.getElementById("metrics").textContent =
            `Source metrics: ${data.metrics.lines} lines · ` +
            `${data.metrics.characters} characters · ` +
            `${data.metrics.functions} functions`;

        results.hidden = false;
        results.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } catch (err) {
        error.textContent =
            err.message || "Could not connect to the server.";
    } finally {
        button.disabled = false;
        button.textContent = "Analyze Code →";
    }
});