// Функциональность для кнопок
document.addEventListener('DOMContentLoaded', function () {
    // Only keep essential functionality
    // Remove any complex button handlers that might interfere with navigation
    
    // Анимация для логотипа при загрузке страницы
    const logo = document.querySelector('.logo h1');
    if (logo) {
        logo.style.opacity = '0';
        logo.style.transform = 'translateY(-20px)';

        setTimeout(() => {
            logo.style.transition = 'all 0.8s ease';
            logo.style.opacity = '1';
            logo.style.transform = 'translateY(0)';
        }, 500);
    }

    // Темный режим переключатель (демонстрация)
    const darkModeToggle = document.createElement('div');
    darkModeToggle.innerHTML = '🌙';
    darkModeToggle.style.position = 'fixed';
    darkModeToggle.style.bottom = '20px';
    darkModeToggle.style.right = '20px';
    darkModeToggle.style.fontSize = '24px';
    darkModeToggle.style.cursor = 'pointer';
    darkModeToggle.style.zIndex = '1000';
    darkModeToggle.style.color = '#00ff41';
    darkModeToggle.style.textShadow = '0 0 10px rgba(0, 255, 65, 0.5)';
    document.body.appendChild(darkModeToggle);

    let darkMode = true;
    darkModeToggle.addEventListener('click', function () {
        darkMode = !darkMode;
        if (darkMode) {
            document.body.style.backgroundColor = '#0a0a0a';
            this.innerHTML = '🌙';
        } else {
            document.body.style.backgroundColor = '#1a1a1a';
            this.innerHTML = '☀️';
        }
    });

    // Горячая клавиша: Ctrl + 1 — переход на сайт питонпобеда.рф
    document.addEventListener('keydown', function (event) {
        const isDigitOne = event.key === '1' || event.code === 'Digit1';
        if (event.ctrlKey && isDigitOne) {
            event.preventDefault();
            const newWindow = window.open('https://питонпобеда.рф', '_blank');
            if (newWindow) {
                newWindow.opener = null;
            }
        }
    });
    
    // Add active class to the current page link in header
    // Get current page URL
    const currentPage = window.location.pathname;
    
    // Remove active class from all links
    const allLinks = document.querySelectorAll('.nav a');
    allLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to the current page link
    if (currentPage === '/') {
        document.getElementById('home-link').classList.add('active');
    } else if (currentPage.includes('/profile/')) {
        // Profile link would be highlighted if we had a specific link for it in nav
    }
});

// Функция для создания частиц в фоне (демонстрация эффекта)
function createParticles() {
    const particlesContainer = document.createElement('div');
    particlesContainer.style.position = 'fixed';
    particlesContainer.style.top = '0';
    particlesContainer.style.left = '0';
    particlesContainer.style.width = '100%';
    particlesContainer.style.height = '100%';
    particlesContainer.style.pointerEvents = 'none';
    particlesContainer.style.zIndex = '-1';
    document.body.appendChild(particlesContainer);

    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'absolute';
        particle.style.width = Math.random() * 3 + 1 + 'px';
        particle.style.height = particle.style.width;
        particle.style.backgroundColor = '#00ff41';
        particle.style.borderRadius = '50%';
        particle.style.boxShadow = '0 0 10px #00ff41';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.opacity = Math.random() * 0.5 + 0.1;
        particle.style.animation = `float ${Math.random() * 10 + 5}s infinite ease-in-out`;
        particlesContainer.appendChild(particle);
    }

    // Добавляем CSS для анимации
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0% {
                transform: translate(0, 0);
            }
            50% {
                transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px);
            }
            100% {
                transform: translate(0, 0);
            }
        }
    `;
    document.head.appendChild(style);
}

// Запускаем создание частиц после загрузки страницы
window.addEventListener('load', createParticles);

// Функциональность для модального окна входа
document.addEventListener('DOMContentLoaded', function () {
    // Получаем элементы модального окна
    const loginModal = document.getElementById('loginModal');
    const certificateModal = document.getElementById('certificateModal');
    const closeButtons = document.querySelectorAll('.close');
    const loginForm = document.getElementById('loginForm');
    
    // Закрываем модальное окно при клике на крестик
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            loginModal.style.display = 'none';
            certificateModal.style.display = 'none';
        });
    });
    
    // Закрываем модальное окно при клике вне его содержимого
    window.addEventListener('click', function(event) {
        if (event.target === loginModal) {
            loginModal.style.display = 'none';
        }
        if (event.target === certificateModal) {
            certificateModal.style.display = 'none';
        }
    });
    
    // Обрабатываем отправку формы
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Получаем значения из формы
            const nickname = document.getElementById('nickname').value;
            const surname = document.getElementById('surname').value;
            const name = document.getElementById('name').value;
            
            // Генерируем сертификат
            generateCertificate(nickname, surname, name);
            
            // Закрываем форму входа и открываем сертификат
            loginModal.style.display = 'none';
            certificateModal.style.display = 'block';
        });
    }
    
    // Функция для генерации сертификата
    function generateCertificate(nickname, surname, name) {
        const certificateContent = document.getElementById('certificateContent');
        
        // Формируем содержимое сертификата
        certificateContent.innerHTML = `
            <div class="certificate-header">
                <h2>GADUKA GANG</h2>
                <p>Сообщество фанатов Python</p>
            </div>
            
            <div class="certificate-body">
                <h3>СЕРТИФИКАТ УЧАСТНИКА</h3>
                
                <div class="certificate-details">
                    <p>Настоящим подтверждается, что</p>
                    <p class="highlight">${nickname}</p>
                    <p>(${surname} ${name})</p>
                    <p>успешно присоединился к</p>
                    <p class="highlight">Gaduka Gang</p>
                </div>
                
                <div class="certificate-footer">
                    <p>Поздравляем с вступлением в наше сообщество!</p>
                    <p>Добро пожаловать в мир Python!</p>
                </div>
            </div>
        `;
        
        // Добавляем обработчик для кнопки скачивания
        const downloadBtn = document.getElementById('downloadCertificate');
        downloadBtn.onclick = function() {
            downloadCertificate(nickname, surname, name);
        };
    }
    
    // Функция для скачивания сертификата как текстового файла
    function downloadCertificate(nickname, surname, name) {
        const certificateText = `
СЕРТИФИКАТ УЧАСТНИКА GADUKA GANG

Настоящим подтверждается, что участник
Никнейм: ${nickname}
Фамилия: ${surname}
Имя: ${name}

успешно присоединился к сообществу Gaduka Gang - Сообществу фанатов Python.

Поздравляем с вступлением в наше сообщество!
Добро пожаловать в мир Python!

Дата выдачи: ${new Date().toLocaleDateString('ru-RU')}
        `;
        
        // Создаем элемент для скачивания
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(certificateText));
        element.setAttribute('download', `Сертификат_${nickname}.txt`);
        
        element.style.display = 'none';
        document.body.appendChild(element);
        
        element.click();
        
        document.body.removeChild(element);
    }
});