# Ejemplos de Integración Frontend - Paginación de Órdenes de Pago

## Ejemplo 1: React con Hooks

```javascript
import React, {useState, useEffect} from 'react';

const PaymentOrdersList = () => {
    const [orders, setOrders] = useState([]);
    const [pagination, setPagination] = useState({
        count: 0,
        next: null,
        previous: null
    });
    const [currentPage, setCurrentPage] = useState(1);
    const [perPage, setPerPage] = useState(10);
    const [filters, setFilters] = useState({});
    const [loading, setLoading] = useState(false);

    const fetchOrders = async (page = 1) => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                page,
                per_page: perPage,
                ...filters
            });

            const response = await fetch(
                `/api/v1/payment-orders/?${params}`,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            const data = await response.json();

            setOrders(data.results);
            setPagination({
                count: data.count,
                next: data.next,
                previous: data.previous
            });
            setCurrentPage(page);
        } catch (error) {
            console.error('Error fetching orders:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchOrders(currentPage);
    }, [filters, perPage]);

    const handleNextPage = () => {
        if (pagination.next) {
            fetchOrders(currentPage + 1);
        }
    };

    const handlePreviousPage = () => {
        if (pagination.previous) {
            fetchOrders(currentPage - 1);
        }
    };

    const handleFilterChange = (filterName, value) => {
        setFilters(prev => ({
            ...prev,
            [filterName]: value
        }));
        setCurrentPage(1); // Reset a primera página cuando cambian filtros
    };

    return (
        <div>
            <h1>Órdenes de Pago</h1>

            {/* Filtros */}
            <div className="filters">
                <select
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                    value={filters.status || ''}
                >
                    <option value="">Todos los estados</option>
                    <option value="PENDING">Pendiente</option>
                    <option value="PAID">Pagado</option>
                    <option value="CANCELLED">Cancelado</option>
                </select>

                <input
                    type="number"
                    placeholder="ID Estudiante"
                    onChange={(e) => handleFilterChange('student_id', e.target.value)}
                />

                <select
                    onChange={(e) => setPerPage(parseInt(e.target.value))}
                    value={perPage}
                >
                    <option value="10">10 por página</option>
                    <option value="20">20 por página</option>
                    <option value="50">50 por página</option>
                </select>
            </div>

            {/* Lista de órdenes */}
            {loading ? (
                <div>Cargando...</div>
            ) : (
                <table>
                    <thead>
                        <tr>
                            <th>Número de Orden</th>
                            <th>Estudiante</th>
                            <th>Estado</th>
                            <th>Total</th>
                            <th>Fecha</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.map(order => (
                            <tr key={order.id}>
                                <td>{order.order_number}</td>
                                <td>{order.student?.first_name} {order.student?.last_name}</td>
                                <td>{order.status}</td>
                                <td>${order.total_order}</td>
                                <td>{new Date(order.created_at).toLocaleDateString()}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

            {/* Paginación */}
            <div className="pagination">
                <button
                    onClick={handlePreviousPage}
                    disabled={!pagination.previous || loading}
                >
                    Anterior
                </button>

                <span>
                    Página {currentPage} - Total: {pagination.count} órdenes
                </span>

                <button
                    onClick={handleNextPage}
                    disabled={!pagination.next || loading}
                >
                    Siguiente
                </button>
            </div>
        </div>
    );
};

export default PaymentOrdersList;
```

---

## Ejemplo 2: Vue.js 3 con Composition API

```javascript
<template>
    <div class="payment-orders">
        <h1>Órdenes de Pago</h1>

        <!-- Filtros -->
        <div class="filters">
            <select v-model="filters.status"
            @change="resetAndFetch">
            <option value="">Todos los estados</option>
            <option value="PENDING">Pendiente</option>
            <option value="PAID">Pagado</option>
            <option value="CANCELLED">Cancelado</option>
        </select>

        <input
            v-model="filters.student_id"
            type="number"
            placeholder="ID Estudiante"
        @input="resetAndFetch"
        />

        <select v-model="perPage"
        @change="resetAndFetch">
        <option
        :value="10">10 por página
    </option>
    <option
    :value="20">20 por página
</option>
<option :value = "50" > 50
por
página < /option>
</select>
</div>

<!-- Loading -->
<div v-if="loading">Cargando...</div>

<!-- Tabla -->
<table v-else>
    <thead>
        <tr>
            <th>Número de Orden</th>
            <th>Estudiante</th>
            <th>Estado</th>
            <th>Total</th>
            <th>Fecha</th>
        </tr>
    </thead>
    <tbody>
        <tr v-for="order in orders"
        :key="order.id">
        <td>{{order.order_number}}</td>
        <td>{{order.student?.first_name}} {{order.student?.last_name}}</td>
        <td>{{order.status}}</td>
        <td>${{order.total_order}}</td>
        <td>{{formatDate(order.created_at)}}</td>
    </tr>
</tbody>
</table>

<!-- Paginación -->
<div class="pagination">
    <button
    @click="fetchOrders(currentPage - 1)"
    :disabled="!pagination.previous || loading"
    >
    Anterior
</button>

<span>
    Página {{currentPage}} - Total: {{pagination.count}} órdenes
</span>

<button 
        @click = "fetchOrders(currentPage + 1)"
:
disabled = "!pagination.next || loading"
    >
    Siguiente
    < /button>
</div>
</div>
</template>

<script setup>
    import {ref, reactive, onMounted, watch} from 'vue';

    const orders = ref([]);
    const pagination = reactive({
    count: 0,
    next: null,
    previous: null
});
    const currentPage = ref(1);
    const perPage = ref(10);
    const filters = reactive({
    status: '',
    student_id: ''
});
    const loading = ref(false);

    const fetchOrders = async (page = 1) => {
    loading.value = true;
    try {
    const cleanFilters = Object.fromEntries(
    Object.entries(filters).filter(([_, v]) => v !== '' && v !== null)
    );

    const params = new URLSearchParams({
    page,
    per_page: perPage.value,
    ...cleanFilters
});

    const response = await fetch(
    `/api/v1/payment-orders/?${params}`,
{
    headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json'
}
}
    );

    const data = await response.json();

    orders.value = data.results;
    pagination.count = data.count;
    pagination.next = data.next;
    pagination.previous = data.previous;
    currentPage.value = page;
} catch (error) {
    console.error('Error fetching orders:', error);
} finally {
    loading.value = false;
}
};

    const resetAndFetch = () => {
    currentPage.value = 1;
    fetchOrders(1);
};

    const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
};

    onMounted(() => {
    fetchOrders();
});
</script>
```

