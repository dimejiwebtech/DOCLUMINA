// Password strength checker
const passwordInput = document.getElementById(
  '{{ form.password1.id_for_label }}'
);
const strengthIndicator = document.getElementById('password-strength');
const strengthBar = document.getElementById('strength-bar');
const strengthText = document.getElementById('strength-text');

passwordInput.addEventListener('input', checkPasswordStrength);

function checkPasswordStrength() {
  const password = passwordInput.value;
  const strengthDiv = document.getElementById('password-strength');

  if (password.length === 0) {
    strengthDiv.classList.add('hidden');
    return;
  }

  strengthDiv.classList.remove('hidden');

  let score = 0;
  const requirements = {
    length: password.length >= 8,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    number: /\d/.test(password),
  };

  // Update requirement indicators
  Object.keys(requirements).forEach((req) => {
    const element = document.getElementById(`req-${req}`);
    const icon = element.querySelector('i');
    if (requirements[req]) {
      icon.className = 'fas fa-check text-green-500 mr-1';
      score++;
    } else {
      icon.className = 'fas fa-times text-red-500 mr-1';
    }
  });

  // Update strength bar
  const percentage = (score / 4) * 100;
  strengthBar.style.width = percentage + '%';

  if (score <= 1) {
    strengthBar.className =
      'bg-red-500 h-2 rounded-full transition-all duration-300';
    strengthText.textContent = 'Weak';
    strengthText.className = 'text-sm font-medium text-red-600';
  } else if (score <= 2) {
    strengthBar.className =
      'bg-yellow-500 h-2 rounded-full transition-all duration-300';
    strengthText.textContent = 'Fair';
    strengthText.className = 'text-sm font-medium text-yellow-600';
  } else if (score <= 3) {
    strengthBar.className =
      'bg-blue-500 h-2 rounded-full transition-all duration-300';
    strengthText.textContent = 'Good';
    strengthText.className = 'text-sm font-medium text-blue-600';
  } else {
    strengthBar.className =
      'bg-green-500 h-2 rounded-full transition-all duration-300';
    strengthText.textContent = 'Strong';
    strengthText.className = 'text-sm font-medium text-green-600';
  }
}
