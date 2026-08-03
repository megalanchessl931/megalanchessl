"use strict";
// Carrinho de compras (balcão + pedido público).
// Evitar inserir HTML originado do usuário via innerHTML sem escapar.

(function () {
    // -----------------------------------------------------------------
    // Utilitários
    // -----------------------------------------------------------------

    function pegarCsrfToken() {
        var campo = document.querySelector('#form-finalizar input[name="csrf_token"]');
        return campo ? campo.value : "";
    }

    function formatarMoeda(valor) {
        var numero = Number(valor) || 0;
        return "R$ " + numero.toFixed(2).replace(".", ",");
    }

    function escaparHtml(texto) {
        var div = document.createElement("div");
        div.textContent = texto == null ? "" : String(texto);
        return div.innerHTML;
    }

    function apiFetch(url, opcoes) {
        opcoes = opcoes || {};
        var headers = opcoes.headers || {};
        headers["X-CSRFToken"] = pegarCsrfToken();
        if (opcoes.body) {
            headers["Content-Type"] = "application/json";
        }
        opcoes.headers = headers;
        return fetch(url, opcoes).then(function (resp) {
            return resp.json().then(function (dados) {
                if (!resp.ok) {
                    throw new Error(dados.erro || "Erro na requisição.");
                }
                return dados;
            });
        });
    }

    // -----------------------------------------------------------------
    // Renderização do carrinho
    // -----------------------------------------------------------------

    function renderCart(cart) {
        var lista = document.getElementById("carrinho-itens");
        var vazio = document.getElementById("carrinho-vazio");
        var totalEl = document.getElementById("carrinho-total");

        lista.innerHTML = "";

        if (!cart.items || cart.items.length === 0) {
            vazio.hidden = false;
        } else {
            vazio.hidden = true;
            cart.items.forEach(function (item) {
                var li = document.createElement("li");
                li.className = "carrinho-item";
                li.dataset.productId = item.product_id;
                li.innerHTML =
                    '<span class="carrinho-item-nome">' + escaparHtml(item.product_name) + "</span>" +
                    '<input type="number" min="1" step="1" class="carrinho-item-qtd" value="' +
                        Number(item.quantity) + '" data-product-id="' + item.product_id + '">' +
                    '<span class="carrinho-item-subtotal">' + formatarMoeda(item.subtotal) + "</span>" +
                    '<button type="button" class="btn-remover" data-product-id="' +
                        item.product_id + '">Remover</button>';
                lista.appendChild(li);
            });
        }

        totalEl.textContent = formatarMoeda(cart.total);
    }

    // -----------------------------------------------------------------
    // Ações do carrinho
    // -----------------------------------------------------------------

    function adicionarAoCarrinho(productId, quantidade) {
        apiFetch("/api/cart/add", {
            method: "POST",
            body: JSON.stringify({ product_id: productId, quantity: quantidade }),
        })
            .then(function (dados) {
                renderCart(dados.cart);
            })
            .catch(function (erro) {
                alert(erro.message);
            });
    }

    function removerDoCarrinho(productId) {
        apiFetch("/api/cart/remove", {
            method: "POST",
            body: JSON.stringify({ product_id: productId }),
        })
            .then(function (dados) {
                renderCart(dados.cart);
            })
            .catch(function (erro) {
                alert(erro.message);
            });
    }

    function atualizarQuantidade(productId, quantidade) {
        apiFetch("/api/cart/update", {
            method: "POST",
            body: JSON.stringify({ product_id: productId, quantity: quantidade }),
        })
            .then(function (dados) {
                renderCart(dados.cart);
            })
            .catch(function (erro) {
                alert(erro.message);
            });
    }

    function limparCarrinho() {
        if (!confirm("Limpar todos os itens do carrinho?")) {
            return;
        }
        apiFetch("/api/cart/clear", { method: "POST" })
            .then(function (dados) {
                renderCart(dados.cart);
            })
            .catch(function (erro) {
                alert(erro.message);
            });
    }

    // -----------------------------------------------------------------
    // Busca de cliente por telefone (autocompletar)
    // -----------------------------------------------------------------

    var timerBusca = null;

    function buscarCliente(telefone) {
        var lista = document.getElementById("resultados-cliente");
        var digitos = telefone.replace(/\D/g, "");

        if (digitos.length < 3) {
            lista.hidden = true;
            lista.innerHTML = "";
            return;
        }

        apiFetch("/api/client/search?phone=" + encodeURIComponent(digitos), { method: "GET" })
            .then(function (dados) {
                renderResultadosCliente(dados.clientes || []);
            })
            .catch(function () {
                lista.hidden = true;
                lista.innerHTML = "";
            });
    }

    function renderResultadosCliente(clientes) {
        var lista = document.getElementById("resultados-cliente");
        lista.innerHTML = "";

        if (clientes.length === 0) {
            lista.hidden = true;
            return;
        }

        clientes.forEach(function (cliente) {
            var li = document.createElement("li");
            li.className = "resultado-cliente-item";
            li.textContent = cliente.name + " — " + cliente.phone;
            li.addEventListener("click", function () {
                document.getElementById("cliente-nome").value = cliente.name || "";
                document.getElementById("cliente-telefone").value = cliente.phone || "";
                document.getElementById("cliente-endereco").value = cliente.address || "";
                document.getElementById("cliente-bairro").value = cliente.neighborhood || "";
                lista.hidden = true;
                lista.innerHTML = "";
            });
            lista.appendChild(li);
        });

        lista.hidden = false;
    }

    // -----------------------------------------------------------------
    // Inicialização
    // -----------------------------------------------------------------

    document.addEventListener("DOMContentLoaded", function () {
        // Carrinho vindo do servidor (se a página for de pedido).
        if (window.CARRINHO_INICIAL) {
            renderCart(window.CARRINHO_INICIAL);
        }

        // Botões "Adicionar" do cardápio.
        document.querySelectorAll(".btn-adicionar").forEach(function (botao) {
            botao.addEventListener("click", function () {
                var productId = botao.dataset.productId;
                var inputQtd = document.getElementById(botao.dataset.qtdInput);
                var quantidade = parseInt(inputQtd.value, 10) || 1;
                adicionarAoCarrinho(productId, quantidade);
            });
        });

        // Lista do carrinho: remover e alterar quantidade (delegação de evento).
        var listaCarrinho = document.getElementById("carrinho-itens");
        if (listaCarrinho) {
            listaCarrinho.addEventListener("click", function (evento) {
                if (evento.target.classList.contains("btn-remover")) {
                    removerDoCarrinho(evento.target.dataset.productId);
                }
            });
            listaCarrinho.addEventListener("change", function (evento) {
                if (evento.target.classList.contains("carrinho-item-qtd")) {
                    var novaQtd = parseInt(evento.target.value, 10) || 1;
                    atualizarQuantidade(evento.target.dataset.productId, novaQtd);
                }
            });
        }

        // Limpar carrinho.
        var botaoLimpar = document.getElementById("btn-limpar-carrinho");
        if (botaoLimpar) {
            botaoLimpar.addEventListener("click", limparCarrinho);
        }

        // Busca de cliente por telefone (com debounce).
        var inputBusca = document.getElementById("busca-telefone");
        if (inputBusca) {
            inputBusca.addEventListener("input", function () {
                clearTimeout(timerBusca);
                var valor = inputBusca.value;
                timerBusca = setTimeout(function () {
                    buscarCliente(valor);
                }, 400);
            });
        }

        // Fecha a lista de resultados se clicar fora dela.
        document.addEventListener("click", function (evento) {
            var lista = document.getElementById("resultados-cliente");
            var busca = document.getElementById("busca-telefone");
            if (lista && !lista.hidden && evento.target !== busca && !lista.contains(evento.target)) {
                lista.hidden = true;
            }
        });
    });
})();
