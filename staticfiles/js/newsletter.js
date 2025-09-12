document.addEventListener('DOMContentLoaded', function () {
  const modal = document.getElementById('newsletterModal');

  const closeBtn = document.getElementById('closeModal');
  const form = document.getElementById('newsletterForm');
  const submitBtn = document.getElementById('submitBtn');
  const successMessage = document.getElementById('successMessage');

  let modalShown = false;

  function showModal() {
    if (!modalShown) {
      modalShown = true;
      setTimeout(() => {
        modal.classList.remove('hidden');
        modal.classList.add('animate-fadeIn');
      }, 2000);
    }
  }

  document.addEventListener('click', showModal);
  document.addEventListener('scroll', showModal);
  document.addEventListener('mousemove', showModal);
  document.addEventListener('keydown', showModal);

  function closeModal() {
    modal.classList.add('hidden');
    localStorage.setItem('newsletterLastShown', now.toString());
  }

  closeBtn.addEventListener('click', closeModal);

  modal.addEventListener('click', function (e) {
    if (e.target === modal) {
      closeModal();
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      closeModal();
    }
  });

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="flex items-center justify-center"><span>Joining...</span><span class="ml-2 animate-spin">⏳</span></span>';

    const formData = new FormData(form);

    try {
      const response = await fetch('/newsletter/subscribe/', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        form.style.display = 'none';
        successMessage.classList.remove('hidden');

        setTimeout(() => {
          closeModal();
        }, 3000);
      } else {
        alert(data.message || 'Something went wrong. Please try again.');
        submitBtn.disabled = false;
        submitBtn.innerHTML =
          '<span class="flex items-center justify-center"><span>Get Exclusive Access</span><span class="ml-2">🚀</span></span>';
      }
    } catch (error) {
      alert('Network error. Please check your connection.');
      submitBtn.disabled = false;
      submitBtn.innerHTML =
        '<span class="flex items-center justify-center"><span>Get Exclusive Access</span><span class="ml-2">🚀</span></span>';
    }
  });
});
