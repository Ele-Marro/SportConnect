//searchForm refers to my existing form, searchInput refers to my search box
const searchForm = document.querySelector("#form"); 
//querySelector() finds the first HTML element matching a CSS selector
//#form selects the element with the id="form" (same with #query below)
const searchInput = document.querySelector("#query");

// HOME AND DISCOVER ACTIVITY SEARCH
if (searchForm && searchInput) { //this condition checks that relevant search elements exist before running the activity search code (prevents error pages without that search bar)
    const activityCards = document.querySelectorAll(".activity-card");

    function filterActivities() {
        const searchText = searchInput.value.toLowerCase().trim();

        activityCards.forEach(function (card) {
            const activityText = card.textContent.toLowerCase();

            if (activityText.includes(searchText)) {
                card.style.display = "";
            } else {
                card.style.display = "none";
            }
        });
    }

    searchInput.addEventListener("input", filterActivities);

    searchForm.addEventListener("submit", function (event) {
        event.preventDefault(); //stops the form from reloading the page when you press search
        filterActivities();
    });
}

// MESSAGES CONTACT SEARCH
const contactSearch = document.querySelector("#contact-search");
const contacts = document.querySelectorAll(".contacts .contact");

if (contactSearch) {
    contactSearch.addEventListener("input", function () {
        const searchText = contactSearch.value.toLowerCase().trim();

        contacts.forEach(function (contact) {
            const contactName = contact
                .querySelector(".contact-name")
                .textContent.toLowerCase();

            if (contactName.includes(searchText)) {
                contact.style.display = "";
            } else {
                contact.style.display = "none";
            }
        });
    });
}
