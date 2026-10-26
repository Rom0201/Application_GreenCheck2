document.addEventListener("DOMContentLoaded", () => {
  initFlashAlerts();
  initPasswordConfirmation();
  initActiveNavLink();
});

/* ---- 1. Fermeture automatique des messages flash (.alert) ---- */
function initFlashAlerts() {
  const alerts = document.querySelectorAll(".alert");

  alerts.forEach((alert) => {
    // Rendre l'alerte cliquable pour la fermer manuellement
    alert.style.cursor = "pointer";
    alert.title = "Cliquer pour fermer";

    const close = () => {
      alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-10px)";
      setTimeout(() => alert.remove(), 400);
    };

    alert.addEventListener("click", close);

    // Fermeture auto après 5 secondes
    setTimeout(close, 5000);
  });
}

/* ---- 2. Validation du mot de passe (register.html) ---- */
function initPasswordConfirmation() {
  const password = document.getElementById("password");
  const confirmPassword = document.getElementById("confirm_password");
  const form = confirmPassword ? confirmPassword.closest("form") : null;

  if (!password || !confirmPassword || !form) return;

  const showError = (message) => {
    let errorEl = confirmPassword.parentElement.querySelector(".field-error");

    if (!errorEl) {
      errorEl = document.createElement("small");
      errorEl.className = "field-error";
      errorEl.style.color = "var(--color-danger)";
      errorEl.style.display = "block";
      errorEl.style.marginTop = "0.3rem";
      confirmPassword.parentElement.appendChild(errorEl);
    }

    errorEl.textContent = message;
    confirmPassword.style.borderColor = message
      ? "var(--color-danger)"
      : "#cfd8cf";
  };

  const checkMatch = () => {
    if (confirmPassword.value === "") {
      showError("");
      return true;
    }
    if (password.value !== confirmPassword.value) {
      showError("Les mots de passe ne correspondent pas.");
      return false;
    }
    showError("");
    return true;
  };

  password.addEventListener("input", checkMatch);
  confirmPassword.addEventListener("input", checkMatch);

  form.addEventListener("submit", (event) => {
    if (!checkMatch()) {
      event.preventDefault();
      confirmPassword.focus();
    }
  });
}

/* ---- 3. Mise en surbrillance du lien actif dans la navbar ---- */
function initActiveNavLink() {
  const links = document.querySelectorAll(".navbar-links a");
  const currentPath = window.location.pathname;

  links.forEach((link) => {
    const linkPath = new URL(link.href).pathname;

    if (linkPath === currentPath) {
      link.style.textDecoration = "underline";
      link.style.fontWeight = "700";
    }
  });
}
