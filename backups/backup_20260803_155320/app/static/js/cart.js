/*
=========================================================
MEGALANCHES
Carrinho de Compras
Parte 1/3
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

    moeda(valor) {

        return Number(valor).toLocaleString(
            "pt-BR",
            {
                style: "currency",
                currency: "BRL"
            }
        );

    },

    async request(url, method = "GET", dados = null) {

        const options = {
            method: method,
            headers: {
                "X-CSRFToken": this.csrfToken()
            }
        };

        if (dados !== null) {

            options.headers["Content-Type"] =
                "application/json";

            options.body =
                JSON.stringify(dados);

        }

        const response = await fetch(url, options);

        const json = await response.json();

        if (!response.ok) {

            throw new Error(
                json.erro || "Erro inesperado."
            );

        }

        return json;

    },

    async carregarCarrinho() {

        try {

            const json =
                await this.request("/api/cart/get");

            this.cart = json.cart;

            this.renderizar();

        }

        catch (erro) {

            console.error(erro);

        }

    },

    async adicionar(produto) {

        try {

            const json =
                await this.request(

                    "/api/cart/add",

                    "POST",

                    {
                        product_id: produto,
                        quantity: 1
                    }

                );

            this.cart = json.cart;

            this.renderizar();

        }

        catch (erro) {

            alert(erro.message);

        }

    },

    async remover(produto) {

        try {

            const json =
                await this.request(

                    "/api/cart/remove",

                    "POST",

                    {
                        product_id: produto
                    }

                );

            this.cart = json.cart;

            this.renderizar();

        }

        catch (erro) {

            alert(erro.message);

        }

    },

    async alterar(produto, quantidade) {

        if (quantidade <= 0) {

            return this.remover(produto);

        }

        try {

            const json =
                await this.request(

                    "/api/cart/update",

                    "POST",

                    {
                        product_id: produto,
                        quantity: quantidade
                    }

                );

            this.cart = json.cart;

            this.renderizar();

        }

        catch (erro) {

            alert(erro.message);

        }

    },

    async limpar() {

        try {

            const json =
                await this.request(

                    "/api/cart/clear",

                    "POST"

                );

            this.cart = json.cart;

            this.renderizar();

        }

        catch (erro) {

            alert(erro.message);

        }

    },

    renderizar() {

        if (!this.cart)
            return;

        const lista =
            document.getElementById(
                "cart-items"
            );

        const total =
            document.getElementById(
                "cart-total"
            );

        if (!lista || !total)
            return;

        lista.innerHTML = "";

        if (this.cart.items.length === 0) {

            lista.innerHTML =
                "<p>Carrinho vazio.</p>";

            total.textContent =
                this.moeda(0);

            return;

        }

        this.cart.items.forEach(item => {

            const linha =
                document.createElement("div");

            linha.className =
                "cart-item";

            linha.dataset.id =
                item.product_id;

            linha.innerHTML = `

                <strong>${item.product_name}</strong>

                <br>

                Unitário:
                ${this.moeda(item.unit_price)}

                <br>

                Subtotal:
                ${this.moeda(item.subtotal)}

                <br><br>

                <button
                    class="menos"
                    data-id="${item.product_id}">

                    -

                </button>

                <span class="qtd">

                    ${item.quantity}

                </span>

                <button
                    class="mais"
                    data-id="${item.product_id}">

                    +

                </button>

                <button
                    class="remover"
                    data-id="${item.product_id}">

                    Remover

                </button>

                <hr>

            `;

            lista.appendChild(linha);

        });

        total.textContent =
            this.moeda(this.cart.total);

        this.bindEventosCarrinho();

    },
    
    bindEventosCarrinho() {

        document
            .querySelectorAll(".mais")
            .forEach(botao => {

                botao.addEventListener(
                    "click",
                    () => {

                        const id =
                            Number(botao.dataset.id);

                        const item =
                            this.cart.items.find(
                                i => i.product_id === id
                            );

                        if (!item)
                            return;

                        this.alterar(
                            id,
                            item.quantity + 1
                        );

                    }
                );

            });

        document
            .querySelectorAll(".menos")
            .forEach(botao => {

                botao.addEventListener(
                    "click",
                    () => {

                        const id =
                            Number(botao.dataset.id);

                        const item =
                            this.cart.items.find(
                                i => i.product_id === id
                            );

                        if (!item)
                            return;

                        this.alterar(
                            id,
                            item.quantity - 1
                        );

                    }
                );

            });

        document
            .querySelectorAll(".remover")
            .forEach(botao => {

                botao.addEventListener(
                    "click",
                    () => {

                        this.remover(
                            Number(botao.dataset.id)
                        );

                    }
                );

            });

    },

    preencherFormulario(cliente) {

        const nome =
            document.getElementById(
                "cliente_nome"
            );

        const telefone =
            document.getElementById(
                "cliente_telefone"
            );

        const endereco =
            document.getElementById(
                "cliente_endereco"
            );

        const bairro =
            document.getElementById(
                "cliente_bairro"
            );

        if (nome)
            nome.value = cliente.name || "";

        if (telefone)
            telefone.value = cliente.phone || "";

        if (endereco)
            endereco.value = cliente.address || "";

        if (bairro)
            bairro.value = cliente.neighborhood || "";

    },

    async buscarCliente() {

        const telefone =
            document.getElementById(
                "cliente_telefone"
            );

        if (!telefone)
            return;

        const numero =
            telefone.value.trim();

        if (numero.length < 3)
            return;

        try {

            const json =
                await this.request(

                    "/api/client/search?phone=" +
                    encodeURIComponent(numero)

                );

            if (
                !json.clientes ||
                json.clientes.length === 0
            ) {

                return;

            }

            this.preencherFormulario(
                json.clientes[0]
            );

        }

        catch (erro) {

            console.error(erro);

        }

    },

    async salvarCliente() {

        const nome =
            document.getElementById(
                "cliente_nome"
            ).value;

        const telefone =
            document.getElementById(
                "cliente_telefone"
            ).value;

        const endereco =
            document.getElementById(
                "cliente_endereco"
            ).value;

        const bairro =
            document.getElementById(
                "cliente_bairro"
            ).value;

        try {

            await this.request(

                "/api/client/create",

                "POST",

                {

                    name: nome,

                    phone: telefone,

                    address: endereco,

                    neighborhood: bairro

                }

            );

        }

        catch (erro) {

            alert(erro.message);

        }

    },

};

/*
=========================================================
Inicialização
=========================================================
*/

document.addEventListener("DOMContentLoaded", () => {

    Cart.carregarCarrinho();

    /*
    ------------------------------------------
    Botões Adicionar do Cardápio
    ------------------------------------------
    */

    document
        .querySelectorAll(".btn-add")
        .forEach(botao => {

            botao.addEventListener(
                "click",
                () => {

                    Cart.adicionar(
                        Number(botao.dataset.product)
                    );

                }
            );

        });

    /*
    ------------------------------------------
    Busca automática por telefone
    ------------------------------------------
    */

    const telefone =
        document.getElementById(
            "cliente_telefone"
        );

    if (telefone) {

        telefone.addEventListener(
            "blur",
            () => {

                Cart.buscarCliente();

            }
        );

    }

    /*
    ------------------------------------------
    Salva cliente antes do submit
    ------------------------------------------
    */

    const formulario =
        document.querySelector("form");

    if (formulario) {

        formulario.addEventListener(

            "submit",

            async function () {

                await Cart.salvarCliente();

            }

        );

    }

});

