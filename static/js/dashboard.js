// Dashboard specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard components
    initializeCharts();
    initializeReadingTracker();
    initializeQuickActions();
    initializeNotifications();

    // Auto-refresh dashboard data every 5 minutes
    setInterval(refreshDashboardData, 300000);
});

// Initialize charts using Chart.js (if available)
function initializeCharts() {
    // Check if Chart.js is loaded
    if (typeof Chart !== 'undefined') {
        // Book status chart
        var bookStatusCtx = document.getElementById('bookStatusChart');
        if (bookStatusCtx) {
            new Chart(bookStatusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Available', 'Issued', 'Overdue', 'Lost', 'Damaged'],
                    datasets: [{
                        data: [35, 25, 15, 5, 5], // Replace with actual data
                        backgroundColor: [
                            '#28a745',
                            '#007bff',
                            '#dc3545',
                            '#6c757d',
                            '#ffc107'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            });
        }

        // Reading activity chart
        var readingActivityCtx = document.getElementById('readingActivityChart');
        if (readingActivityCtx) {
            new Chart(readingActivityCtx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Pages Read',
                        data: [12, 19, 3, 5, 2, 3, 9], // Replace with actual data
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Monthly transactions chart
        var transactionsCtx = document.getElementById('transactionsChart');
        if (transactionsCtx) {
            new Chart(transactionsCtx, {
                type: 'bar',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Issues',
                        data: [65, 59, 80, 81, 56, 55], // Replace with actual data
                        backgroundColor: '#28a745'
                    }, {
                        label: 'Returns',
                        data: [28, 48, 40, 19, 86, 27], // Replace with actual data
                        backgroundColor: '#007bff'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
}

// Initialize reading tracker functionality
function initializeReadingTracker() {
    // Reading log form handling
    var readingLogForm = document.getElementById('reading-log-form');
    if (readingLogForm) {
        readingLogForm.addEventListener('submit', function(e) {
            e.preventDefault();

            var formData = new FormData(this);
            var data = {
                read_today: formData.get('read_today') === 'on',
                pages_read: parseInt(formData.get('pages_read')) || 0,
                minutes_read: parseInt(formData.get('minutes_read')) || 0,
                notes: formData.get('notes') || ''
            };

            ajaxRequest(
                this.action,
                'POST',
                data,
                function(response) {
                    showToast('Reading log updated successfully!', 'success');
                    updateReadingStreak(response.streak_days);
                    refreshReadingCalendar();
                },
                function(status, error) {
                    showToast('Error updating reading log', 'error');
                }
            );
        });
    }

    // Progress update form
    var progressForm = document.getElementById('progress-form');
    if (progressForm) {
        progressForm.addEventListener('submit', function(e) {
            e.preventDefault();

            var progress = parseInt(this.querySelector('[name="progress"]').value);
            ajaxRequest(
                this.action,
                'POST',
                { progress: progress },
                function(response) {
                    showToast('Progress updated!', 'success');
                    updateProgressBar(progress);
                },
                function(status, error) {
                    showToast('Error updating progress', 'error');
                }
            );
        });
    }
}

// Update reading streak display
function updateReadingStreak(streakDays) {
    var streakElement = document.getElementById('reading-streak');
    if (streakElement) {
        streakElement.textContent = streakDays;
        // Add animation
        streakElement.classList.add('animate-pulse');
        setTimeout(function() {
            streakElement.classList.remove('animate-pulse');
        }, 1000);
    }
}

// Update progress bar
function updateProgressBar(progress) {
    var progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = progress + '%';
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = progress + '%';
    }
}

// Refresh reading calendar
function refreshReadingCalendar() {
    var calendarElement = document.getElementById('reading-calendar');
    if (calendarElement) {
        ajaxRequest(
            '/reading/calendar-data/',
            'GET',
            null,
            function(data) {
                updateCalendarDisplay(data);
            }
        );
    }
}

// Update calendar display
function updateCalendarDisplay(data) {
    // Implementation for updating calendar with reading data
    // This would update the visual calendar with reading days
}

// Initialize quick actions
function initializeQuickActions() {
    // Issue book modal
    var issueBookBtn = document.getElementById('issue-book-btn');
    if (issueBookBtn) {
        issueBookBtn.addEventListener('click', function() {
            var modal = new bootstrap.Modal(document.getElementById('issueBookModal'));
            modal.show();
        });
    }

    // Return book actions
    var returnButtons = document.querySelectorAll('.return-book-btn');
    returnButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var transactionId = this.getAttribute('data-transaction-id');
            if (confirm('Are you sure you want to mark this book as returned?')) {
                ajaxRequest(
                    '/transactions/return/' + transactionId + '/',
                    'POST',
                    null,
                    function(response) {
                        showToast('Book returned successfully!', 'success');
                        location.reload();
                    },
                    function(status, error) {
                        showToast('Error returning book', 'error');
                    }
                );
            }
        });
    });

    // Renew book actions
    var renewButtons = document.querySelectorAll('.renew-book-btn');
    renewButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var transactionId = this.getAttribute('data-transaction-id');
            ajaxRequest(
                '/transactions/renew/' + transactionId + '/',
                'POST',
                null,
                function(response) {
                    showToast('Book renewed successfully!', 'success');
                    location.reload();
                },
                function(status, error) {
                    showToast('Error renewing book', 'error');
                }
            );
        });
    });
}

