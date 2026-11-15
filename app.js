// app.js — Логика интерфейса и расстановка игроков

document.addEventListener("DOMContentLoaded", () => {
    const table = document.getElementById("table-area");
    const overlay = document.getElementById("matrix-overlay");
    const grid = document.getElementById("matrix-grid");
    const slot1 = document.getElementById("slot-1");
    const slot2 = document.getElementById("slot-2");

    // 1. РАССТАНОВКА ИГРОКОВ ПО КРУГУ
    const totalSeats = 9;
    const radiusX = 40; 
    const radiusY = 40; 
    let startAngle = -90; 

    for (let i = 1; i < totalSeats; i++) {
        let angle = startAngle + i * (360 / totalSeats);
        let rad = angle * (Math.PI / 180);
        let x = 50 + radiusX * Math.cos(rad);
        let y = 50 + radiusY * Math.sin(rad);

        let seat = document.createElement("div");
        seat.className = "player-seat";
        seat.innerText = "P" + i;
        seat.style.left = x + "%";
        seat.style.top = y + "%";
        table.appendChild(seat);
    }

    // 2. ГЕНЕРАЦИЯ МАТРИЦЫ 13x13
    const ranks = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"];
    
    // Создаем ячейки
    ranks.forEach((rowRank, i) => {
        ranks.forEach((colRank, j) => {
            let cell = document.createElement("div");
            cell.className = "matrix-cell";
            
            // Определяем тип руки (пара, одномастные, разномастные)
            let text = "";
            if (i === j) { text = rowRank + colRank; } // Пары (AA, KK...)
            else if (i < j) { text = rowRank + colRank + "s"; } // Одномастные (AKs)
            else { text = colRank + rowRank + "o"; } // Разномастные (AKo)
            
            cell.innerText = text;
            
            // Обработчик клика по ячейке
            cell.onclick = () => {
                handleCardSelect(text);
                overlay.classList.remove("active");
            };
            
            grid.appendChild(cell);
        });
    });

    // 3. ЛОГИКА ВЫБОРА КАРТ
    let currentSlot = 1; // В какой слот пишем

    // Открытие матрицы при клике на слот
    slot1.onclick = () => { currentSlot = 1; overlay.classList.add("active"); };
    slot2.onclick = () => { currentSlot = 2; overlay.classList.add("active"); };

    function handleCardSelect(hand) {
        // hand может быть "AA", "AKs", "AKo"
        let isPair = !hand.includes("s") && !hand.includes("o");
        let isSuited = hand.includes("s");
        
        let rank1 = hand[0];
        let rank2 = hand[1];

        if (currentSlot === 1) {
            slot1.innerText = rank1 + (isSuited ? "♠" : "♠"); // Пока ставим крести, масть выберем потом
            slot1.classList.add("filled");
            currentSlot = 2; // Автоматически переключаем на второй слот
        } else {
            slot2.innerText = rank2 + (isSuited ? "♠" : "♦");
            slot2.classList.add("filled");
        }
    }

    // 4. ОБРАБОТКА КНОПКИ "БЫСТРЫЙ" (пока просто визуально)
    const modeBtns = document.querySelectorAll(".mode-switch span");
    modeBtns.forEach(btn => {
        btn.onclick = () => {
            modeBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
        };
    });
});
