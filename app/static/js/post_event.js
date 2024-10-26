document.addEventListener('DOMContentLoaded', function() {
    const responsibilitiesContainer = document.getElementById('responsibilities-container');
    const addResponsibilityBtn = document.getElementById('add-responsibility');

    function createResponsibilityEntry() {
        const entry = document.createElement('div');
        entry.className = 'responsibility-entry';
        entry.innerHTML = `
            <input type="text" 
                   name="responsibilities[]" 
                   class="responsibility-input" 
                   placeholder="Ex: Băuturi, Gustări, Decorațiuni" required>
            <input type="text" 
                   name="responsibility_details[]" 
                   class="responsibility-details" 
                   placeholder="Detalii despre responsabilitate">
            <input type="number" 
                name="responsibility_budget[]" 
                class="responsibility-budget" 
                placeholder="Buget (RON)" >
            <button type="button" class="remove-responsibility">×</button>
        `;

        entry.querySelector('.remove-responsibility').addEventListener('click', function() {
            entry.remove();
        });

        return entry;
    }

    addResponsibilityBtn.addEventListener('click', function() {
        responsibilitiesContainer.appendChild(createResponsibilityEntry());
    });

    // Add event listener for initial remove button
    document.querySelectorAll('.remove-responsibility').forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.remove();
        });
    });
});