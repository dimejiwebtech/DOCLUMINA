function showApplicationModal(applicationId) {
  const modal = document.getElementById('applicationModal');
  const content = document.getElementById('modalContent');

  // Show loading
  content.innerHTML =
    '<div class="text-center py-8"><i class="fas fa-spinner fa-spin text-2xl text-gray-400"></i></div>';
  modal.classList.remove('hidden');

  // Fetch application details
  fetch(`/dashboard/mentors/detail/${applicationId}/`)
    .then((response) => response.json())
    .then((data) => {
      content.innerHTML = `
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <div class="flex items-center mb-6">
                            ${
                              data.professional_picture
                                ? `<img class="h-16 w-16 rounded-full object-cover mr-4" src="${data.professional_picture}" alt="${data.full_name}">`
                                : `<div class="h-16 w-16 rounded-full bg-gray-300 flex items-center justify-center mr-4"><span class="text-lg font-medium text-gray-700">${data.full_name.charAt(
                                    0
                                  )}</span></div>`
                            }
                            <div>
                                <h4 class="text-xl font-semibold text-gray-900">${
                                  data.full_name
                                }</h4>
                                <p class="text-gray-600">${data.job_title}</p>
                                <div class="flex items-center mt-1">
                                    ${
                                      data.status.approved
                                        ? '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Approved</span>'
                                        : data.status.rejected
                                        ? '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Rejected</span>'
                                        : '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Pending</span>'
                                    }
                                </div>
                            </div>
                        </div>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="text-sm font-medium text-gray-700">Contact Information</label>
                                <div class="mt-1 text-sm text-gray-900">
                                    <p>Email: ${data.email}</p>
                                    <p>Phone: ${data.phone_number}</p>
                                </div>
                            </div>
                            
                            <div>
                                <label class="text-sm font-medium text-gray-700">Professional Details</label>
                                <div class="mt-1 text-sm text-gray-900">
                                    <p>Area of Expertise: ${
                                      data.area_of_expertise
                                    }</p>
                                    <p>Years of Experience: ${
                                      data.years_of_experience
                                    } years</p>
                                    <p>Submitted: ${data.submitted_at}</p>
                                </div>
                            </div>
                            
                            ${
                              data.linkedin_link || data.facebook_link
                                ? `
                            <div>
                                <label class="text-sm font-medium text-gray-700">Social Links</label>
                                <div class="mt-1 space-x-4">
                                    ${
                                      data.linkedin_link
                                        ? `<a href="${data.linkedin_link}" target="_blank" class="text-blue-600 hover:text-blue-800 text-sm">LinkedIn</a>`
                                        : ''
                                    }
                                    ${
                                      data.facebook_link
                                        ? `<a href="${data.facebook_link}" target="_blank" class="text-blue-600 hover:text-blue-800 text-sm">Facebook</a>`
                                        : ''
                                    }
                                </div>
                            </div>
                            `
                                : ''
                            }
                        </div>
                    </div>
                    
                    <div>
                        <div class="mb-6">
                            <label class="text-sm font-medium text-gray-700">Professional Bio</label>
                            <div class="mt-1 p-3 bg-gray-50 rounded-lg text-sm text-gray-900">${
                              data.bio
                            }</div>
                        </div>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="text-sm font-medium text-gray-700 mb-2 block">Documents</label>
                                <div class="space-y-2">
                                    ${
                                      data.cv
                                        ? `<a href="${data.cv}" target="_blank" class="flex items-center p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"><i class="fas fa-file-pdf text-red-500 mr-3"></i><span class="text-sm text-blue-700">Download CV</span></a>`
                                        : '<p class="text-sm text-gray-500">No CV uploaded</p>'
                                    }
                                    ${
                                      data.certificate
                                        ? `<a href="${data.certificate}" target="_blank" class="flex items-center p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"><i class="fas fa-certificate text-green-500 mr-3"></i><span class="text-sm text-green-700">Download Certificate</span></a>`
                                        : '<p class="text-sm text-gray-500">No certificate uploaded</p>'
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
    })
    .catch((error) => {
      content.innerHTML =
        '<div class="text-center py-8 text-red-600"><i class="fas fa-exclamation-triangle text-2xl mb-2"></i><p>Error loading application details</p></div>';
    });
}

function closeApplicationModal() {
  document.getElementById('applicationModal').classList.add('hidden');
}

function showRejectModal(applicationId, applicantName) {
  const modal = document.getElementById('rejectModal');
  const form = document.getElementById('rejectForm');
  const nameSpan = document.getElementById('rejectApplicantName');

  form.action = `/dashboard/mentors/reject/${applicationId}/`;
  nameSpan.textContent = applicantName;
  document.getElementById('rejectReason').value = '';

  modal.classList.remove('hidden');
}

function closeRejectModal() {
  document.getElementById('rejectModal').classList.add('hidden');
}

function showStatusChangeModal(applicationId, applicantName, newStatus) {
  const modal = document.getElementById('statusChangeModal');
  const form = document.getElementById('statusChangeForm');
  const nameSpan = document.getElementById('statusChangeApplicantName');

  form.action = `/dashboard/mentors/change-status/${applicationId}/`;
  nameSpan.textContent = applicantName;
  document.getElementById('statusChangeReason').value = '';

  modal.classList.remove('hidden');
}

function closeStatusChangeModal() {
  document.getElementById('statusChangeModal').classList.add('hidden');
}

// Close modals when clicking outside
document
  .getElementById('applicationModal')
  .addEventListener('click', function (e) {
    if (e.target === this) {
      closeApplicationModal();
    }
  });

document.getElementById('rejectModal').addEventListener('click', function (e) {
  if (e.target === this) {
    closeRejectModal();
  }
});

document
  .getElementById('statusChangeModal')
  .addEventListener('click', function (e) {
    if (e.target === this) {
      closeStatusChangeModal();
    }
  });

// Close modals with Escape key
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    closeApplicationModal();
    closeRejectModal();
    closeStatusChangeModal();
  }
});
