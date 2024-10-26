function claimResponsibility(taskId, button) {
    fetch("/claim_responsibility", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ responsibility_id: taskId}),
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.message) {  // Success response
            button.textContent = "Preluat";
            button.classList.add("claimed");
            button.disabled = true;
        } else {  // Error response
            alert("Nu poți prelua responsabilitate. Te-ai logat?.");
        }
    })
    .catch((error) => {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
    });
}
