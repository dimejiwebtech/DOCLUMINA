// Modal functionality
const modal = document.getElementById('testimonial-modal');
const deleteModal = document.getElementById('delete-modal');
const form = document.getElementById('testimonial-form');
const modalTitle = document.getElementById('modal-title');
let currentTestimonialId = null;
let deleteTestimonialId = null;

// Open modal for adding
document
  .getElementById('add-testimonial-btn')
  ?.addEventListener('click', () => openModal());
document
  .getElementById('add-first-testimonial-btn')
  ?.addEventListener('click', () => openModal());

// Close modal events
document.getElementById('close-modal').addEventListener('click', closeModal);
document.getElementById('cancel-btn').addEventListener('click', closeModal);
document
  .getElementById('cancel-delete')
  .addEventListener('click', () => deleteModal.classList.add('hidden'));

// Modal backdrop clicks
modal.addEventListener('click', (e) => {
  if (e.target === modal) closeModal();
});
deleteModal.addEventListener('click', (e) => {
  if (e.target === deleteModal) deleteModal.classList.add('hidden');
});

function openModal(testimonialId = null) {
  currentTestimonialId = testimonialId;

  if (testimonialId) {
    modalTitle.textContent = 'Edit Testimonial';
    document.getElementById('submit-btn').textContent = 'Update Testimonial';
    loadTestimonialData(testimonialId);
  } else {
    modalTitle.textContent = 'Add Testimonial';
    document.getElementById('submit-btn').textContent = 'Save Testimonial';
    form.reset();
    document.getElementById('testimonial-id').value = '';
  }

  modal.classList.remove('hidden');
  document.getElementById('name').focus();
}

function closeModal() {
  modal.classList.add('hidden');
  form.reset();
  currentTestimonialId = null;
}

function loadTestimonialData(id) {
  fetch(`/dashboard/testimonials/${id}/edit/`)
    .then((response) => response.json())
    .then((data) => {
      document.getElementById('testimonial-id').value = data.id;
      document.getElementById('name').value = data.name;
      document.getElementById('current_job').value = data.current_job;
      document.getElementById('testimony').value = data.testimony;
    })
    .catch((error) => {
      console.error('Error loading testimonial:', error);
      alert('Error loading testimonial data');
    });
}

// Form submission
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const formData = new FormData(form);
  const data = {
    name: formData.get('name').trim(),
    current_job: formData.get('current_job').trim(),
    testimony: formData.get('testimony').trim(),
  };

  // Validation
  if (!data.name || !data.current_job || !data.testimony) {
    alert('Please fill in all required fields');
    return;
  }

  const submitBtn = document.getElementById('submit-btn');
  const originalText = submitBtn.textContent;
  submitBtn.textContent = 'Saving...';
  submitBtn.disabled = true;

  try {
    const url = currentTestimonialId
      ? `/dashboard/testimonials/${currentTestimonialId}/edit/`
      : '/dashboard/testimonials/add/';

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (result.success) {
      closeModal();
      location.reload(); // Reload to show changes
    } else {
      alert(result.error || 'Error saving testimonial');
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error saving testimonial');
  } finally {
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
  }
});

function editTestimonial(id) {
  openModal(id);
}

function deleteTestimonial(id) {
  deleteTestimonialId = id;
  deleteModal.classList.remove('hidden');
}

document
  .getElementById('confirm-delete')
  .addEventListener('click', async () => {
    if (!deleteTestimonialId) return;

    try {
      const response = await fetch(
        `/dashboard/testimonials/${deleteTestimonialId}/delete/`,
        {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
          },
        }
      );

      const result = await response.json();

      if (result.success) {
        deleteModal.classList.add('hidden');
        location.reload();
      } else {
        alert('Error deleting testimonial');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error deleting testimonial');
    }

    deleteTestimonialId = null;
  });

// CSRF token helper
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
