document.addEventListener('DOMContentLoaded', function () {
    const gameDropdown = document.getElementById('gameDropdown');
    const gameTitle = document.querySelector('h6[data-testid="standard-game-card-title"]');
    const gameImages = [
        document.querySelector('#game0 img'),
        document.querySelector('#game1 img'),
        document.querySelector('#game2 img'),
        document.querySelector('#game3 img')
    ];

    // Assume `gameData` is already defined globally by Streamlit
    // Example: <script>var gameData = {...};</script> will be in the HTML
    // let gameData = window.gameData || [];

    // Populate the dropdown with game names
    gameData.forEach(entry => {
        const option = document.createElement('option');
        option.value = entry.GameName;
        option.textContent = entry.GameName;
        gameDropdown.appendChild(option);
    });

    // Add event listener to update the h6 text and images when a game is selected
    gameDropdown.addEventListener('change', function () {
        const selectedGame = gameDropdown.value;
        if (selectedGame) {
            gameTitle.textContent = `Because You Played ${selectedGame}`;
            const selectedGameData = gameData.find(game => game.GameName === selectedGame);
            if (selectedGameData && selectedGameData.Recommendations) {
                selectedGameData.Recommendations.forEach((url, index) => {
                    if (gameImages[index]) {
                        gameImages[index].src = url;
                    }
                });
            }
        } else {
            gameTitle.textContent = "Because You Played";
            gameImages.forEach(img => img.src = '');
        }
    });
});