
const uploadForm = document.getElementById("upload-form");
const imageInput = document.getElementById("medical-image");
const uploadArea = document.getElementById("upload-area");
const browseButton = document.getElementById("browse-button");

const uploadPlaceholder = document.getElementById("upload-placeholder");
const previewContainer = document.getElementById("preview-container");
const imagePreview = document.getElementById("image-preview");
const fileName = document.getElementById("file-name");
const removeButton = document.getElementById("remove-image");

const errorMessage = document.getElementById("error-message");
const resultSection = document.getElementById("result-section");
const imageType = document.getElementById("image-type");

let selectedImage = null;
let previewUrl = null;

const allowedTypes = [
    "image/jpeg",
    "image/png",
    "image/webp"
];

const maxFileSize = 10 * 1024 * 1024; // 10 MB

browseButton.addEventListener("click", () => {
    imageInput.click();
});

imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];

    if (file) {
        handleImage(file);
    }
});

function handleImage(file) {
    errorMessage.textContent = "";
    resultSection.hidden = true;

    if (!allowedTypes.includes(file.type)) {
        showError("Please select a JPG, PNG, or WEBP image.");
        return;
    }

    if (file.size > maxFileSize) {
        showError("The image must be smaller than 10 MB.");
        return;
    }

    if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
    }

    selectedImage = file;
    previewUrl = URL.createObjectURL(file);

    imagePreview.src = previewUrl;
    fileName.textContent = file.name;

    uploadPlaceholder.hidden = true;
    previewContainer.hidden = false;
}

function showError(message) {
    errorMessage.textContent = message;
}

function clearImage() {
    selectedImage = null;
    imageInput.value = "";

    if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        previewUrl = null;
    }

    imagePreview.removeAttribute("src");
    fileName.textContent = "";

    previewContainer.hidden = true;
    uploadPlaceholder.hidden = false;
    resultSection.hidden = true;
    errorMessage.textContent = "";
}

removeButton.addEventListener("click", clearImage);

// Drag-and-drop image upload
uploadArea.addEventListener("dragover", (event) => {
    event.preventDefault();
    uploadArea.classList.add("dragover");
});

uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("dragover");
});

uploadArea.addEventListener("drop", (event) => {
    event.preventDefault();
    uploadArea.classList.remove("dragover");

    const file = event.dataTransfer.files[0];

    if (file) {
        handleImage(file);
    }
});

// Frontend demonstration only — no AI model is called here.
uploadForm.addEventListener("submit", (event) => {
    event.preventDefault();
    errorMessage.textContent = "";
    resultSection.hidden = true;

    if (!selectedImage) {
        showError("Please upload a medical image first.");
        return;
    }

    if (!imageType.value) {
        showError("Please select a medical image category.");
        imageType.focus();
        return;
    }

    document.getElementById("predicted-class").textContent =
        "Awaiting backend integration";

    document.getElementById("confidence-score").textContent =
        "Not available";

    resultSection.hidden = false;
    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
});



/* Login and Registration interface */
const getStartedButton = document.getElementById("get-started-button");
const authOverlay = document.getElementById("auth-overlay");
const authClose = document.getElementById("auth-close");

const loginTab = document.getElementById("login-tab");
const registerTab = document.getElementById("register-tab");
const authForm = document.getElementById("auth-form");

const authTitle = document.getElementById("auth-title");
const authSubtitle = document.getElementById("auth-subtitle");
const authSubmit = document.getElementById("auth-submit");
const authMessage = document.getElementById("auth-message");

const nameField = document.getElementById("name-field");
const authName = document.getElementById("auth-name");
const authEmail = document.getElementById("auth-email");
const authPassword = document.getElementById("auth-password");

let authMode = "login";

function openAuth() {
    authOverlay.hidden = false;
    document.body.classList.add("auth-open");
    setAuthMode("login");
    authEmail.focus();
}

function closeAuth() {
    authOverlay.hidden = true;
    document.body.classList.remove("auth-open");
    authMessage.textContent = "";
    getStartedButton.focus();
}

function setAuthMode(mode) {
    authMode = mode;
    const isRegister = mode === "register";

    loginTab.classList.toggle("active", !isRegister);
    registerTab.classList.toggle("active", isRegister);

    nameField.hidden = !isRegister;
    authName.required = isRegister;

    authTitle.textContent = isRegister
        ? "Create Your Account"
        : "Welcome Back";

    authSubtitle.textContent = isRegister
        ? "Register to get started with MedVision."
        : "Sign in to access your dashboard.";

    authSubmit.textContent = isRegister
        ? "Create Account"
        : "Login";

    authPassword.autocomplete = isRegister
        ? "new-password"
        : "current-password";

    authMessage.textContent = "";
}

getStartedButton.addEventListener("click", openAuth);
authClose.addEventListener("click", closeAuth);

loginTab.addEventListener("click", () => setAuthMode("login"));
registerTab.addEventListener("click", () => setAuthMode("register"));

authOverlay.addEventListener("click", (event) => {
    if (event.target === authOverlay) {
        closeAuth();
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !authOverlay.hidden) {
        closeAuth();
    }
});

authForm.addEventListener("submit", (event) => {
    event.preventDefault();

    authMessage.textContent = authMode === "register"
        ? "Registration interface ready. Backend authentication is not connected yet."
        : "Login interface ready. Backend authentication is not connected yet.";
});
