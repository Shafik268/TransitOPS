document.addEventListener('DOMContentLoaded', function() {
    const dispatchForm = document.getElementById('live-dispatch-form');
    const vehicleSelect = document.getElementById('dispatch-vehicle-select');
    const weightInput = document.getElementById('dispatch-weight-input');
    const alertBox = document.getElementById('dispatch-alert');

    if (dispatchForm) {
        dispatchForm.addEventListener('submit', function(event) {
            // Reset validation visibility state
            alertBox.classList.add('hidden');
            alertBox.innerHTML = '';

            const selectedOption = vehicleSelect.options[vehicleSelect.selectedIndex];
            const maxCapacity = parseFloat(selectedOption.getAttribute('data-capacity')) || 0;
            const enteredWeight = parseFloat(weightInput.value) || 0;

            // Enforce explicit physical weight limit parameters matching system criteria
            if (enteredWeight > maxCapacity) {
                event.preventDefault(); // Intercept browser submission pipeline
                
                alertBox.innerHTML = `<strong>🚨 Structural Constraint Invalidation:</strong> Configured payload mass (${enteredWeight} KG) directly breaks vehicle engineering limit parameters (${maxCapacity} KG)!`;
                alertBox.classList.remove('hidden'); // Triggers CSS display evaluation update
                
                // Trigger smooth scroll animation focus onto alert element
                alertBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }
});