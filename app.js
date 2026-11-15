// app.js — Математическая расстановка игроков по овалу

document.addEventListener("DOMContentLoaded", () => {
    const table = document.getElementById("table-area");
    if (!table) return;

    // Общее количество мест за столом (включая "Вы")
    const totalSeats = 9;
    
    // Радиусы эллипса в процентах от ширины и высоты стола
    // Ширина: 40% (чтобы не вылезали за края)
    const radiusX = 40;
    // Высота: 40%
    const radiusY = 40;

    // Начинаем с верхнего центра (12 часов) 
    // Угол -90 градусов — это верх
    let startAngle = -90;

    // "Вы" уже есть в HTML, поэтому создаем 8 остальных
    for (let i = 1; i < totalSeats; i++) {
        // Вычисляем угол для каждого игрока
        // 360 градусов делим на 9 мест
        let angle = startAngle + i * (360 / totalSeats);
        
        // Переводим в радианы
        let rad = angle * (Math.PI / 180);

        // Вычисляем координаты (центр стола 50%, 50%)
        let x = 50 + radiusX * Math.cos(rad);
        let y = 50 + radiusY * Math.sin(rad);

        // Создаем элемент игрока
        let seat = document.createElement("div");
        seat.className = "player-seat";
        seat.innerText = "P" + i;
        
        // Позиционируем
        seat.style.left = x + "%";
        seat.style.top = y + "%";

        // Добавляем на стол
        table.appendChild(seat);
    }
});
