/**
 * API Client для работы с Gaduka Gang API
 * 
 * Использование:
 *   api.get('/api/users/').then(data => console.log(data));
 *   api.post('/api/users/', {username: 'test'}).then(data => console.log(data));
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.token = this.getToken();
    }

    /**
     * Получить токен из localStorage
     */
    getToken() {
        return localStorage.getItem('api_token') || null;
    }

    /**
     * Сохранить токен в localStorage
     */
    setToken(token) {
        if (token) {
            localStorage.setItem('api_token', token);
            this.token = token;
        } else {
            localStorage.removeItem('api_token');
            this.token = null;
        }
    }

    /**
     * Получить заголовки для запроса
     */
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (includeAuth && this.token) {
            headers['Authorization'] = `Token ${this.token}`;
            // Или для JWT:
            // headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    /**
     * Обработка ответа от сервера
     */
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (!response.ok) {
                // Обработка ошибок
                const error = {
                    status: response.status,
                    statusText: response.statusText,
                    message: data.error || data.message || 'Произошла ошибка',
                    data: data
                };
                throw error;
            }
            
            return data;
        } else {
            // Если ответ не JSON
            const text = await response.text();
            if (!response.ok) {
                throw {
                    status: response.status,
                    statusText: response.statusText,
                    message: text || 'Произошла ошибка'
                };
            }
            return text;
        }
    }

    /**
     * GET запрос
     */
    async get(url, params = {}) {
        // Добавляем query параметры
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;

        const response = await fetch(this.baseURL + fullUrl, {
            method: 'GET',
            headers: this.getHeaders(),
        });

        return this.handleResponse(response);
    }

    /**
     * POST запрос
     */
    async post(url, data = {}) {
        const response = await fetch(this.baseURL + url, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(data),
        });

        return this.handleResponse(response);
    }

    /**
     * PUT запрос (полное обновление)
     */
    async put(url, data = {}) {
        const response = await fetch(this.baseURL + url, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(data),
        });

        return this.handleResponse(response);
    }

    /**
     * PATCH запрос (частичное обновление)
     */
    async patch(url, data = {}) {
        const response = await fetch(this.baseURL + url, {
            method: 'PATCH',
            headers: this.getHeaders(),
            body: JSON.stringify(data),
        });

        return this.handleResponse(response);
    }

    /**
     * DELETE запрос
     */
    async delete(url) {
        const response = await fetch(this.baseURL + url, {
            method: 'DELETE',
            headers: this.getHeaders(),
        });

        return this.handleResponse(response);
    }

    /**
     * Аутентификация
     */
    async login(username, password) {
        try {
            const response = await this.post('/api/auth/login/', {
                username,
                password
            });
            
            if (response.token) {
                this.setToken(response.token);
            }
            
            return response;
        } catch (error) {
            throw error;
        }
    }

    /**
     * Выход
     */
    async logout() {
        try {
            await this.post('/api/auth/logout/');
            this.setToken(null);
            return true;
        } catch (error) {
            // Даже если запрос не удался, очищаем токен локально
            this.setToken(null);
            throw error;
        }
    }

    /**
     * Получить текущего пользователя
     */
    async getCurrentUser() {
        return this.get('/api/auth/me/');
    }

    /**
     * Проверить, авторизован ли пользователь
     */
    isAuthenticated() {
        return this.token !== null;
    }
}

// Создаем глобальный экземпляр API клиента
const api = new APIClient();

// Экспортируем для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { api, APIClient };
}

