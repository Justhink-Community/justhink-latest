const filterButtons = document.querySelectorAll('.filter-button')

filterButtons.forEach(filterButton => {
    filterButton.addEventListener('click', (_e) => {
        if (!filterButton.classList.contains('active')) {
            document.querySelector('.filter-button.active').classList.remove('active')
            filterButton.classList.add('active')
        }
    })
});