---

## Ejemplo 3: JavaScript Vanilla (sin frameworks)

```javascript
class PaymentOrdersManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentPage = 1;
        this.perPage = 10;
        this.filters = {};
        this.pagination = {};

        this.init();
    }

    init() {
        this.renderFilters();
        this.fetchOrders();
    }

    renderFilters() {
        const filtersHTML = `
      <div class="filters">
        <select id="statusFilter">
          <option value="">Todos los estados</option>
          <option value="PENDING">Pendiente</option>
          <option value="PAID">Pagado</option>
          <option value="CANCELLED">Cancelado</option>
        </select>

        <input id="studentFilter" type="number" placeholder="ID Estudiante" />

        <select id="perPageSelect">
          <option value="10">10 por página</option>
          <option value="20">20 por página</option>
          <option value="50">50 por página</option>
        </select>

        <button id="applyFilters">Aplicar Filtros</button>
      </div>
      <div id="ordersContent"></div>
    `;

        this.container.innerHTML = filtersHTML;

        // Event listeners
        document.getElementById('applyFilters').addEventListener('click', () => {
            this.filters.status = document.getElementById('statusFilter').value;
            this.filters.student_id = document.getElementById('studentFilter').value;
            this.perPage = parseInt(document.getElementById('perPageSelect').value);
            this.currentPage = 1;
            this.fetchOrders();
        });
    }

    async fetchOrders(page = 1) {
        try {
            const params = new URLSearchParams({
                page,
                per_page: this.perPage,
                ...this.filters
            });

            // Limpiar parámetros vacíos
            for (const [key, value] of [...params]) {
                if (!value) params.delete(key);
            }

            const response = await fetch(
                `/api/v1/payment-orders/?${params}`,
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            const data = await response.json();
            this.currentPage = page;
            this.pagination = {
                count: data.count,
                next: data.next,
                previous: data.previous
            };

            this.renderOrders(data.results);
            this.renderPagination();
        } catch (error) {
            console.error('Error:', error);
            this.renderError('Error al cargar las órdenes');
        }
    }

    renderOrders(orders) {
        const contentDiv = document.getElementById('ordersContent');

        if (orders.length === 0) {
            contentDiv.innerHTML = '<p>No se encontraron órdenes</p>';
            return;
        }

        const tableHTML = `
      <table>
        <thead>
          <tr>
            <th>Número de Orden</th>
            <th>Estudiante</th>
            <th>Estado</th>
            <th>Total</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          ${orders.map(order => `
            <tr>
              <td>${order.order_number}</td>
              <td>${order.student?.first_name || ''} ${order.student?.last_name || ''}</td>
              <td>${order.status}</td>
              <td>$${order.total_order}</td>
              <td>${new Date(order.created_at).toLocaleDateString()}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

        contentDiv.innerHTML = tableHTML;
    }

    renderPagination() {
        const paginationHTML = `
      <div class="pagination">
        <button id="prevPage" ${!this.pagination.previous ? 'disabled' : ''}>
          Anterior
        </button>
        
        <span>
          Página ${this.currentPage} - Total: ${this.pagination.count} órdenes
        </span>
        
        <button id="nextPage" ${!this.pagination.next ? 'disabled' : ''}>
          Siguiente
        </button>
      </div>
    `;

        document.getElementById('ordersContent').insertAdjacentHTML('beforeend', paginationHTML);

        // Event listeners para paginación
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.fetchOrders(this.currentPage - 1));
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.fetchOrders(this.currentPage + 1));
        }
    }

    renderError(message) {
        document.getElementById('ordersContent').innerHTML = `
      <div class="error">${message}</div>
    `;
    }
}

// Uso
document.addEventListener('DOMContentLoaded', () => {
    new PaymentOrdersManager('paymentOrdersContainer');
});
```

---

## Ejemplo 4: jQuery

```javascript
$(document).ready(function () {
    const PaymentOrders = {
        currentPage: 1,
        perPage: 10,
        filters: {},

        init: function () {
            this.bindEvents();
            this.fetchOrders();
        },

        bindEvents: function () {
            $('#applyFilters').on('click', () => {
                this.filters = {
                    status: $('#statusFilter').val(),
                    student_id: $('#studentFilter').val()
                };
                this.perPage = parseInt($('#perPageSelect').val());
                this.currentPage = 1;
                this.fetchOrders();
            });

            $(document).on('click', '#prevPage', () => {
                this.fetchOrders(this.currentPage - 1);
            });

            $(document).on('click', '#nextPage', () => {
                this.fetchOrders(this.currentPage + 1);
            });
        },

        fetchOrders: function (page = 1) {
            const params = $.param({
                page: page,
                per_page: this.perPage,
                ...this.filters
            });

            $.ajax({
                url: `/api/v1/payment-orders/?${params}`,
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                success: (data) => {
                    this.currentPage = page;
                    this.pagination = {
                        count: data.count,
                        next: data.next,
                        previous: data.previous
                    };
                    this.renderOrders(data.results);
                    this.renderPagination();
                },
                error: (error) => {
                    console.error('Error:', error);
                    $('#ordersContent').html('<div class="error">Error al cargar órdenes</div>');
                }
            });
        },

        renderOrders: function (orders) {
            let html = '<table><thead><tr>';
            html += '<th>Número</th><th>Estudiante</th><th>Estado</th><th>Total</th><th>Fecha</th>';
            html += '</tr></thead><tbody>';

            orders.forEach(order => {
                html += `<tr>
          <td>${order.order_number}</td>
          <td>${order.student?.first_name || ''} ${order.student?.last_name || ''}</td>
          <td>${order.status}</td>
          <td>$${order.total_order}</td>
          <td>${new Date(order.created_at).toLocaleDateString()}</td>
        </tr>`;
            });

            html += '</tbody></table>';
            $('#ordersContent').html(html);
        },

        renderPagination: function () {
            const html = `
        <div class="pagination">
          <button id="prevPage" ${!this.pagination.previous ? 'disabled' : ''}>
            Anterior
          </button>
          <span>Página ${this.currentPage} - Total: ${this.pagination.count}</span>
          <button id="nextPage" ${!this.pagination.next ? 'disabled' : ''}>
            Siguiente
          </button>
        </div>
      `;
            $('#ordersContent').append(html);
        }
    };

    PaymentOrders.init();
});
```

---

## Ejemplo 5: Axios (puede usarse con cualquier framework)

```javascript
import axios from 'axios';

class PaymentOrdersAPI {
    constructor(baseURL = '/api/v1') {
        this.client = axios.create({
            baseURL,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Interceptor para agregar token
        this.client.interceptors.request.use(config => {
            const token = localStorage.getItem('token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });
    }

    async getPaymentOrders(page = 1, perPage = 10, filters = {}) {
        try {
            const params = {
                page,
                per_page: perPage,
                ...filters
            };

            const response = await this.client.get('/payment-orders/', {params});
            return response.data;
        } catch (error) {
            console.error('Error fetching payment orders:', error);
            throw error;
        }
    }

    async getAllPages(filters = {}, perPage = 100) {
        let allOrders = [];
        let page = 1;
        let hasMore = true;

        while (hasMore) {
            const data = await this.getPaymentOrders(page, perPage, filters);
            allOrders = [...allOrders, ...data.results];
            hasMore = data.next !== null;
            page++;
        }

        return allOrders;
    }
}

// Uso
const api = new PaymentOrdersAPI();

// Obtener una página
const page1 = await api.getPaymentOrders(1, 20, {status: 'PAID'});
console.log(page1);

// Obtener todas las páginas
const allOrders = await api.getAllPages({advisor_id: 5});
console.log(`Total órdenes: ${allOrders.length}`);
```

---

## CSS Básico para Paginación

```css
.filters {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    padding: 15px;
    background: #f5f5f5;
    border-radius: 8px;
}

.filters select,
.filters input {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

table th,
table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

table th {
    background: #f8f9fa;
    font-weight: 600;
}

table tr:hover {
    background: #f5f5f5;
}

.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    margin-top: 20px;
}

.pagination button {
    padding: 8px 16px;
    border: 1px solid #007bff;
    background: #007bff;
    color: white;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.3s;
}

.pagination button:hover:not(:disabled) {
    background: #0056b3;
}

.pagination button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: #6c757d;
    border-color: #6c757d;
}

.pagination span {
    font-weight: 500;
    color: #333;
}

.error {
    padding: 15px;
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    margin: 20px 0;
}
```

