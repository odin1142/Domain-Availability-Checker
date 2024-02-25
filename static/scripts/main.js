document.addEventListener('DOMContentLoaded', function() {
    // Attach click event listeners to all stars
    document.querySelectorAll('.favorite-star').forEach(star => {
        star.addEventListener('click', function() {
            const domainName = this.getAttribute('data-domain');
            toggleDomainFavorite(domainName, this);
        });
    });
});

function toggleDomainFavorite(domainName, starElement) {
    fetch('/toggle_favorite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `domainName=${encodeURIComponent(domainName)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Use the `isFavorite` status from the server to determine the star state
            if (data.isFavorite) {
                starElement.textContent = '★'; // Domain is a favorite
                starElement.classList.add('favorited');
            } else {
                starElement.textContent = '☆'; // Domain is not a favorite
                starElement.classList.remove('favorited');
            }
        } else {
            alert(`Failed to update favorite status for ${domainName}.`);
        }
    })
    .catch(error => console.error('Error favoriting domain:', error));
}

$(document).ready( function () {
    $('#domainsTable').DataTable();
});