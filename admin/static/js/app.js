// Admin panel JavaScript functionality

// HTMX event handling
document.addEventListener('DOMContentLoaded', function() {
    // Toggle staff active status
    document.body.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('toggle-active-btn')) {
            const staffId = e.target.dataset.staffId;
            const activeStatus = e.target.dataset.active === 'true';
            
            // Send AJAX request to toggle status
            fetch(`/staff/${staffId}/toggle-active`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ is_active: !activeStatus })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update button state
                    e.target.dataset.active = data.is_active;
                    
                    // Update button text and class
                    if (data.is_active) {
                        e.target.textContent = 'Active';
                        e.target.classList.remove('btn-danger');
                        e.target.classList.add('btn-success');
                    } else {
                        e.target.textContent = 'Inactive';
                        e.target.classList.remove('btn-success');
                        e.target.classList.add('btn-danger');
                    }
                    
                    // Refresh the table
                    const tableRow = e.target.closest('tr');
                    if (tableRow) {
                        if (data.is_active) {
                            tableRow.classList.remove('table-danger');
                        } else {
                            tableRow.classList.add('table-danger');
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to update status');
            });
        }
    });
    
    // Delete confirmation for staff and bookings
    document.body.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('delete-btn')) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
                return false;
            }
            
            const itemId = e.target.dataset.id;
            const itemType = e.target.dataset.type;
            
            // Send DELETE request
            fetch(`/${itemType}/${itemId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Remove the row from the table
                    const tableRow = e.target.closest('tr');
                    if (tableRow) {
                        tableRow.remove();
                    }
                } else {
                    alert('Failed to delete: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to delete item');
            });
            
            e.preventDefault();
        }
    });
    
    // Working day toggle in schedule form
    document.body.addEventListener('change', function(e) {
        if (e.target && e.target.classList.contains('working-day-toggle')) {
            const weekday = e.target.dataset.weekday;
            const timeFields = document.querySelectorAll(`.time-field-${weekday}`);
            
            timeFields.forEach(field => {
                field.disabled = !e.target.checked;
            });
        }
    });
    
    // Initialize working day toggles
    document.querySelectorAll('.working-day-toggle').forEach(toggle => {
        const weekday = toggle.dataset.weekday;
        const timeFields = document.querySelectorAll(`.time-field-${weekday}`);
        
        timeFields.forEach(field => {
            field.disabled = !toggle.checked;
        });
    });
    
    // Date range picker initialization for booking filters
    const dateFromInput = document.getElementById('date-from');
    const dateToInput = document.getElementById('date-to');
    
    if (dateFromInput && dateToInput) {
        dateFromInput.addEventListener('change', function() {
            dateToInput.min = dateFromInput.value;
        });
        
        dateToInput.addEventListener('change', function() {
            dateFromInput.max = dateToInput.value;
        });
    }
});

// Schedule related functions
function applyDefaultSchedule(staffId) {
    if (confirm('This will overwrite the current schedule with default working hours. Continue?')) {
        document.getElementById('apply-default-form').submit();
    }
}

// Apply all weekday settings to a specific weekday
function copyToAll(weekday) {
    const sourceToggle = document.querySelector(`.working-day-toggle[data-weekday="${weekday}"]`);
    const sourceStart = document.querySelector(`.time-field-${weekday}[name="start_time_${weekday}"]`);
    const sourceEnd = document.querySelector(`.time-field-${weekday}[name="end_time_${weekday}"]`);
    
    if (!sourceToggle || !sourceStart || !sourceEnd) return;
    
    const isWorkingDay = sourceToggle.checked;
    const startTime = sourceStart.value;
    const endTime = sourceEnd.value;
    
    for (let i = 0; i < 7; i++) {
        if (i === parseInt(weekday)) continue;
        
        const targetToggle = document.querySelector(`.working-day-toggle[data-weekday="${i}"]`);
        const targetStart = document.querySelector(`.time-field-${i}[name="start_time_${i}"]`);
        const targetEnd = document.querySelector(`.time-field-${i}[name="end_time_${i}"]`);
        
        if (targetToggle && targetStart && targetEnd) {
            targetToggle.checked = isWorkingDay;
            targetStart.value = startTime;
            targetEnd.value = endTime;
            targetStart.disabled = !isWorkingDay;
            targetEnd.disabled = !isWorkingDay;
        }
    }
}
