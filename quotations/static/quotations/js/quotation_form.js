/**
 * JavaScript for multi-location quotation form interactions
 * Handles nested formsets: Quotation → Locations → Items
 */

// Item choices for dropdown (should match Django model ITEM_CHOICES)
const ITEM_CHOICES = [
    ['storage_charges', 'Storage Charges (per pallet per month)'],
    ['inbound_handling', 'Inbound Handling (per unit)'],
    ['outbound_handling', 'Outbound Handling (per unit)'],
    ['pick_pack', 'Pick & Pack (per order)'],
    ['packaging_material', 'Packaging Material'],
    ['labelling_services', 'Labelling Services'],
    ['wms_platform', 'WMS Platform Access (monthly per pallet)'],
    ['value_added', 'Value-Added Services'],
];

document.addEventListener('DOMContentLoaded', function () {
    // Client modal functionality
    initializeClientModal();

    // Initialize location and item handling
    initializeLocationHandling();

    // Load existing items if editing
    loadExistingItems();

    // Initial calculations
    recalculateAllLocationTotals();

    // Form validation on submit
    const quotationForm = document.getElementById('quotation-form');
    if (quotationForm) {
        quotationForm.addEventListener('submit', function (e) {
            // Backend now accepts 'at actual' directly - no cleanup needed
            if (!validateQuotationForm()) {
                e.preventDefault();
                showMessage('Please fill in all required fields correctly.', 'error');
            }
        });
    }
});

/**
 * Initialize client modal functionality
 */