// Initialize notifications
function initializeNotifications() {
    // Mark notifications as read
    var notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(function(item) {
        item.addEventListener('click', function() {
            var notificationId = this.getAttribute('data-notification-id');
            if (notificationId && !this.classList.contains('read')) {
                ajaxRequest(
                    '/notifications/mark-read/' + notificationId + '/',
                    'POST',
                    null,
                    function(response) {
                        this.classList.add('read');
                    }.bind(this)
                );
            }
        });
    });

    // Notification dropdown
    var notificationDropdown = document.getElementById('notification-dropdown');
    if (notificationDropdown) {
        notificationDropdown.addEventListener('shown.bs.dropdown', function() {
            // Mark all as read when dropdown is opened
            ajaxRequest(
                '/notifications/mark-all-read/',
                'POST',
                null,
                function(response) {
                    var badge = document.querySelector('.notification-badge');
                    if (badge) {
                        badge.style.display = 'none';
                    }
                }
            );
        });
    }
}

// Refresh dashboard data
function refreshDashboardData() {
    ajaxRequest(
        '/dashboard/data/',
        'GET',
        null,
        function(data) {
            updateDashboardStats(data);
        }
    );
}

// Update dashboard statistics
function updateDashboardStats(data) {
    // Update stat numbers
    Object.keys(data).forEach(function(key) {
        var element = document.getElementById(key + '-stat');
        if (element) {
            element.textContent = data[key];
        }
    });
}

// Reading calendar navigation
function changeCalendarMonth(direction) {
    var currentMonth = document.getElementById('current-month');
    if (currentMonth) {
        var currentDate = new Date(currentMonth.getAttribute('data-date'));
        currentDate.setMonth(currentDate.getMonth() + direction);

        ajaxRequest(
            '/reading/calendar/' + currentDate.getFullYear() + '/' + (currentDate.getMonth() + 1) + '/',
            'GET',
            null,
            function(data) {
                updateCalendarDisplay(data);
                currentMonth.textContent = currentDate.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
                currentMonth.setAttribute('data-date', currentDate.toISOString().split('T')[0]);
            }
        );
    }
}

// Book request functionality
function submitBookRequest(type) {
    var formData = new FormData(document.getElementById('book-request-form'));
    var data = {
        request_type: type,
        title: formData.get('title') || '',
        author: formData.get('author') || '',
        reason: formData.get('reason') || ''
    };

    ajaxRequest(
        '/requests/submit/',
        'POST',
        data,
        function(response) {
            showToast('Book request submitted successfully!', 'success');
            document.getElementById('book-request-form').reset();
            var modal = bootstrap.Modal.getInstance(document.getElementById('bookRequestModal'));
            modal.hide();
        },
        function(status, error) {
            showToast('Error submitting request', 'error');
        }
    );
}

