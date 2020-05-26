function copy(target_id, button_id) {
    const copyButton = document.querySelector(button_id);
    copyButton.addEventListener("click", function (event) {
        const originalButtonText = copyButton.innerText;
        const copyTarget = document.querySelector(target_id);

        const dummy = document.createElement("textarea");
        dummy.style.position = "absolute";
        dummy.style.left = "-9999px";
        dummy.style.top = "0";
        dummy.textContent = copyTarget.textContent;
        document.body.appendChild(dummy);

        dummy.select();

        try {
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

        setTimeout(() => {
            swapClass(copyButton, "btn-success", "btn-primary");
            swapClass(copyButton, "btn-warning", "btn-primary");
            copyButton.innerText = originalButtonText;
        }, 5000);

        dummy.remove();
    });
}

function swapClass(element, remove, add) {
    element.className = element.className.replace(remove, add);
}
