import os

def imprimir_cupom(order_data, device_path=None):
    """
    Impressão ESC/POS opcional.
    Se PRINT_DEVICE não estiver definido, não imprime.
    """
    device_path = device_path or os.getenv("PRINT_DEVICE", "")
    if not device_path:
        return False

    try:
        from escpos.printer import File
        printer = File(device_path)
        printer.text(f"PEDIDO #{order_data.get('id', '')}\n")
        printer.text(f"Total: R$ {order_data.get('total', '0.00')}\n")
        printer.cut()
        return True
    except Exception:
        # Não expõe detalhes do dispositivo ao usuário.
        return False
