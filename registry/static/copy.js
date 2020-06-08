"use strict";

function copy(target_id, button_id) {
    const copyButton = document.querySelector(button_id);
    copyButton.addEventListener("click", function (event) {
        const originalButtonText = copyButton.innerText;

        // Create a dummy textarea with the same text as the target,
        // because we can only programmatically copy out of textareas.
        const dummy = document.createElement("textarea");
        dummy.style.position = "absolute";
        dummy.style.left = "-9999px";
        dummy.style.top = "0";
        dummy.textContent = document.querySelector(target_id).textContent;
        document.body.appendChild(dummy);

        try {
            // Copy copies the selected text, so select the text in the dummy
            dummy.select();
            const successful = document.execCommand("copy");

            if (successful) {
                swapClass(copyButton, "btn-primary", "btn-success");
                copyButton.innerText = "Copied!";
            } else {
                swapClass(copyButton, "btn-primary", "btn-warning");
                copyButton.innerText = "Error, Try Again!";
            }
        } catch (err) {
            console.log(`Oops, unable to copy: ${err}`);
            swapClass(copyButton, "btn-primary", "btn-warning");
            copyButton.innerText = "Error, Try Again!";
        }

        // After a short timeout, change the button back to its original styling
        setTimeout(() => {
            swapClass(copyButton, "btn-success", "btn-primary");
            swapClass(copyButton, "btn-warning", "btn-primary");
            copyButton.innerText = originalButtonText;
        }, 5000);

        // Remove the dummy element from the DOM
        dummy.remove();
    });
}

function swapClass(element, remove, add) {
    element.className = element.className.replace(remove, add);
}
