// app.js — Математическая расстановка игроков по овалу

document.addEventListener("DOMContentLoaded", () => {
    const table = document.getElementById("table-area");
    
    // Количество игроков, которых нужно расставить (всего 9, но "Вы" уже есть в HTML)
    const playersToSpawn = 8; 
    
    // Координаты центра стола
    // Мы используем 50% ширины и 50% высоты
    const centerX = 50; 
    const centerY = 50;

    // Радиусы эллипса (в процентах от размера стола)
    // Ширина (X) чуть меньше 50%, чтобы кружки не вылезали за края
    const radiusX = 40; 
    // Высота (Y) чуть меньше 50%
    const radiusY = 40; 

    // Начинаем с верхнего центра (12 часов) и идем по часовой стрелке
    // Угол в градусах для первого игрока (P1)
    let startAngle = -90; 

    // Шаг угла: 360 градусов делим на общее количество мест (9)
    // Но так как "Вы" занимаете нижнее место (-90 + 180 = 90 градусов),
    // мы просто расставляем остальных 8 игроков.
    
    for (let i = 0; i < playersToSpawn; i++) {
        // Вычисляем угол для текущего игрока
        // 360 / 9 = 40 градусов на каждого
        let angle = startAngle + (i + 1) * (360 / 9); 
        
        // Переводим градусы в радианы для тригонометрии
        let rad = angle * (Math.PI / 180);

        // Вычисляем координаты по формуле эллипса:
        // x = центр + радиус * cos(угол)
        // y = центр + радиус * sin(угол)
        let x = centerX + radiusX * Math.cos(rad);
        let y = centerY + radiusY * Math.sin(rad);

        // Создаем элемент для игрока
        let seat = document.createElement("div");
        seat.className = "player-seat";
        seat.innerText = "P" + (i + 1);
        
        // Применяем координаты
        seat.style.left = x + "%";
        seat.style.top = y + "%";

        // Добавляем на стол
        table.appendChild(seat);
    }
});
