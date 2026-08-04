/*
=========================================================
MEGALANCHES
Carrinho de compras
=========================================================
*/

const Cart = {

    cart: null,

    csrfToken() {
        const token = document.querySelector(
            'input[name="csrf_token"]'
        );

        return token ? token.value : "";
    },

    async request(url, method = "GET", data = null) {

        const options = {
            method: method,
            headers: {
                "X-CSRFToken": this.csrfToken()
            }
        };

        if (data !== null) {

            options.headers["Content-Type"] = "application/json";

            options.body = JSON.stringify(data);

        }

        const response = await fetch(url, options);

        return await response.json();

    },

    async carregarCarrinho() {

        const json = await this.request("/api/cart/get");

        if (!json.ok)
            return;

        this.cart = json.cart;

        this.renderizar();

    },

    async adicionar(productId) {

        const json = await this.request(
            "/api/cart/add",
            "POST",
            {
                product_id: productId,
                quantity: 1
            }
        );

        if (!json.ok) {

            alert(json.erro);

            return;

        }

        this.cart = json.cart;

        this.renderizar();

    },

    async remover(productId) {

        const json = await this.request(
            "/api/cart/remove",
            "POST",
            {
                product_id: productId
            }
        );

        if (!json.ok) {

            alert(json.erro);

            return;

        }

        this.cart = json.cart;

        this.renderizar();

    },

    async alterarQuantidade(productId, quantidade) {

        const json = await this.request(
            "/api/cart/update",
            "POST",
            {
                product_id: productId,
                quantity: quantidade
            }
        );

        if (!json.ok) {

            alert(json.erro);

            return;

        }

        this.cart = json.cart;

        this.renderizar();

    },

    renderizar() {

        const lista = document.getElementById("cart-items");

        const total = document.getElementById("cart-total");

        if (!lista)
            return;

        lista.innerHTML = "";

        if (this.cart.items.length === 0) {

            lista.innerHTML =
                "<p>Carrinho vazio.</p>";

            total.innerHTML = "R$ 0,00";

            return;

        }

        this.cart.items.forEach(item => {

            const div = document.createElement("div");

            div.className = "cart-item";

            div.innerHTML = `

                <strong>${item.product_name}</strong>

                <br>

                R$ ${parseFloat(item.unit_price).toFixed(2)}

                <br>

                <button
                    onclick="Cart.alterarQuantidade(${item.product_id}, ${item.quantity-1})">

                    -

                </button>

                <strong>${item.quantity}</strong>

                <button
                    onclick="Cart.alterarQuantidade(${item.product_id}, ${item.quantity+1})">

                    +

                </button>

                <button
                    onclick="Cart.remover(${item.product_id})">

                    Remover

                </button>

                <hr>

            `;

            lista.appendChild(div);

        });

        total.innerHTML =
            "R$ " + parseFloat(this.cart.total).toFixed(2);

    },

    async procurarCliente() {

        const telefone =
            document.getElementById(
                "cliente_telefone"
            ).value;

        if (telefone.length < 3)
            return;

        const json = await this.request(
            "/api/client/search?phone=" +
            encodeURIComponent(telefone)
        );

        if (!json.ok)
            return;

        if (json.clientes.length === 0)
            return;

        const cliente = json.clientes[0];

        document.getElementById(
            "cliente_nome"
        ).value = cliente.name;

        document.getElementById(
            "cliente_endereco"
        ).value = cliente.address || "";

        document.getElementById(
            "cliente_bairro"
        ).value = cliente.neighborhood || "";

    }

};


/*
====================================
Inicialização
====================================
*/

document.addEventListener("DOMContentLoaded", function () {

    Cart.carregarCarrinho();

    document.querySelectorAll(".btn-add")
        .forEach(botao => {

            botao.addEventListener(
                "click",
                function () {

                    Cart.adicionar(
                        this.dataset.product
                    );

                }

            );

        });

    const telefone =
        document.getElementById(
            "cliente_telefone"
        );

    if (telefone) {

        telefone.addEventListener(
            "blur",
            function () {

                Cart.procurarCliente();

            }

        );

    }

});