// Utility functions for dashboard
function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateTimeString) {
    var date = new Date(dateTimeString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function calculateDaysDifference(dateString) {
    var date = new Date(dateString);
    var today = new Date();
    var diffTime = date - today;
    var diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
}

// Export dashboard data
function exportDashboardData(format) {
    var url = '/dashboard/export/?format=' + format;
    window.open(url, '_blank');
}

// Print dashboard
function printDashboard() {
    window.print();
}

// Bulk operations for admin dashboard
function sendBulkReminders() {
    if (confirm('Send overdue reminders to all users with overdue books? This action cannot be undone.')) {
        var button = event.target;
        var originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
        button.disabled = true;

        ajaxRequest(
            '/notifications/send_overdue/',
            'POST',
            null,
            function(response) {
                showToast('Overdue reminders sent successfully! Sent to ' + response.sent + ' users.', 'success');
                button.innerHTML = originalText;
                button.disabled = false;
                // Update reminder count badge
                var badge = document.getElementById('reminder-count');
                if (badge) {
                    badge.textContent = '0';
                }
            },
            function(status, error) {
                showToast('Error sending reminders: ' + error, 'error');
                button.innerHTML = originalText;
                button.disabled = false;
            }
        );
    }
}

function bulkMarkAvailable() {
    if (confirm('Mark all books that are currently issued but should be available? This will update book statuses.')) {
        var button = event.target;
        var originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Updating...';
        button.disabled = true;

        ajaxRequest(
            '/core/bulk_mark_available/',
            'POST',
            null,
            function(response) {
                showToast('Books updated successfully! ' + response.updated + ' books marked as available.', 'success');
                button.innerHTML = originalText;
                button.disabled = false;
                // Refresh dashboard data
                setTimeout(function() {
                    location.reload();
                }, 1000);
            },
            function(status, error) {
                showToast('Error updating books: ' + error, 'error');
                button.innerHTML = originalText;
                button.disabled = false;
            }
        );
    }
}

function generateBulkQRCodes() {
    const useForce = confirm('Do you want to regenerate ALL QR codes? (Click Cancel to only generate missing ones). \n\nNote: If you are on Render, you should click OK to fix broken images.');
    
    var button = event.target;
    var originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generating...';
    button.disabled = true;

    ajaxRequest(
        '/core/bulk_generate_qr/',
        'POST',
        'force=' + useForce,
        function(response) {
            showToast('QR codes processed successfully! Created ' + response.generated + ' QR codes.', 'success');
            button.innerHTML = originalText;
            button.disabled = false;
            // Reload after a short delay to see new images
            setTimeout(function() {
                location.reload();
            }, 2000);
        },
        function(status, error) {
            showToast('Error generating QR codes: ' + error, 'error');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    );
}

// Toast notification function
function showToast(message, type) {
    // Create toast container if it doesn't exist
    var toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    var toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-' + (type === 'success' ? 'success' : 'danger') + ' border-0';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Initialize and show toast
    var bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Utility function for AJAX requests
function ajaxRequest(url, method, data, successCallback, errorCallback) {
    var xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    
    // Get CSRF token
    var csrfToken = getCsrfToken();
    if (csrfToken) {
        xhr.setRequestHeader('X-CSRFToken', csrfToken);
    }
    
    if (data) {
        if (typeof data === 'object') {
            xhr.setRequestHeader('Content-Type', 'application/json');
            data = JSON.stringify(data);
        } else if (typeof data === 'string') {
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        }
    }

    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            var response = xhr.responseText;
            try {
                response = JSON.parse(response);
            } catch (e) {}
            if (successCallback) successCallback(response);
        } else {
            if (errorCallback) errorCallback(xhr.status, xhr.statusText);
        }
    };

    xhr.onerror = function() {
        if (errorCallback) errorCallback(xhr.status, 'Network error');
    };

    xhr.send(data);
}

// Helper to get CSRF token from cookies
function getCsrfToken() {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    // Fallback to searching for a hidden input if cookie is not available
    if (!cookieValue) {
        var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            cookieValue = csrfInput.value;
        }
    }
    return cookieValue;
}