function initializeClientModal() {
    const clientModal = document.getElementById('client-modal');
    const addClientBtn = document.getElementById('add-client-btn');
    const clientForm = document.getElementById('client-form');
    const closeButtons = document.querySelectorAll('.modal-close');

    // Open client modal
    if (addClientBtn && clientModal) {
        addClientBtn.addEventListener('click', function (e) {
            e.preventDefault();
            clientModal.style.display = 'block';
        });
    }

    // Close modal
    if (clientModal) {
        closeButtons.forEach(btn => {
            btn.addEventListener('click', function () {
                clientModal.style.display = 'none';
            });
        });

        // Close modal on outside click
        window.addEventListener('click', function (e) {
            if (e.target === clientModal) {
                clientModal.style.display = 'none';
            }
        });
    }

    // Submit client form via AJAX
    if (clientForm) {
        clientForm.addEventListener('submit', function (e) {
            e.preventDefault();

            if (!validateClientForm()) {
                return;
            }

            const formData = new FormData(clientForm);

            fetch('/quotations/clients/create/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Add new client to select dropdown
                        const clientSelect = document.getElementById('id_client');
                        if (clientSelect) {
                            const option = new Option(data.client.name, data.client.id, true, true);
                            clientSelect.add(option);
                        }

                        // Close modal and reset form
                        if (clientModal) {
                            clientModal.style.display = 'none';
                        }
                        clientForm.reset();

                        showMessage('Client added successfully!', 'success');
                    } else {
                        showMessage('Error adding client. Please check form fields.', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('Error adding client.', 'error');
                });
        });
    }

    // Enforce 10-digit limit on contact number field
    const contactNumberFields = document.querySelectorAll('input[name="contact_number"], input[type="tel"]');
    contactNumberFields.forEach(field => {
        field.addEventListener('input', function (e) {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 10) {
                this.value = this.value.slice(0, 10);
            }
        });

        field.addEventListener('paste', function (e) {
            e.preventDefault();
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            const digitsOnly = pastedText.replace(/[^0-9]/g, '').slice(0, 10);
            this.value = digitsOnly;
            this.dispatchEvent(new Event('input', { bubbles: true }));
        });

        field.addEventListener('keypress', function (e) {
            if (e.key && !/[0-9]/.test(e.key)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initialize location handling (add/remove locations, add/remove items)
 */
function initializeLocationHandling() {
    console.log('[DEBUG] initializeLocationHandling called');
    const addLocationBtn = document.getElementById('add-location-btn');

    if (addLocationBtn) {
        addLocationBtn.addEventListener('click', addLocation);
    }

    // Attach event listeners to existing remove location buttons
    attachLocationEventListeners();

    // Auto-populate items for the initial location(s) if they don't have items yet
    const locationGroups = document.querySelectorAll('.location-group');
    console.log('[DEBUG] Found', locationGroups.length, 'location groups');

    locationGroups.forEach((locationGroup, index) => {
        const locationIndex = locationGroup.getAttribute('data-location-index');
        const itemsContainer = locationGroup.querySelector('.items-container');
        const existingItems = Array.from(itemsContainer.querySelectorAll('.item-row')).filter(row => {
            const style = row.getAttribute('style') || '';
            return !style.includes('none'); // Exclude template with display:none
        });

        console.log('[DEBUG] Location', locationIndex, 'has', existingItems.length, 'existing items');

        // Only populate if no items exist yet (create mode)
        if (existingItems.length === 0) {
            console.log('[DEBUG] Auto-populating items for location', locationIndex);
            populateAllItemsForLocation(locationIndex);
        }
    });
}

/**
 * Attach event listeners to location elements
 */
function attachLocationEventListeners() {
    // Remove location buttons
    document.querySelectorAll('.remove-location-btn').forEach(btn => {
        btn.removeEventListener('click', removeLocation);
        btn.addEventListener('click', removeLocation);
    });

    // Add item buttons
    document.querySelectorAll('.add-item-btn').forEach(btn => {
        btn.removeEventListener('click', addItemToLocation);
        btn.addEventListener('click', addItemToLocation);
    });
}

/**
 * Add a new location
 */
function addLocation() {
    const locationsContainer = document.getElementById('locations-container');
    const totalFormsInput = document.querySelector('#id_locations-TOTAL_FORMS');
    const currentLocationCount = parseInt(totalFormsInput.value);

    // Get template from first location or create new
    let templateGroup = locationsContainer.querySelector('.location-group');
    if (!templateGroup) {
        console.error('No location template found');
        return;
    }

    // Clone the template
    const newLocationGroup = templateGroup.cloneNode(true);

    // Update location index
    newLocationGroup.setAttribute('data-location-index', currentLocationCount);

    // Update all field names and IDs
    updateLocationFormPrefix(newLocationGroup, currentLocationCount);

    // Clear all input values
    newLocationGroup.querySelectorAll('input:not([type="hidden"]), select, textarea').forEach(field => {
        if (field.type !== 'checkbox') {
            field.value = '';
        } else {
            field.checked = false;
        }
    });

    // Clear items container (will add items dynamically)
    const itemsContainer = newLocationGroup.querySelector('.items-container');
    itemsContainer.querySelectorAll('.item-row:not([style*="display: none"])').forEach(row => row.remove());

    // Reset totals
    newLocationGroup.querySelector('.location-subtotal').textContent = '₹ 0.00';
    newLocationGroup.querySelector('.location-gst').textContent = '₹ 0.00';
    newLocationGroup.querySelector('.location-grand-total').textContent = '₹ 0.00';

    // Append to container
    locationsContainer.appendChild(newLocationGroup);

    // Update total forms count
    totalFormsInput.value = currentLocationCount + 1;

    // Attach event listeners
    attachLocationEventListeners();

    // AUTO-POPULATE all 8 item types for this new location
    populateAllItemsForLocation(currentLocationCount);
}

/**
 * Auto-populate all 8 item types for a location
 */
function populateAllItemsForLocation(locationIndex) {
    console.log('[POPULATE] Starting for location', locationIndex);

    // Create all 8 item types automatically
    ITEM_CHOICES.forEach(([value, label], index) => {
        console.log('[POPULATE] Processing item', index, ':', label);

        const locationGroup = document.querySelector(`.location-group[data-location-index="${locationIndex}"]`);
        if (!locationGroup) {
            console.error('[POPULATE] Location group not found for index', locationIndex);
            return;
        }

        const itemsContainer = locationGroup.querySelector('.items-container');
        if (!itemsContainer) {
            console.error('[POPULATE] Items container not found');
            return;
        }

        // Find template by checking style.display instead of attribute selector
        const allItemRows = itemsContainer.querySelectorAll('.item-row');
        console.log('[POPULATE] Found', allItemRows.length, 'item rows total');

        const itemTemplate = Array.from(allItemRows).find(row => row.style.display === 'none');

        if (!itemTemplate) {
            console.error('[POPULATE] Item template not found!');
            console.error('[POPULATE] Item rows:', Array.from(allItemRows).map(r => ({
                display: r.style.display,
                styleAttr: r.getAttribute('style')
            })));
            return;
        }

        console.log('[POPULATE] Template found, cloning...');

        // Clone template
        const newItem = itemTemplate.cloneNode(true);
        newItem.style.display = '';
        newItem.setAttribute('data-row-index', index);

        // Enable all inputs (template has them disabled to prevent submission)
        newItem.querySelectorAll('input, select, textarea').forEach(input => {
            input.disabled = false;
        });

        // Update prefixes
        const prefix = `locations-${locationIndex}-items-${index}`;
        updateItemFormPrefix(newItem, prefix);

        // Set the item description
        const itemDescSelect = newItem.querySelector('.item-description');
        if (itemDescSelect) {
            itemDescSelect.innerHTML = '';
            ITEM_CHOICES.forEach(([choiceValue, choiceLabel]) => {
                const option = document.createElement('option');
                option.value = choiceValue;
                option.textContent = choiceLabel;
                if (choiceValue === value) {
                    option.selected = true;
                }
                itemDescSelect.appendChild(option);
            });
        }

        // Set default values - leave empty (backend will convert to "at actual")
        const unitCostInput = newItem.querySelector('.unit-cost');
        const quantityInput = newItem.querySelector('.quantity');
        if (unitCostInput) unitCostInput.value = '';
        if (quantityInput) quantityInput.value = '';

        // Add before template
        itemsContainer.insertBefore(newItem, itemTemplate);
        console.log('[POPULATE] Item', index, 'added to DOM');

        // Attach event listeners
        attachItemEventListeners(newItem, locationIndex);
    });

    console.log('[POPULATE] Finished adding all items');

    // Update management form with count of 8 items
    updateItemManagementForm(locationIndex);

    // Recalculate totals
    calculateLocationTotals(locationIndex);
}

/**
 * Update form prefix for a location group
 */
function updateLocationFormPrefix(locationGroup, newIndex) {
    const formRegex = /locations-\d+-/g;

    // Update all HTML content
    locationGroup.innerHTML = locationGroup.innerHTML.replace(formRegex, `locations-${newIndex}-`);

    // Update data attributes
    locationGroup.setAttribute('data-location-index', newIndex);
    locationGroup.querySelectorAll('[data-location-index]').forEach(el => {
        el.setAttribute('data-location-index', newIndex);
    });
}

/**
 * Remove a location
 */
function removeLocation(e) {
    const locationGroup = e.target.closest('.location-group');
    const totalFormsInput = document.querySelector('#id_locations-TOTAL_FORMS');
    const currentLocationCount = parseInt(totalFormsInput.value);

    // Prevent removing if only one location
    if (currentLocationCount <= 1) {
        showMessage('At least one location is required', 'error');
        return;
    }

    // Mark for deletion if it's an existing location
    const deleteCheckbox = locationGroup.querySelector('input[name$="-DELETE"]');
    if (deleteCheckbox) {
        deleteCheckbox.checked = true;
        locationGroup.style.display = 'none';
    } else {
        // Just remove it if it's a new location
        locationGroup.remove();
        totalFormsInput.value = currentLocationCount - 1;
    }

    recalculateAllLocationTotals();
}

/**
 * Add item to a specific location
 */
function addItemToLocation(e) {
    const locationGroup = e.target.closest('.location-group');
    const locationIndex = locationGroup.getAttribute('data-location-index');
    const itemsContainer = locationGroup.querySelector('.items-container');

    // Get item template
    const itemTemplate = itemsContainer.querySelector('.item-row[style*="display: none"]');
    if (!itemTemplate) {
        console.error('No item template found');
        return;
    }

    // Count existing items (not deleted, not template)
    const existingItems = itemsContainer.querySelectorAll('.item-row:not([style*="display: none"])');
    const itemIndex = existingItems.length;

    // Clone template
    const newItem = itemTemplate.cloneNode(true);
    newItem.style.display = '';
    newItem.setAttribute('data-row-index', itemIndex);

    // Update prefixes
    const prefix = `locations-${locationIndex}-items-${itemIndex}`;
    updateItemFormPrefix(newItem, prefix);

    // Populate item description dropdown
    const itemDescSelect = newItem.querySelector('.item-description');
    if (itemDescSelect) {
        itemDescSelect.innerHTML = '<option value="">---------</option>';
        ITEM_CHOICES.forEach(([value, label]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            itemDescSelect.appendChild(option);
        });
    }

    // Clear values
    newItem.querySelectorAll('input:not([type="hidden"]), select, textarea').forEach(field => {
        if (field.type !== 'checkbox') {
            field.value = '';
        } else {
            field.checked = false;
        }
    });

    // Add before template
    itemsContainer.insertBefore(newItem, itemTemplate);

    // Update management form
    updateItemManagementForm(locationIndex);

    // Attach event listeners
    attachItemEventListeners(newItem, locationIndex);

    // Recalculate totals
    calculateLocationTotals(locationIndex);
}

/**
 * Update item form prefix
 */
function updateItemFormPrefix(itemRow, newPrefix) {
    // Update all name attributes
    itemRow.querySelectorAll('[name]').forEach(field => {
        const name = field.getAttribute('name');
        if (name.includes('__prefix__')) {
            field.setAttribute('name', name.replace('__prefix__', newPrefix));
        }
    });

    // Update all id attributes
    itemRow.querySelectorAll('[id]').forEach(field => {
        const id = field.getAttribute('id');
        if (id.includes('__prefix__')) {
            field.setAttribute('id', id.replace('__prefix__', newPrefix));
        }
    });

    // Update for attributes in labels
    itemRow.querySelectorAll('label[for]').forEach(label => {
        const forAttr = label.getAttribute('for');
        if (forAttr.includes('__prefix__')) {
            label.setAttribute('for', forAttr.replace('__prefix__', newPrefix));
        }
    });
}

/**
 * Update item management form for a location
 */
function updateItemManagementForm(locationIndex) {
    const locationGroup = document.querySelector(`.location-group[data-location-index="${locationIndex}"]`);
    const itemsContainer = locationGroup.querySelector('.items-container');

    // Count visible, enabled items (exclude deleted items and disabled template)
    const visibleItems = Array.from(itemsContainer.querySelectorAll('.item-row')).filter(row => {
        // Exclude hidden template
        if (row.style.display === 'none') return false;

        // Exclude items with disabled inputs (template)
        const firstInput = row.querySelector('input, select');
        if (firstInput && firstInput.disabled) return false;

        // Exclude deleted items
        const deleteCheckbox = row.querySelector('input[name$="-DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) return false;

        return true;
    });

    const totalItems = visibleItems.length;

    console.log('[UPDATE_MGMT] Location', locationIndex, '- Total items:', totalItems);

    // Update TOTAL_FORMS field
    const totalFormsInput = document.getElementById(`id_locations-${locationIndex}-items-TOTAL_FORMS`);
    if (totalFormsInput) {
        totalFormsInput.value = totalItems;
        console.log('[UPDATE_MGMT] Set TOTAL_FORMS to', totalItems);
    }
}

/**
 * Attach event listeners to item inputs
 */
function attachItemEventListeners(itemRow, locationIndex) {
    // Unit cost and quantity inputs
    itemRow.querySelectorAll('.unit-cost, .quantity').forEach(input => {
        input.addEventListener('input', () => {
            validateNumberInput({ target: input });
            calculateLocationTotals(locationIndex);
        });
    });

    // Delete checkbox
    const deleteCheckbox = itemRow.querySelector('input[name$="-DELETE"]');
    if (deleteCheckbox) {
        deleteCheckbox.addEventListener('change', () => {
            calculateLocationTotals(locationIndex);
        });
    }
}

/**
 * Calculate totals for a specific location
 */
function calculateLocationTotals(locationIndex) {
    const locationGroup = document.querySelector(`.location-group[data-location-index="${locationIndex}"]`);
    if (!locationGroup) return;

    const itemsContainer = locationGroup.querySelector('.items-container');
    let subtotal = 0;

    itemsContainer.querySelectorAll('.item-row:not([style*="display: none"])').forEach(row => {
        // Check if row is marked for deletion
        const deleteCheckbox = row.querySelector('input[name$="-DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) {
            row.style.opacity = '0.5';
            return;
        } else {
            row.style.opacity = '1';
        }

        const unitCostInput = row.querySelector('.unit-cost');
        const quantityInput = row.querySelector('.quantity');
        const totalInput = row.querySelector('.item-total');

        if (unitCostInput && quantityInput && totalInput) {
            let unitCostValue = unitCostInput.value.trim();
            let quantityValue = quantityInput.value.trim();

            // Check for 'at actual' values (empty values are treated as 'at actual')
            const isUnitCostAtActual = !unitCostValue || unitCostValue === '0' || unitCostValue === '0.00' || unitCostValue.toLowerCase() === 'at actual';
            const isQuantityAtActual = !quantityValue || quantityValue === '0' || quantityValue === '0.00' || quantityValue.toLowerCase() === 'at actual';

            // If either field is 'at actual', total is N/A
            if (isUnitCostAtActual || isQuantityAtActual) {
                totalInput.value = 'N/A';
                return; // Skip this row in calculations
            }

            const unitCost = parseFloat(unitCostValue) || 0;
            const quantity = parseFloat(quantityValue) || 0;
            const total = unitCost * quantity;

            totalInput.value = total.toFixed(2);
            subtotal += total;
        }
    });

    const gst = subtotal * 0.18;
    const grandTotal = subtotal + gst;

    // Update location-specific displays
    const subtotalDisplay = locationGroup.querySelector('.location-subtotal');
    const gstDisplay = locationGroup.querySelector('.location-gst');
    const grandTotalDisplay = locationGroup.querySelector('.location-grand-total');

    if (subtotalDisplay) subtotalDisplay.textContent = '₹ ' + subtotal.toFixed(2);
    if (gstDisplay) gstDisplay.textContent = '₹ ' + gst.toFixed(2);
    if (grandTotalDisplay) grandTotalDisplay.textContent = '₹ ' + grandTotal.toFixed(2);
}

/**
 * Recalculate totals for all locations
 */
function recalculateAllLocationTotals() {
    document.querySelectorAll('.location-group').forEach((locationGroup, index) => {
        const locationIndex = locationGroup.getAttribute('data-location-index');
        calculateLocationTotals(locationIndex);
    });
}

/**
 * Load existing items when editing a quotation
 * This function populates items from Django context
 */
function loadExistingItems() {
    // Items are already rendered by Django template
    // Just attach event listeners to them
    document.querySelectorAll('.location-group').forEach(locationGroup => {
        const locationIndex = locationGroup.getAttribute('data-location-index');
        locationGroup.querySelectorAll('.item-row:not([style*="display: none"])').forEach(itemRow => {
            attachItemEventListeners(itemRow, locationIndex);
        });
    });
}

/**
 * Validate client form
 */
function validateClientForm() {
    const form = document.getElementById('client-form');
    if (!form) return false;

    const clientName = form.querySelector('[name="client_name"]');
    const companyName = form.querySelector('[name="company_name"]');
    const email = form.querySelector('[name="email"]');
    const contactNumber = form.querySelector('[name="contact_number"]');
    const address = form.querySelector('[name="address"]');

    let isValid = true;

    if (!clientName.value.trim()) {
        showFieldError(clientName, 'Client name is required');
        isValid = false;
    } else {
        clearFieldError(clientName);
    }

    if (!companyName.value.trim()) {
        showFieldError(companyName, 'Company name is required');
        isValid = false;
    } else {
        clearFieldError(companyName);
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.value.trim()) {
        showFieldError(email, 'Email is required');
        isValid = false;
    } else if (!emailRegex.test(email.value)) {
        showFieldError(email, 'Please enter a valid email address');
        isValid = false;
    } else {
        clearFieldError(email);
    }

    const contactClean = contactNumber.value.trim();
    const phoneRegex = /^[0-9]{10}$/;

    if (!contactClean) {
        showFieldError(contactNumber, 'Contact number is required');
        isValid = false;
    } else if (!phoneRegex.test(contactClean)) {
        showFieldError(contactNumber, 'Contact number must be exactly 10 digits');
        isValid = false;
    } else {
        clearFieldError(contactNumber);
    }

    if (!address.value.trim()) {
        showFieldError(address, 'Address is required');
        isValid = false;
    } else {
        clearFieldError(address);
    }

    return isValid;
}

/**
 * Validate quotation form
 */
function validateQuotationForm() {
    const form = document.getElementById('quotation-form');
    if (!form) return true;

    let isValid = true;

    // Validate client selection
    const clientSelect = document.getElementById('id_client');
    if (clientSelect && !clientSelect.value) {
        showFieldError(clientSelect, 'Please select a client');
        isValid = false;
    } else if (clientSelect) {
        clearFieldError(clientSelect);
    }

    // Validate validity period
    const validityPeriod = document.getElementById('id_validity_period');
    if (validityPeriod) {
        const value = parseInt(validityPeriod.value);
        if (!value || value < 1) {
            showFieldError(validityPeriod, 'Validity period must be at least 1 day');
            isValid = false;
        } else {
            clearFieldError(validityPeriod);
        }
    }

    // Validate point of contact
    const pointOfContact = document.getElementById('id_point_of_contact');
    if (pointOfContact && !pointOfContact.value.trim()) {
        showFieldError(pointOfContact, 'Point of contact is required');
        isValid = false;
    } else if (pointOfContact) {
        clearFieldError(pointOfContact);
    }

    // Validate at least one location with one item
    const locations = document.querySelectorAll('.location-group');
    let hasValidLocation = false;

    locations.forEach(locationGroup => {
        const deleteCheckbox = locationGroup.querySelector('input[name$="-DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) return;

        const locationName = locationGroup.querySelector('.location-name');
        if (!locationName || !locationName.value.trim()) {
            showFieldError(locationName, 'Location name is required');
            isValid = false;
        } else {
            clearFieldError(locationName);
            hasValidLocation = true;
        }
    });

    if (!hasValidLocation) {
        showMessage('At least one location is required', 'error');
        isValid = false;
    }

    return isValid;
}

/**
 * Validate number input fields
 */
function validateNumberInput(e) {
    const input = e.target;
    const value = parseFloat(input.value);

    if (input.classList.contains('unit-cost')) {
        if (value < 0) {
            showFieldError(input, 'Must be positive');
        } else {
            clearFieldError(input);
        }
    }

    if (input.classList.contains('quantity')) {
        if (value <= 0) {
            showFieldError(input, 'Must be greater than 0');
        } else {
            clearFieldError(input);
        }
    }
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    clearFieldError(field);

    field.style.borderColor = '#dc3545';

    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '0.85rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;

    field.parentNode.appendChild(errorDiv);
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.style.borderColor = '';

    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Show message to user
 */
function showMessage(message, type) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass}`;
    alertDiv.textContent = message;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.style.animation = 'slideIn 0.3s ease-out';

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}
